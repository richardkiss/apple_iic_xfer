import sys

from .applesoft import list_applesoft


def main():
    blob = open(sys.argv[1], "rb").read()
    print(list_applesoft(blob))


if __name__ == "__main__":
    main()
