# hack to parse raw tracks

import io

from apple_ii_utils.xferdos33 import process_track

s = open("track-dump-preprocessed-and-raw").read()

lines = s.splitlines()
b1 = lines.index("T=11")
b2 = lines.index("T=11", b1 + 1)

section_1 = "\n".join(lines[b1:b2])
section_2 = "\n".join(lines[b2:])

track_index, track_data = process_track(section_1.encode("utf8"))

raw_track_index, raw_track_data = process_track(section_2.encode("utf8"))

print(track_index)
print(hex(len(raw_track_data)))


def parse_4x4(stream: io.BytesIO) -> bytes:
    t1 = get1(stream)
    t2 = get1(stream)
    t = (t2 & 0x55) | ((t1 & 0x55) << 1)
    return t


def get1(stream: io.BytesIO) -> int:
    b = stream.read(1)
    if len(b) == 0:
        raise IOError()
    return b[0]


SECTOR_LOOKUP = [int(_, 16) for _ in "07e6d5c4b3a2918f"]
REV_SECTOR_LOOKUP = {v: k for k, v in enumerate(SECTOR_LOOKUP)}


def build_nibble_table():
    def is_valid(s):
        # check for two consecutive 1 bits
        if all((s & (0b11 << x) != (0b11 << x)) for x in range(6)):
            return False
        # make sure two consecutive 0 bits only happens at most once
        return sum(1 if (s & (0b11 << x) == 0) else 0 for x in range(7)) < 2

    table = [None] * 256
    s = 0x96
    for idx in range(0x40):
        table[s] = idx
        while 1:
            s += 1
            if is_valid(s):
                break
    return table


NIBBLE_TABLE = build_nibble_table()


def debug():
    for a, b in enumerate(NIBBLE_TABLE):
        if b is None:
            continue
        print(f"{hex(a)} => {hex(b)}")
    print(SECTOR_LOOKUP)


def dump256(b: bytes):
    def char(v):
        c = chr(v & 0x7F)
        if c.isprintable():
            return c
        return "."

    for _ in range(0, 256, 16):
        t = " ".join(b[v : v + 1].hex() for v in range(_, _ + 16))
        ascii = ''.join(char(_) for _ in b[_ : _ + 16])
        print(t, " ", ascii)


def dump_sec(b: bytes, sector_index: int):
    dump256(b[0x100 * sector_index : 0x100 * (sector_index + 1)])


for _ in range(16):
    print(f"SECTOR={hex(_)}")
    dump_sec(track_data, _)
    print()


def nibblize(raw_track_data: bytes):
    found = []
    stream = io.BytesIO(raw_track_data)
    b = get1(stream)
    while 1:
        not_found = b != 0xD5
        b = get1(stream)
        if not_found:
            continue

        not_found = b != 0xAA
        b = get1(stream)
        if not_found:
            continue

        not_found = b != 0x96
        if not_found:
            continue

        volume = parse_4x4(stream)
        track = parse_4x4(stream)
        sector = parse_4x4(stream)
        checksum = parse_4x4(stream)

        if volume ^ track ^ sector != checksum:
            continue

        b = get1(stream)
        if b != 0xDE:
            continue
        b = get1(stream)
        if b != 0xAA:
            continue
        b = get1(stream)

        retry_count = 8
        b = get1(stream)
        while retry_count:
            retry_count -= 1
            not_found = b != 0xD5
            b = get1(stream)
            if not_found:
                continue

            not_found = b != 0xAA
            b = get1(stream)
            if not_found:
                continue

            if b == 0xAD:
                break

        if not retry_count:
            continue

        raw_sector = stream.read(343)

        b = get1(stream)
        if b != 0xDE:
            continue
        b = get1(stream)
        if b != 0xAA:
            continue

        sector_bytes = nibblize_raw_sector(raw_sector)

        lsec = SECTOR_LOOKUP[sector] + 1
        sector_bytes_ftd = track_data[0x100 * lsec : 0x100 * (lsec + 1)]

        print()
        dump256(sector_bytes)
        print()
        dump256(sector_bytes_ftd)
        print(sector_bytes == sector_bytes_ftd)

        # the_eor = bytes(a ^ b for a, b in zip(sector_bytes, sector_bytes_ftd))
        # dump256(the_eor)
        breakpoint()


def nibblize_raw_sector(raw_sector: bytes):
    two_bit_reverse_table = [0, 2, 1, 3]
    nibbles = []
    xor = 0
    for b in raw_sector:
        xor ^= NIBBLE_TABLE[b]
        nibbles.append(xor)
    original_nibbles = bytes(nibbles)
    if xor != 0:
        # IO error
        raise IOError()
    extra_bits = nibbles[:86]
    sector_data = nibbles[86 : 86 + 256]
    read_index = 0
    write_index = 0
    while write_index < 256:
        sector_data[write_index] <<= 2
        sector_data[write_index] |= two_bit_reverse_table[extra_bits[read_index] & 0b11]
        extra_bits[read_index] >>= 2
        read_index += 1
        if read_index == len(extra_bits):
            read_index = 0
        write_index += 1
    return bytes(sector_data)


nibblize(raw_track_data)
