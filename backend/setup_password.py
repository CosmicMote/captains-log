#!/usr/bin/env python3
"""Set or change the journal login password.

Run from the backend directory:
    python setup_password.py
"""

import getpass
import sys

import auth
import auth_config


def main() -> None:
    print("Journal Password Setup")
    print("=" * 30)

    if auth_config.get_password_hash():
        print("A password is already configured.")
        answer = input("Change it? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return

    while True:
        password = getpass.getpass("Enter new password: ")
        if len(password) < 8:
            print("Password must be at least 8 characters. Try again.")
            continue
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match. Try again.")
            continue
        break

    auth_config.set_password_hash(auth.hash_password(password))
    print("Password set successfully. You can now start the server.")


if __name__ == "__main__":
    main()
