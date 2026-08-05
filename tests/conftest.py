"""
File: conftest.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Shared test fixtures and helper functions for PassClash test suite.

Description:
    This module provides common test fixtures and builder functions used across the
    PassClash test suite. The make_state helper creates minimal GameState instances
    for testing various scenarios without requiring full scenario file loading.
    These fixtures enable isolated, fast unit testing of individual components.

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from passclash import hashes
from passclash.scenario import GameState, Target


# ---------- FIXTURE
def make_state(*entries, budget: int = 120) -> GameState:
    """Build a small game state from ``(user, algorithm, plaintext)`` tuples."""
    targets = [
        Target(
            user=user,
            algo=hashes.canonical_algo(algo),
            digest=hashes.ALGOS[hashes.canonical_algo(algo)]["digest"](plain),
            plaintext=plain,
        )
        for user, algo, plain in entries
    ]
    return GameState(name="test", time_budget=budget, targets=targets)
