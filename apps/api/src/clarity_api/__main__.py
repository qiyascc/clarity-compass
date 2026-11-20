import argparse
import getpass
import json
import secrets
import sys

from pydantic import SecretStr

from clarity_api.app import create_app
from clarity_api.queue import RecordingQueue
from clarity_api.security import hash_password
from clarity_api.settings import Settings


def main() -> None:
    parser = argparse.ArgumentParser(prog="clarity-api")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "hash-password", help="hash an admin password for CLARITY_ADMIN_PASSWORD_HASH"
    )
    commands.add_parser("generate-secret", help="print a random secret for keys")
    commands.add_parser("openapi", help="print the OpenAPI schema")
    args = parser.parse_args()

    if args.command == "hash-password":
        password = getpass.getpass("Password: ")
        if password != getpass.getpass("Repeat: "):
            sys.exit("passwords do not match")
        print(hash_password(password))
    elif args.command == "generate-secret":
        print(secrets.token_urlsafe(32))
    elif args.command == "openapi":
        print(json.dumps(_schema(), indent=2))


def _schema() -> dict[str, object]:
    placeholder = SecretStr("unused")
    settings = Settings(
        database_url="postgresql+asyncpg://unused",
        secret_key=placeholder,
        credentials_key=placeholder,
        admin_password_hash=placeholder,
        _env_file=None,
    )
    return create_app(settings, RecordingQueue()).openapi()


if __name__ == "__main__":
    main()
