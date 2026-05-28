# Stealth-Crypt

A local CLI tool for securely encrypting and decrypting sensitive files—such as penetration testing notes or exploit payloads—using password-based encryption. No keys are stored on disk; only your password and the encrypted file are required to recover plaintext.

## Features

- **AES-256-GCM** — Authenticated encryption with a 256-bit key
- **PBKDF2-HMAC-SHA256** — Password-based key derivation (600,000 iterations)
- **Per-file salt and nonce** — Prepended to each encrypted file for standalone decryption
- **Secure shredding** — After encryption, the original plaintext is overwritten with random bytes (3 passes) before deletion
- **Hidden password input** — Passwords are read via `getpass` (no terminal echo)

## Requirements

- Python 3.9+
- [cryptography](https://pypi.org/project/cryptography/) (`pip install -r requirements.txt`)

## Installation

```bash
git clone <repository-url>
cd Stealth-Crypt
pip install -r requirements.txt
```

## Usage

### Encrypt a file

Encrypts the input file, writes the ciphertext to a new file, then shreds and deletes the original.

```bash
python -m stealth_crypt encrypt notes.txt
```

This creates `notes.txt.enc` and securely removes `notes.txt`. You will be prompted for a password twice (confirmation).

```bash
# Custom output path
python -m stealth_crypt encrypt notes.txt -o vault.bin

# Overwrite existing output file
python -m stealth_crypt encrypt notes.txt -o vault.bin --force
```

### Decrypt a file

```bash
python -m stealth_crypt decrypt notes.txt.enc
```

Writes plaintext to `notes.txt` (the `.enc` suffix is stripped by default). You will be prompted for the password once.

```bash
# Custom output path
python -m stealth_crypt decrypt vault.bin -o recovered_notes.txt

# Overwrite existing output file
python -m stealth_crypt decrypt vault.bin -o recovered_notes.txt --force
```

### Other commands

```bash
python -m stealth_crypt --version
python -m stealth_crypt --help
python -m stealth_crypt encrypt --help
python -m stealth_crypt decrypt --help
```

## Encrypted file format

Each encrypted file is a single binary blob with this layout:

| Field       | Size     | Description                          |
|------------|----------|--------------------------------------|
| Salt       | 16 bytes | Random salt for PBKDF2               |
| Nonce (IV) | 12 bytes | GCM nonce                            |
| Ciphertext | variable | Encrypted data + 16-byte GCM tag   |

```
┌──────────────┬──────────────┬─────────────────────────┐
│  Salt (16B)  │ Nonce (12B)  │  Ciphertext + GCM tag   │
└──────────────┴──────────────┴─────────────────────────┘
```

## How it works

1. **Key derivation** — A random 16-byte salt is generated. Your password is fed through PBKDF2-HMAC-SHA256 (600,000 iterations) to produce a 32-byte AES key.
2. **Encryption** — A random 12-byte nonce is generated. The file contents are encrypted with AES-256-GCM. The salt, nonce, and ciphertext are written to the output file.
3. **Shredding** — The original plaintext file is overwritten three times with cryptographically random bytes, flushed to disk, then deleted.
4. **Decryption** — Salt and nonce are read from the file header. The same PBKDF2 process derives the key from your password. GCM verifies integrity; a wrong password or tampered file causes decryption to fail.

## Project structure

```
Stealth-Crypt/
├── README.md
├── requirements.txt
└── stealth_crypt/
    ├── __init__.py      # Package version
    ├── __main__.py      # CLI entry point
    └── core.py          # Crypto primitives and file shredding
```

## Security notes

- **Use a strong password.** Key strength depends entirely on your password; PBKDF2 only slows offline guessing.
- **Back up encrypted files.** After encryption, the original is destroyed. If you lose the password or the `.enc` file, recovery is impossible.
- **Shredding limits.** Multi-pass overwrite helps on traditional HDDs. On SSDs with wear leveling and TRIM, forensic recovery may still be possible; this tool reduces casual recovery, not nation-state forensic guarantees.
- **Local use only.** This tool is intended for offline, local file protection—not for network transport protocols or key exchange.


