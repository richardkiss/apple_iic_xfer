# about the Apple //c serial port:
#   http://support.apple.com/kb/TA38851?viewlocale=en_US
#   http://support.apple.com/kb/TA29788?viewlocale=en_US

import argparse
import binascii
import io
import re
import sys
import time
from functools import reduce
from typing import Tuple

import serial


def send_blind(port: serial.Serial, t_str: str):
    t = t_str.encode()
    for v in t:
        c = bytes([v])
        port.write(c)
        time.sleep(0.25)


def send(port: serial.Serial, t_str: str, wait_char: str = "]"):
    t = t_str.encode()
    wait_char = wait_char.encode() if wait_char else None

    for v in t:
        c = bytes([v])
        port.write(c)
        while 1:
            c1 = port.read(1)
            same = c1 == c
            if c1 == b"\r":
                c1 = b"\n"
            sys.stdout.write(c1.decode())
            sys.stdout.flush()
            if same:
                break
    if wait_char is None:
        return
    while 1:
        c1 = port.read(1)
        if c1 == b"\r":
            c1 = b"\n"
        sys.stdout.write(c1.decode())
        sys.stdout.flush()
        if c1 == wait_char:
            break


def wait_for(port: serial.Serial, sentinal: bytes) -> bytes:
    f = io.BytesIO()
    while 1:
        c1 = port.read(1)
        if c1 == b"\r":
            c1 = b"\n"
        f.write(c1)
        sys.stdout.write(c1.decode())
        if c1 == sentinal:
            break
    return f.getvalue()


TRACK_RE = re.compile(r"T=([0-9A-F]{2})")
SECTOR_RE = re.compile(
    r"([0-9A-F]{64})x([0-9A-F]{64})x([0-9A-F]{64})x([0-9A-F]{64})x"
    r"([0-9A-F]{64})x([0-9A-F]{64})x([0-9A-F]{64})x([0-9A-F]{64})x"
    r"\+=([0-9A-F]{2})xE=([0-9A-F]{2})"
)


def process_track(dump_bytes: bytes) -> Tuple[int, bytes]:
    dump = dump_bytes.decode()
    dump = dump.replace("\n", "x")
    track_found = TRACK_RE.findall(dump)
    track_idx = int(track_found[0], 16)
    sectors = SECTOR_RE.findall(dump)
    sector_data = []
    for _sector_idx, sector_tuple in enumerate(sectors):
        d = b"".join(binascii.unhexlify(x) for x in sector_tuple[:8])
        actual_sum = sum(d) % 256
        actual_xor = reduce(lambda a, b: a ^ b, d, 0)
        expected_sum = int(sector_tuple[8], 16)
        expected_xor = int(sector_tuple[9], 16)
        if actual_sum != expected_sum or actual_xor != expected_xor:
            msg = "bad checksum!! aborting"
            raise OSError(msg)
        sector_data.append(d)
    track_data = b"".join(sector_data)
    return track_idx, track_data


APPLE_BIN = """8000:A9 0F 85 01 A9 10 85 0A
8008:18 69 60 85 09 20 AC 80
8010:B0 08 C6 09 C6 01 10 F5
8018:30 2D A0 01 B1 07 AA BD
8020:89 C0 88 84 04 A9 60 85
8028:05 A9 1C 85 09 85 0A BD
8030:8C C0 DD 8C C0 F0 F8 BD
8038:8C C0 10 FB 91 04 C8 D0
8040:F6 E6 05 C6 09 D0 F0 A9
8048:D4 A4 00 20 9B 80 A9 60
8050:85 09 A9 00 48 20 63 80
8058:68 A8 E6 09 C8 98 C4 0A
8060:90 F2 60 A0 00 84 04 84
8068:02 84 03 A5 09 85 05 B1
8070:04 48 20 DA FD 68 48 18
8078:65 02 85 02 68 45 03 85
8080:03 C8 98 29 1F D0 03 20
8088:A7 80 98 D0 E2 A9 AB A4
8090:02 20 9B 80 A9 C5 A4 03
8098:4C 9B 80 20 ED FD A9 BD
80A0:20 ED FD 98 20 DA FD A9
80A8:8D 4C ED FD 20 E3 03 84
80B0:07 85 08 A0 03 A9 00 91
80B8:07 A5 00 C8 91 07 A5 01
80C0:C8 91 07 A9 00 A0 08 91
80C8:07 A5 09 C8 91 07 A9 01
80D0:A0 0C 91 07 20 E3 03 20
80D8:D9 03 A0 0D B1 07 60 00"""


def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Serial Port Data Logger")

    # Add arguments
    parser.add_argument(
        "-p",
        "--port",
        type=str,
        default="/dev/tty.usbserial",
        help="Serial port name (e.g., /dev/ttyUSB0, COM1)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Output file to save the data",
    )

    # Parse the arguments
    args = parser.parse_args()

    s = """On the Apple, type:
]IN#2

then
^A 15B (to set 19200 baud)
^A 1D (to set 7N1)

Note that ^A means "control-A".

Then hit return. >"""

    t = input(s)

    try:
        port = serial.Serial(
            args.port,
            19200,
            bytesize=serial.SEVENBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
        )
    except OSError:
        parser.error(f"Can't open {args.port}")

    send_blind(port, "\r\3\rPR#2\r")
    send(port, "CALL-151\r", wait_char="*")

    for t in APPLE_BIN.split("\n"):
        send(port, t + "\r", wait_char="*")

    track_data_list = []

    for track in range(35):
        send(port, "0:%02x\r" % track, wait_char="*")
        send(port, "8000G\r", wait_char=None)
        track_dump = wait_for(port, b"*")
        actual_track, track_data = process_track(track_dump)
        track_data_list.append(track_data)

    disk_data = b"".join(track_data_list)

    f = open(args.output, "wb")
    f.write(disk_data)
    f.close()


if __name__ == "__main__":
    main()
