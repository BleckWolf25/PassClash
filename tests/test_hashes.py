"""
File: test_hashes.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Unit tests for hash algorithm correctness using RFC test vectors and round-trips.

Description:
    This module validates the cryptographic hash implementations (MD4, MD5, SHA-1, SHA-256,
    NTLM, bcrypt) against known RFC test vectors and ensures digest/verification round-trips
    work correctly. Tests verify algorithm registry completeness, case-insensitive hex
    comparison, and proper bcrypt verification behavior including rejection of wrong passwords.

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from passclash import hashes

# ---------- FIXTURES
def test_md4_empty_vector():
    """The public MD4 implementation matches the empty-message RFC vector."""
    assert hashes.md4_digest(b"").hex() == "31d6cfe0d16ae931b73c59d7e0c089c0"


def test_md4_abc_vector():
    """The public MD4 implementation matches the ``abc`` RFC vector."""
    assert hashes.md4_digest(b"abc").hex() == "a448017aaf21d8525fc10ae87aa6729d"


def test_ntlm_password_vector():
    """NTLM hashes the UTF-16LE password with MD4."""
    # MD4 of the UTF-16LE encoding of "password"
    assert hashes.ntlm_hex("password") == "8846f7eaee8fb117ad06bdd830b7586c"


def test_md5_password_vector():
    """MD5 output matches the known password test vector."""
    assert hashes.md5_hex("password") == "5f4dcc3b5aa765d61d8327deb882cf99"


def test_sha1_password_vector():
    """SHA-1 output matches the known password test vector."""
    assert hashes.sha1_hex("password") == "5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8"


def test_sha256_password_vector():
    """SHA-256 output matches the known password test vector."""
    assert (
        hashes.sha256_hex("password")
        == "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
    )


def test_bcrypt_roundtrip():
    """bcrypt verification accepts the source password and rejects another."""
    digest = hashes.bcrypt_hash("hunter2", rounds=4)
    assert hashes.verify_digest("bcrypt", "hunter2", digest)
    assert not hashes.verify_digest("bcrypt", "hunter3", digest)


def test_verify_digest_is_case_insensitive():
    """Hexadecimal digest comparison is case-insensitive."""
    digest = hashes.md5_hex("password")
    assert hashes.verify_digest("MD5", "password", digest.upper())


def test_registry_is_complete():
    """Every advertised algorithm has usable digest and verification functions."""
    for algo in ("MD5", "SHA-256", "NTLM", "bcrypt"):
        entry = hashes.ALGOS[algo]
        assert entry["weight"] > 0
        assert entry["base_speed"] > 0
        # digest() and verify() must agree
        digest = entry["digest"]("letmein")
        assert entry["verify"]("letmein", digest)
        assert not entry["verify"]("wrong", digest)
