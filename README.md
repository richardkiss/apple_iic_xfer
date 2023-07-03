[![PyPI - Version](https://img.shields.io/pypi/v/apple-ii-utils.svg)](https://pypi.org/project/apple-ii-utils)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/apple-ii-utils.svg)](https://pypi.org/project/apple-ii-utils)

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)

## Installation

```console
pip install apple-ii-utils
```

## License


apple_iic_xfer
==============

A hack to copy DOS 3.3 (or ProDOS) formatted Apple ][ disks to a modern machine via the Apple //c serial port.

Intro
=====

When I was a kid, I had an Apple ][ which I hacked the heck out of. I independently developed a bunch of software, some of which was not terrible, which I wanted to archive. So I wrote this hack, along with an Apple //c I bought off eBay for $25 a few years ago, lets me dump a DOS 3.3-formatted disk one track at a time out the serial port, capturing and reassembling it into a .dsk file, suitable for use with Apple // emulators.

I know ADTPro <http://adtpro.sourceforge.net/> exists, but it seemed like overkill and I hate Java. This is an ugly but functional little hack that is tiny, written in Python, and transfers a 143K disk in about four minutes.

Usage
=====

You need an Apple //c serial null-modem cable. I bought mine off of <http://www.retrofloppy.com/products.html>. You also need a modern machine with a serial port, Python, and pyserial.

Connect the two machines. You need to determine what your local serial port is named. On my Linux machine, it's /dev/ttyUSB0 (I use a USB-serial adaptor). Change SERIAL_PORT_DEVICE on line 15 of xferdos33.py if necessary.

Boot a DOS 3.3 disk on the Apple //c, so the RWTS code which reads raw disk sectors is available. Get to a BASIC prompt "]". Then start the Python script on the modern machine.

```$ python xferdos33.py output.dsk```

(If you see the message "ImportError: No module named serial", you need to install pyserial with `pip install pyserial`.)

You will see instructions on what to type on the Apple //c to get things started. Follow the instructions.

Wait about four minutes. Your output disk will be dumped into output.dsk. Tada!

Caveats
=======

As mentioned, this code is not great. It does include simple checksums of the disk data, although in my experience, the short serial port connection is pretty much perfect.

I've only tested this on the Apple //c, which assumes the serial port is #2 (as in "IN#2" and "PR#2"). It might work on an Apple //e or Apple ][+ with a super serial card, maybe an Apple //gs. You may have to change how the set-up works on the Apple side. Maybe not though.

It doesn't handle DOS 3.3 errors very cleverly -- it just aborts. The upside is that if you get a .dsk file, you can feel pretty safe that it transfered okay.
