import argparse
from pathlib import Path

from apple_iic_xfer.apple_ii_utils.dos33 import catalog_entries, open_file

DSK_SIZE = 16 * 35 * 256


def parse_args():
    parser = argparse.ArgumentParser(description="undsk - Tool to process .dsk files")

    # Positional argument: List of .dsk files
    parser.add_argument("dsk_files", nargs="+", metavar="file.dsk", type=Path, help="List of .dsk files to process")

    # Optional arguments can be added here if needed

    args = parser.parse_args()
    return args


def undsk(dsk_file: Path):
    print(f"Processing {dsk_file}")
    with open(dsk_file, "rb") as f:
        disk = f.read(DSK_SIZE)
    if len(disk) < DSK_SIZE:
        print(f"too short: {dsk_file}")
        return
    output_dir = dsk_file.with_suffix("")
    try:
        output_dir.mkdir(exist_ok=False)
    except FileExistsError:
        print(f"already exists: {output_dir}")
        return
    for entry in catalog_entries(disk):
        file_contents = open_file(disk, entry)
        file_name = entry["name"]
        target = output_dir / file_name
        with open(target, "wb") as f:
            f.write(file_contents)


def main():
    args = parse_args()
    dsk_files = args.dsk_files

    # Process the list of .dsk files here
    for dsk_file in dsk_files:
        undsk(dsk_file)


if __name__ == "__main__":
    main()
