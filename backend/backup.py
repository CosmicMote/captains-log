"""
Encrypted backup utilities for Captain's Log.

File format:
  Offset   Size  Field
  ------   ----  -----
       0      4  Magic bytes: b'CLOG'
       4      1  Version: 0x01
       5     16  PBKDF2 salt (random)
      21     12  AES-GCM IV (random)
      33      *  AES-256-GCM ciphertext + 16-byte authentication tag

Key derivation: PBKDF2-HMAC-SHA256, 260 000 iterations → 32-byte key
Encryption:     AES-256-GCM (authenticated; wrong password → decryption error)
"""

import os
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

MAGIC = b'CLOG'
VERSION = 1
PBKDF2_ITERATIONS = 260_000  # NIST SP 800-132 recommended minimum (2023)

_HEADER_SIZE = len(MAGIC) + 1 + 16 + 12  # 33 bytes before ciphertext
_MIN_FILE_SIZE = _HEADER_SIZE + 16        # + GCM tag minimum

SQLITE_MAGIC = b'SQLite format 3\x00'


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode('utf-8'))


def encrypt_db(db_path: Path, password: str) -> bytes:
    """Read db_path, encrypt with password, return backup bytes."""
    salt = os.urandom(16)
    iv   = os.urandom(12)
    key  = _derive_key(password, salt)

    plaintext = db_path.read_bytes()
    # AESGCM.encrypt() appends the 16-byte GCM tag to the ciphertext
    ciphertext_and_tag = AESGCM(key).encrypt(iv, plaintext, None)

    return MAGIC + bytes([VERSION]) + salt + iv + ciphertext_and_tag


def decrypt_backup(data: bytes, password: str) -> bytes:
    """Decrypt backup bytes with password; raise ValueError on any failure."""
    if len(data) < _MIN_FILE_SIZE:
        raise ValueError("File is too small to be a valid backup")

    if data[:4] != MAGIC:
        raise ValueError("Not a Captain's Log backup file")

    version = data[4]
    if version != VERSION:
        raise ValueError(f"Unsupported backup version {version}")

    salt               = data[5:21]
    iv                 = data[21:33]
    ciphertext_and_tag = data[33:]

    key = _derive_key(password, salt)
    try:
        return AESGCM(key).decrypt(iv, ciphertext_and_tag, None)
    except Exception:
        raise ValueError("Decryption failed — wrong password or corrupted backup")


def is_valid_sqlite(data: bytes) -> bool:
    """Return True if data begins with the SQLite file header."""
    return data[:16] == SQLITE_MAGIC
