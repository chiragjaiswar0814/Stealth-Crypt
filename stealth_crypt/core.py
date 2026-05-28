"""Cryptographic primitives and file shredding."""

from __future__ import annotations

import os
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
PBKDF2_ITERATIONS = 600_000


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_bytes(plaintext: bytes, password: str) -> bytes:
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    return salt + nonce + ciphertext


def decrypt_bytes(blob: bytes, password: str) -> bytes:
    if len(blob) < SALT_SIZE + NONCE_SIZE + 16:
        raise ValueError("File is too short to be a valid encrypted payload.")

    salt = blob[:SALT_SIZE]
    nonce = blob[SALT_SIZE : SALT_SIZE + NONCE_SIZE]
    ciphertext = blob[SALT_SIZE + NONCE_SIZE :]

    key = derive_key(password, salt)
    return AESGCM(key).decrypt(nonce, ciphertext, None)


def encrypt_file(source: Path, destination: Path, password: str) -> None:
    plaintext = source.read_bytes()
    destination.write_bytes(encrypt_bytes(plaintext, password))


def decrypt_file(source: Path, destination: Path, password: str) -> None:
    blob = source.read_bytes()
    destination.write_bytes(decrypt_bytes(blob, password))


def shred_file(path: Path, passes: int = 3) -> None:
    """Overwrite file contents with random bytes, then delete."""
    if not path.is_file():
        raise FileNotFoundError(f"Cannot shred: {path} is not a file.")

    size = path.stat().st_size
    if size == 0:
        path.unlink()
        return

    with path.open("r+b") as handle:
        for _ in range(passes):
            handle.seek(0)
            handle.write(os.urandom(size))
            handle.flush()
            os.fsync(handle.fileno())

    path.unlink()
