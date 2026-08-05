"""
File: scoring.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Scoring system for red and blue teams with weighted algorithm points and detection bonuses.

Description:
    This module implements the competitive scoring system for PassClash. Red team earns points
    for hash recoveries (weighted by algorithm difficulty), speed bonuses, and incurs alert
    penalties. Blue team earns points for early detection, locked accounts, successful rotations,
    and residual hashes remaining at round end. Detection logic evaluates blue-team monitoring
    against attack telemetry to trigger alerts based on attempt thresholds.

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from __future__ import annotations

from . import hashes
from .events import emit, recent
from .scenario import GameState

# ---------- CONSTANTS
POINTS_PER_WEIGHT = 10
DETECTION_EARLY_BONUS = 25
ALERT_PENALTY = 5
SPEED_BONUS = 25
DETECTION_ATTEMPT_THRESHOLD = 500

# ---------- FUNCTIONS
def _crack_time(state: GameState, user: str) -> float | None:
    t = state.target_for(user)
    if t is None or t.recovered_at is None:
        return None
    if state.round_started is None:
        return None
    return t.recovered_at - state.round_started


def red_score(state: GameState, events: list[dict] | None = None) -> dict:
    """Red team totals."""
    points = 0.0
    per_target: list[dict] = []
    for t in state.targets:
        if not t.recovered:
            per_target.append({"user": t.user, "algo": t.algo, "points": 0})
            continue
        base = hashes.ALGOS[t.algo]["weight"] * POINTS_PER_WEIGHT
        points += base
        per_target.append(
            {"user": t.user, "algo": t.algo, "points": base,
             "time": _crack_time(state, t.user)}
        )

    events = events if events is not None else recent("gm", limit=400)
    alerts = [e for e in events if e["kind"] == "alert"]
    penalty = len(alerts) * ALERT_PENALTY

    speed_bonus = 0.0
    if all(t.recovered for t in state.targets):
        budget = float(state.time_budget)
        finished_at = max((t.recovered_at or 0.0) for t in state.targets)
        if state.round_started and finished_at - state.round_started <= budget * 0.5:
            speed_bonus = SPEED_BONUS

    total = points - penalty + speed_bonus
    return {
        "points": round(total, 1),
        "cracks": sum(1 for t in state.targets if t.recovered),
        "crack_points": round(points, 1),
        "alerts": len(alerts),
        "alert_penalty": penalty,
        "speed_bonus": speed_bonus,
        "per_target": per_target,
    }


def blue_score(state: GameState, events: list[dict] | None = None) -> dict:
    """Blue team totals."""
    events = events if events is not None else recent("gm", limit=400)
    alerts = [e for e in events if e["kind"] == "alert"]

    detection_points = 0.0
    for alert in alerts:
        alert_at = alert.get("t", 0.0)
        if state.round_started and alert_at - state.round_started < state.time_budget * 0.25:
            detection_points += DETECTION_EARLY_BONUS
        else:
            detection_points += 10

    locked_never_cracked = [
        t for t in state.targets if t.locked and not t.recovered
    ]
    locked_points = sum(
        hashes.ALGOS[t.algo]["weight"] * POINTS_PER_WEIGHT
        for t in locked_never_cracked
    )

    rotation_points = 25.0 if state.rotation_done else 0.0

    standing = [t for t in state.targets if not t.recovered]
    residual_points = sum(
        hashes.ALGOS[t.algo]["weight"] * POINTS_PER_WEIGHT for t in standing
    )

    total = detection_points + locked_points + rotation_points + residual_points
    return {
        "points": round(total, 1),
        "detection": round(detection_points, 1),
        "locked_points": locked_points,
        "rotation_points": rotation_points,
        "residual": round(residual_points, 1),
        "hashes_standing": len(standing),
        "alerts": len(alerts),
    }

def check_detection(state: GameState) -> bool:
    """Evaluate blue's detection rules against live telemetry.

    Fires one alert the first time the attempt counter crosses the threshold
    while monitoring is enabled. Called from the blue page on every render --
    a SOC that never opens its dashboard never detects anything.
    """
    if not state.monitoring or state.alert_fired:
        return False
    if state.attack_active and state.attempts >= DETECTION_ATTEMPT_THRESHOLD:
        state.alert_fired = True
        emit(
            "alert",
            f"Brute-force detected: {state.attempts:,} attempts "
            f"(mode: {state.attack_mode or 'unknown'})",
            team="both",
        )
        return True
    return False


def round_summary(state: GameState) -> dict:
    """Per-target verdicts for the end-of-round table."""
    rows = []
    for t in state.targets:
        verdict = "cracked" if t.recovered else ("locked" if t.locked else "standing")
        rows.append(
            {
                "user": t.user,
                "algo": t.algo,
                "plaintext": t.plaintext if t.recovered else "",
                "verdict": verdict,
                "recovered_at": t.recovered_at,
            }
        )
    return {
        "rows": rows,
        "red": red_score(state),
        "blue": blue_score(state),
    }
