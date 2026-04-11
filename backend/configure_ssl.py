#!/usr/bin/env python3
"""Configure the TLS certificate used by the journal server.

Use this to point to a certificate issued by a real CA (e.g. Let's Encrypt).
For a self-signed cert, run generate_cert.py instead.

Usage:
    python configure_ssl.py <cert.pem> <key.pem>   # set cert paths
    python configure_ssl.py --clear                  # revert to HTTP
"""

import sys
from pathlib import Path

import auth_config


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--clear":
        auth_config.clear_ssl_config()
        print("SSL configuration cleared. Server will use plain HTTP.")
        return

    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    cert_path = Path(sys.argv[1]).resolve()
    key_path  = Path(sys.argv[2]).resolve()

    errors = []
    if not cert_path.exists():
        errors.append(f"Certificate not found: {cert_path}")
    if not key_path.exists():
        errors.append(f"Private key not found: {key_path}")
    if errors:
        for e in errors:
            print(f"Error: {e}")
        sys.exit(1)

    auth_config.set_ssl_config(str(cert_path), str(key_path))

    print("SSL configured.")
    print(f"  Certificate : {cert_path}")
    print(f"  Private key : {key_path}")
    print()
    print("Start the server with: python start.py")


if __name__ == "__main__":
    main()
