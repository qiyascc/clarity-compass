import argparse
from pathlib import Path

from clarity_saliency.registry import fetch


def main() -> None:
    parser = argparse.ArgumentParser(prog="clarity-saliency")
    commands = parser.add_subparsers(dest="command", required=True)
    pull = commands.add_parser("fetch", help="download and verify the saliency models")
    pull.add_argument("directory", type=Path, nargs="?", default=Path("models"))
    args = parser.parse_args()
    for path in fetch(args.directory):
        print(path)


if __name__ == "__main__":
    main()
