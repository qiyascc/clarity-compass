import argparse
import getpass
import secrets
import sys

from clarity_api.security import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(prog="clarity-api")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "hash-password", help="hash an admin password for CLARITY_ADMIN_PASSWORD_HASH"
    )
    commands.add_parser("generate-secret", help="print a random secret for keys")
    args = parser.parse_args()

    if args.command == "hash-password":
        password = getpass.getpass("Password: ")
        if password != getpass.getpass("Repeat: "):
            sys.exit("passwords do not match")
        print(hash_password(password))
    elif args.command == "generate-secret":
        print(secrets.token_urlsafe(32))


if __name__ == "__main__":
    main()
