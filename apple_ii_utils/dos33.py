#!/usr/bin/env python3

import struct
import subprocess
import sys

CATALOG_TRACK = 17
SECTOR_SIZE = 256

from apple_iic_xfer.apple_ii_utils.applesoft import list_applesoft


def list_binary(data):
    address, length = struct.unpack("<HH", data[:4])


def sector_from_disk(disk, t, s):
    offset = 256 * (s + 16 * t)
    data = disk[offset : offset + 256]
    return data


TYPE_LOOKUP = {
    0: "T",
    1: "I",
    2: "A",
    4: "B",
    8: "R",
    0x10: "Z",
    0x20: "Y",
    0x40: "X",
}


def catalog_entries(disk):
    t, s = CATALOG_TRACK, 0
    while s > 0 or t == CATALOG_TRACK:
        cat_sector = sector_from_disk(disk, t, s)
        if (t, s) != (17, 0):
            for offset in range(11, 256, 35):
                ts_list_track, ts_list_sector, type_lock, name, sector_count = struct.unpack(
                    "<BBB30sH", cat_sector[offset : offset + 35]
                )
                name = "".join(chr(x & 127) for x in name).rstrip()
                is_locked = not not (type_lock & 0x80)
                file_type = TYPE_LOOKUP.get(type_lock & 0x7F, "?")
                catalog_entry = {
                    "ts_list": (ts_list_track, ts_list_sector),
                    "name": name,
                    "file_type": file_type,
                    "is_locked": is_locked,
                    "sector_count": sector_count,
                }
                if ts_list_track > 0:
                    yield catalog_entry
        t, s = struct.unpack("!BB", cat_sector[1:3])


def catalog_entry_as_text(entry):
    lock_flag = "*" if entry["is_locked"] else " "
    return "%s%s %03d %s" % (lock_flag, entry["file_type"], entry["sector_count"], entry["name"])


def open_file(disk, entry):
    t, s = entry["ts_list"]
    ts_list = sector_from_disk(disk, t, s)
    data_blocks = []
    offset = 12
    while offset < SECTOR_SIZE:
        t, s = struct.unpack("!BB", ts_list[offset : offset + 2])
        if t == 0:
            break
        data_blocks.append(sector_from_disk(disk, t, s))
        offset += 2
    return b"".join(data_blocks)


def contents_of_entry(disk, entry):
    data = open_file(disk, entry)
    if entry["file_type"] == "A":
        return list_applesoft(data)
    data = bytes(_ & 0x7f for _ in data)
    t1=subprocess.run("/usr/bin/hexdump -C".split(), capture_output=True, input=data)
    return t1.stdout.decode()


def main():
    disk = open(sys.argv[1], "rb").read()

    entries = list(catalog_entries(disk))
    for entry in catalog_entries(disk):
        print(catalog_entry_as_text(entry))
    print(contents_of_entry(disk, entries[1]))


if __name__ == "__main__":
    main()
