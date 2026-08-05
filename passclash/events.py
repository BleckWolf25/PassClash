"""
File: events.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    In-memory event bus for real-time game event distribution across teams.

Description:
    This module implements a thread-safe in-memory event bus that broadcasts game events
    (attacks, cracks, alerts, mitigations, GM injections) with team visibility controls.
    Each event is tagged with a team flag determining which roles can see it. The UI
    components drain the bus to display events appropriate to each team's perspective.

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from __future__ import annotations

import threading
import time
from typing import Literal

# ---------- CONSTANTS
Team = Literal["red", "blue", "gm", "both"]

_EVENTS: list[dict] = []
_LOCK = threading.Lock()
_MAX = 1500

_VISIBILITY: dict[Team, set[str]] = {
    "red": {"red", "both"},
    "blue": {"blue", "both"},
    "gm": {"red", "blue", "gm", "both"},
}

# ---------- FUNCTIONS
def emit(kind: str, message: str, team: Team = "both", **extra) -> None:
    """Append one event to the bus (thread-safe, bounded)."""
    with _LOCK:
        _EVENTS.append(
            {
                "t": time.time(),
                "kind": kind,
                "msg": message,
                "team": team,
                **extra,
            }
        )
        if len(_EVENTS) > _MAX:
            del _EVENTS[: len(_EVENTS) - _MAX]


def recent(role: Team = "gm", limit: int = 60) -> list[dict]:
    """Most recent events visible to *role*, newest first."""
    allowed = _VISIBILITY[role]
    with _LOCK:
        events = [e for e in _EVENTS if e["team"] in allowed]
        return list(reversed(events[-limit:]))


def clear() -> None:
    """Remove every event from the in-memory event bus."""
    with _LOCK:
        _EVENTS.clear()
