#!/usr/bin/env python3
"""Generate a self-signed TLS certificate for local HTTPS development.

Outputs cert.pem and key.pem to backend/certs/ and saves the paths
to auth_config.json so start.py picks them up automatically.

Run from the backend directory:
    python generate_cert.py
"""

import datetime
import ipaddress
import sys
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

import auth_config

CERTS_DIR    = Path(__file__).parent / "certs"
CERT_FILE    = CERTS_DIR / "cert.pem"
KEY_FILE     = CERTS_DIR / "key.pem"
VALIDITY_DAYS = 825   # browsers accept self-signed certs well past 398 days


def main() -> None:
    print("Generating self-signed TLS certificate…")

    CERTS_DIR.mkdir(exist_ok=True)

    # Private key
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # Certificate
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now  = datetime.datetime.now(datetime.timezone.utc)

    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=VALIDITY_DAYS))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )

    # Write private key (read-only by owner)
    KEY_FILE.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    KEY_FILE.chmod(0o600)

    # Write certificate
    CERT_FILE.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    # Persist paths so start.py uses them automatically
    auth_config.set_ssl_config(str(CERT_FILE.resolve()), str(KEY_FILE.resolve()))

    print(f"Certificate : {CERT_FILE}")
    print(f"Private key : {KEY_FILE}")
    print(f"Valid for   : {VALIDITY_DAYS} days")
    print()
    print("SSL config saved. Start the server with:")
    print("  python start.py")
    print()
    print("Your browser will warn about the self-signed cert on first visit.")
    print("To silence the warning, add cert.pem to your system's trust store.")


if __name__ == "__main__":
    main()
