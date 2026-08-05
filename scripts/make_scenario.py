#!/usr/bin/env python3
"""
File: make_scenario.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Generate bundled demo scenario with hash dump for password cracking simulation.

Description:
    This script generates the demonstration scenario JSON file used by PassClash for
    training simulations. The scenario defines a hash dump that red team attacks,
    containing user accounts with various hash algorithms (MD5, SHA-256, NTLM, bcrypt).
    All plaintext passwords are guaranteed to exist in the generated wordlist, ensuring
    the default dictionary attack can successfully crack them. The scenario includes
    metadata like name, description, and time budget for the round.

Usage:  python scripts/make_scenario.py [output.json]

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from __future__ import annotations

import json
import sys
from pathlib import Path

from passclash.hashes import ALGOS, canonical_algo

# ---------- CONSTANTS
# (user, algo, plaintext) -- plaintexts must appear in the generated wordlist
ENTRIES = [
    ("admin", "md5", "admin123"),
    ("jcosta", "sha256", "summer2024"),
    ("svc_backup", "sha256", "qwerty123"),
    ("alice", "md5", "princess1"),
    ("bob", "ntlm", "trustno1"),
    ("root", "ntlm", "toor"),
    ("audit", "sha256", "passw0rd1"),
    ("vault", "bcrypt", "hunter2"),
]

SCENARIO = {
    "name": "Nexus Corp breach, hash dump",
    "description": (
        "Red team: crack as many hashes as you can before the clock runs out. "
        "Blue team: detect, lock, rotate."
    ),
    "time_budget": 240,
}

# ---------- FUNCTIONS
def main() -> int:
    """Generate the demonstration scenario and return a process status."""
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).resolve().parent.parent / "scenarios" / "default.json"
    )
    entries = []
    for user, algo, plaintext in ENTRIES:
        algo = canonical_algo(algo)
        entries.append(
            {
                "user": user,
                "algo": algo,
                "plaintext": plaintext,
                "digest": ALGOS[algo]["digest"](plaintext),
            }
        )
    data = {**SCENARIO, "hashes": entries}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} hashes -> {out_path}")
    return 0

# ---------- MAIN
if __name__ == "__main__":
    raise SystemExit(main())
