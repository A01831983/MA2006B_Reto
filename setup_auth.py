#! /usr/bin/env python

"""
First-time setup helper for the authentication module.

Creates a .env file with a random JWT_SECRET if it does not already exist.
Safe to run multiple times: skips files that already exist.
"""

__author__ = "Diego Octavio Arias Inchaustegui"

import os
import secrets
import string


ENV_FILE = ".env"
SECRET_LENGTH = 48
SECRET_PREFIX = "cmonarca-"


def generate_secret(length: int = SECRET_LENGTH) -> str:
    alphabet = string.ascii_letters + string.digits
    body = "".join(secrets.choice(alphabet) for _ in range(length))
    return SECRET_PREFIX + body


def setup_env_file() -> None:
    if os.path.exists(ENV_FILE):
        print(f"  [SKIP] {ENV_FILE} already exists.")
        return

    secret = generate_secret()
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write(f"JWT_SECRET={secret}\n")

    print(f"  [OK]   {ENV_FILE} created with a random JWT_SECRET.")


def main() -> None:
    print("=" * 60)
    print("Setting up authentication environment...")
    print("=" * 60)

    setup_env_file()

    print("=" * 60)
    print("Done.")
    print()
    print("Next steps:")
    print("  1. Generate sample data:    python examples/create_dummy_data.py")
    print("  2. Start the server:        python run.py --db <db.json> --cert <cert.pem> --key <key.pem>")
    print()
    print("On first startup, an initial admin will be created:")
    print("  Email:    admin@casamonarca.mx")
    print("  Password: admin123  (must be changed on first login)")
    print("=" * 60)


if __name__ == "__main__":
    main()