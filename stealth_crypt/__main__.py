"""CLI entry point for Stealth-Crypt."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from stealth_crypt import __version__
from stealth_crypt.core import decrypt_file, encrypt_file, shred_file


def _prompt_password(confirm: bool = False) -> str:
    password = getpass.getpass("Password: ")
    if not password:
        print("Error: password cannot be empty.", file=sys.stderr)
        sys.exit(1)
    if confirm:
        again = getpass.getpass("Confirm password: ")
        if password != again:
            print("Error: passwords do not match.", file=sys.stderr)
            sys.exit(1)
    return password


def _default_encrypted_path(source: Path) -> Path:
    return source.with_suffix(source.suffix + ".enc")


def _default_decrypted_path(source: Path) -> Path:
    name = source.name
    if name.endswith(".enc"):
        return source.with_name(name[:-4])
    return source.with_suffix(".dec")


def cmd_encrypt(args: argparse.Namespace) -> None:
    source = args.input.resolve()
    if not source.is_file():
        print(f"Error: {source} is not a file.", file=sys.stderr)
        sys.exit(1)

    destination = (args.output or _default_encrypted_path(source)).resolve()
    if destination.exists() and not args.force:
        print(f"Error: {destination} already exists. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    password = _prompt_password(confirm=True)
    encrypt_file(source, destination, password)
    shred_file(source)
    print(f"Encrypted: {destination}")
    print(f"Shredded:  {source}")


def cmd_decrypt(args: argparse.Namespace) -> None:
    source = args.input.resolve()
    if not source.is_file():
        print(f"Error: {source} is not a file.", file=sys.stderr)
        sys.exit(1)

    destination = (args.output or _default_decrypted_path(source)).resolve()
    if destination.exists() and not args.force:
        print(f"Error: {destination} already exists. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    password = _prompt_password()
    try:
        decrypt_file(source, destination, password)
    except Exception as exc:
        print(f"Error: decryption failed ({exc}). Wrong password or corrupt file.", file=sys.stderr)
        sys.exit(1)

    print(f"Decrypted: {destination}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stealth-crypt",
        description="Encrypt and decrypt sensitive files with AES-256-GCM and PBKDF2.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    encrypt_parser = subparsers.add_parser("encrypt", help="Encrypt a file and shred the original.")
    encrypt_parser.add_argument("input", type=Path, help="Plaintext file to encrypt.")
    encrypt_parser.add_argument(
        "-o", "--output", type=Path, help="Encrypted output path (default: <input>.enc)."
    )
    encrypt_parser.add_argument("-f", "--force", action="store_true", help="Overwrite output if it exists.")
    encrypt_parser.set_defaults(func=cmd_encrypt)

    decrypt_parser = subparsers.add_parser("decrypt", help="Decrypt an encrypted file.")
    decrypt_parser.add_argument("input", type=Path, help="Encrypted file (.enc).")
    decrypt_parser.add_argument(
        "-o", "--output", type=Path, help="Decrypted output path (default: strip .enc suffix)."
    )
    decrypt_parser.add_argument("-f", "--force", action="store_true", help="Overwrite output if it exists.")
    decrypt_parser.set_defaults(func=cmd_decrypt)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
