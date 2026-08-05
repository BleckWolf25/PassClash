"""
File: state.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Process-wide game state management for multi-user PassClash simulation.

Description:
    This module provides the singleton GameState instance shared across all Streamlit
    sessions (Red Team, Blue Team, Game Master) and the cracking engine thread.
    The StateStore class ensures thread-safe access to the shared state, enabling
    real-time multi-user collaboration. This shared state architecture is what makes
    PassClash a multi-player simulation rather than a single-user tool.

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from __future__ import annotations

import threading
from pathlib import Path

from .scenario import GameState, load_scenario

# ---------- CONSTANTS
DEFAULT_SCENARIO = Path(__file__).resolve().parent.parent / "scenarios" / "default.json"
DEFAULT_WORDLIST = Path(__file__).resolve().parent.parent / "wordlists" / "rockyou_top5k.txt"

# ---------- CLASS
class StateStore:
    """Synchronize access to the application's single shared game state."""

    def __init__(self) -> None:
        """Create an empty store guarded by a lock."""
        self._state: GameState | None = None
        self._lock = threading.Lock()

    def get(self, scenario_path: str | Path | None = None) -> GameState:
        """Return the shared state, loading it once when first requested."""
        if self._state is None:
            with self._lock:
                if self._state is None:
                    path = Path(scenario_path) if scenario_path else DEFAULT_SCENARIO
                    self._state = load_scenario(path)
        return self._state

    def reset(self, scenario_path: str | Path | None = None) -> GameState:
        """Discard the current state and load a fresh scenario."""
        with self._lock:
            path = Path(scenario_path) if scenario_path else DEFAULT_SCENARIO
            self._state = load_scenario(path)
            return self._state


_STATE_STORE = StateStore()

# ---------- FUNCTIONS
def get_state(scenario_path: str | Path | None = None) -> GameState:
    """Return the shared game state, loading *scenario_path* on first use."""
    return _STATE_STORE.get(scenario_path)


def reset_state(scenario_path: str | Path | None = None) -> GameState:
    """Replace the shared state (new round) with a fresh scenario."""
    return _STATE_STORE.reset(scenario_path)
