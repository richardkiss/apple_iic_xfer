#!/usr/bin/env python

# about the Apple //c serial port:
#   http://support.apple.com/kb/TA38851?viewlocale=en_US
#   http://support.apple.com/kb/TA29788?viewlocale=en_US

import binascii
import io
import re
import sys
import time

import serial

SERIAL_PORT_DEVICE = "/dev/ttyUSB0"

APPLE_BIN = """8000:A9 0F 85 01 18 69 85 85
8008:09 20 77 80 C6 09 C6 01
8010:10 F7 A9 D4 A4 00 20 66
8018:80 A9 85 85 09 A9 00 48
8020:20 2E 80 68 A8 E6 09 C8
8028:98 C0 10 90 F2 60 A0 00
8030:84 04 84 02 84 03 A5 09
8038:85 05 B1 04 48 20 DA FD
8040:68 48 18 65 02 85 02 68
8048:45 03 85 03 C8 98 29 1F
8050:D0 03 20 72 80 98 D0 E2
8058:A9 AB A4 02 20 66 80 A9
8060:C5 A4 03 4C 66 80 20 ED
8068:FD A9 BD 20 ED FD 98 20
8070:DA FD A9 8D 4C ED FD 20
8078:E3 03 84 07 85 08 A0 03
8080:A9 00 91 07 A5 00 C8 91
8088:07 A5 01 C8 91 07 A9 00
8090:A0 08 91 07 A5 09 C8 91
8098:07 A9 01 A0 0C 91 07 20
80A0:E3 03 20 D9 03 A0 0D B1
80A8:07 B0 01 60 4C 59 FF 00"""

OUTPUT = sys.argv[1]

s = """On the Apple, type:
]IN#2

then
^A 15B (to set 19200 baud)
^A 1D (to set 7N1)

Note that ^A means "control-A".

Then hit return. >"""

t = raw_input(s)

p = serial.Serial(SERIAL_PORT_DEVICE, 19200, bytesize=serial.SEVENBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

def send_blind(t):
   for c in t:
      p.write(c)
      time.sleep(0.25)

def send(t, wait_char=']'):
   for c in t:
      p.write(c)
      while 1:
         c1 = p.read(1)
         same = c1 == c
         if c1 == '\r':
            c1 = '\n'
         sys.stdout.write(c1)
         sys.stdout.flush()
         if same: break
   if wait_char == None: return
   while 1:
      c1 = p.read(1)
      if c1 == '\r':
         c1 = '\n'
      sys.stdout.write(c1)
      sys.stdout.flush()
      if c1 == wait_char: break

def send_lines(lines):
   for t in lines.split("\n"):
       send(t + "\r")

def wait_for(sentinal):
   f = io.BytesIO()
   while 1:
      c1 = p.read(1)
      if c1 == '\r':
         c1 = '\n'
      f.write(c1)
      sys.stdout.write(c1)
      if c1 == sentinal:
         break
   return f.getvalue()

TRACK_RE = re.compile(r"T=([0-9A-F]{2})")
SECTOR_RE = re.compile(r"([0-9A-F]{64})x([0-9A-F]{64})x([0-9A-F]{64})x([0-9A-F]{64})x([0-9A-F]{64})x([0-9A-F]{64})x([0-9A-F]{64})x([0-9A-F]{64})x\+=([0-9A-F]{2})xE=([0-9A-F]{2})")

def process_track(dump):
    dump = dump.replace("\n", "x")
    track_found = TRACK_RE.findall(dump)
    track_idx = int(track_found[0], 16)
    sectors = SECTOR_RE.findall(dump)
    sector_data = []
    for sector_idx, sector_tuple in enumerate(sectors):
       d = b''.join(binascii.unhexlify(x) for x in sector_tuple[:8])
       actual_sum = sum(ord(x) for x in d) % 256
       actual_xor = reduce(lambda a, b: a^b, (ord(x) for x in d), 0)
       expected_sum = int(sector_tuple[8], 16)
       expected_xor = int(sector_tuple[9], 16)
       if actual_sum != expected_sum or actual_xor != expected_xor:
           raise Exception("bad checksum!! aborting")
       sector_data.append(d)
       print track_idx, sector_idx
    track_data = b''.join(sector_data)
    return track_idx, track_data

def main():
    send_blind("\r\3\rPR#2\r")
    send("CALL-151\r", wait_char='*')

    for t in APPLE_BIN.split("\n"):
       send(t + "\r", wait_char="*")

    track_data_list = []

    for track in range(35):
       send("0:%02x\r" % track, wait_char="*")
       send("8000G\r", wait_char=None)
       track_dump = wait_for("*")
       actual_track, track_data = process_track(track_dump)
       track_data_list.append(track_data)

    disk_data = b''.join(track_data_list)

    f = open(OUTPUT, "wb")
    f.write(disk_data)
    f.close()

main()
