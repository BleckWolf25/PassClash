"""
File: hashes.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Cryptographic hash algorithm implementations for password cracking simulation.

Description:
    This module provides uniform hash algorithm implementations (MD5, SHA-256, NTLM, bcrypt)
    used throughout PassClash. Each algorithm exposes digest() and verify() functions for
    consistent interface. Includes a pure Python MD4 implementation for NTLM support and
    maintains an algorithm registry with metadata for scoring, speed simulation, and display.
    All algorithms are designed for educational password cracking scenarios.

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from __future__ import annotations

import hashlib
import struct

try:
    import bcrypt
except ImportError:
    bcrypt = None


# Round 3 uses a fixed index permutation (RFC 1320 section 3.4), not the
# linear/quadratic ones of rounds 1 and 2.
_MD4_R3 = (0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15)

# ---------- FUNCTIONS
def _md4_f(left: int, middle: int, right: int) -> int:
    """Return the RFC 1320 round-one Boolean function."""
    return (left & middle) | (~left & right)


def _md4_g(left: int, middle: int, right: int) -> int:
    """Return the RFC 1320 round-two Boolean function."""
    return (left & middle) | (left & right) | (middle & right)


def _md4_h(left: int, middle: int, right: int) -> int:
    """Return the RFC 1320 round-three Boolean function."""
    return left ^ middle ^ right


def _rotate_left(value: int, shift: int) -> int:
    """Rotate a 32-bit unsigned integer left by *shift* bits."""
    return ((value << shift) | (value >> (32 - shift))) & 0xFFFFFFFF


def _md4_block(state: tuple[int, int, int, int], block: bytes) -> tuple[int, int, int, int]:
    """Process one 64-byte MD4 *block* and return the next hash state."""
    a, b, c, d = state
    original = state
    words = struct.unpack("<16I", block)

    for index, shift in enumerate((3, 7, 11, 19) * 4):
        a = _rotate_left((a + _md4_f(b, c, d) + words[index]) & 0xFFFFFFFF, shift)
        a, b, c, d = d, a, b, c
    for index, shift in enumerate((3, 5, 9, 13) * 4):
        word_index = (index % 4) * 4 + index // 4
        a = _rotate_left(
            (a + _md4_g(b, c, d) + words[word_index] + 0x5A827999) & 0xFFFFFFFF,
            shift,
        )
        a, b, c, d = d, a, b, c
    for index, shift in enumerate((3, 9, 11, 15) * 4):
        a = _rotate_left(
            (a + _md4_h(b, c, d) + words[_MD4_R3[index]] + 0x6ED9EBA1) & 0xFFFFFFFF,
            shift,
        )
        a, b, c, d = d, a, b, c

    return tuple((value + initial) & 0xFFFFFFFF for value, initial in zip((a, b, c, d), original))


def md4_digest(message: bytes) -> bytes:
    """Return the MD4 digest of *message* (RFC 1320)."""
    padded = message + b"\x80"
    padded += b"\x00" * ((56 - len(padded) % 64) % 64)
    padded += struct.pack("<Q", (len(message) * 8) & 0xFFFFFFFFFFFFFFFF)
    state = (0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476)
    for offset in range(0, len(padded), 64):
        state = _md4_block(state, padded[offset:offset + 64])
    return struct.pack("<4I", *state)


# ---------- DIGESTION OF PRIMITIVES
def md5_hex(plaintext: str) -> str:
    """Return the MD5 hexadecimal digest of *plaintext*."""
    return hashlib.md5(plaintext.encode("utf-8")).hexdigest()


def sha1_hex(plaintext: str) -> str:
    """Return the SHA-1 hexadecimal digest of *plaintext*."""
    return hashlib.sha1(plaintext.encode("utf-8")).hexdigest()


def sha256_hex(plaintext: str) -> str:
    """Return the SHA-256 hexadecimal digest of *plaintext*."""
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def ntlm_hex(plaintext: str) -> str:
    """NTLM: MD4 over UTF-16LE."""
    return md4_digest(plaintext.encode("utf-16-le")).hex()


def bcrypt_hash(plaintext: str, rounds: int = 10) -> str:
    """Hash *plaintext* with bcrypt using *rounds* (log2 cost factor).

    Rounds default to 10 (about 80 ms) so blue-team rotations stay snappy
    while remaining genuinely expensive for the cracker.
    """
    if bcrypt is None:
        raise RuntimeError("bcrypt is required for this scenario")
    return bcrypt.hashpw(plaintext.encode("utf-8"),
                         bcrypt.gensalt(rounds=rounds)).decode("utf-8")


def _bcrypt_verify(plaintext: str, digest: str) -> bool:
    """Return whether *plaintext* matches a bcrypt *digest*."""
    if bcrypt is None:
        raise RuntimeError("bcrypt is required for this scenario")
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), digest.encode("utf-8"))
    except ValueError:
        return False


# ---------- ALGORITHM REGISTRY
ALGOS: dict[str, dict] = {
    "MD5": {
        "digest": md5_hex,
        "verify": lambda p, d: md5_hex(p) == d.lower(),
        # Expected throughput of a single worker at the simulated speed cap.
        "base_speed": 2_000_000,
        # Scoring weight -- harder algorithms are worth more red points.
        "weight": 1,
        "label": "MD5",
    },
    "SHA-256": {
        "digest": sha256_hex,
        "verify": lambda p, d: sha256_hex(p) == d.lower(),
        "base_speed": 800_000,
        "weight": 3,
        "label": "SHA256",
    },
    "NTLM": {
        "digest": ntlm_hex,
        "verify": lambda p, d: ntlm_hex(p) == d.lower(),
        "base_speed": 2_000_000,
        "weight": 1,
        "label": "NTLM",
    },
    "bcrypt": {
        "digest": lambda p: bcrypt_hash(p, rounds=10),
        "verify": _bcrypt_verify,
        "base_speed": 12,
        "weight": 10,
        "label": "bcrypt",
    },
}


def canonical_algo(name: str) -> str:
    """Map a case/separator-insensitive name to its canonical ``ALGOS`` key.

    ``"sha256"``, ``"SHA-256"`` and ``"SHA_256"`` all resolve to
    ``"SHA-256"``; unknown names raise :class:`KeyError`.
    """
    norm = name.strip().lower().replace("-", "").replace("_", "").replace(" ", "")
    for key in ALGOS:
        key_norm = key.lower().replace("-", "").replace("_", "").replace(" ", "")
        if key_norm == norm:
            return key
    raise KeyError(f"unknown algorithm: {name!r}")


def verify_digest(algo: str, plaintext: str, digest: str) -> bool:
    """Verify *plaintext* against *digest* using the algorithm's checker."""
    return ALGOS[canonical_algo(algo)]["verify"](plaintext, digest)


def crackable_speed(algo: str) -> int:
    """Theoretical hashes-per-second of one worker for *algo*."""
    return ALGOS[canonical_algo(algo)]["base_speed"]
