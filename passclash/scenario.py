"""
File: scenario.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Scenario loading and shared game state management for multi-user simulation.

Description:
    This module handles scenario JSON loading and maintains the shared GameState object
    used across all Streamlit sessions and the cracking engine thread. The state
    encompasses targets, round timing, team settings, and attack telemetry. Blue-team
    actions (lockouts, rotations, rate limiting) mutate this state for real-time
    effect on red-team cracking operations. Thread-safe operations ensure consistent
    state across concurrent users.

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from __future__ import annotations

import json
import secrets
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import hashes

# ---------- DATACLASSES
@dataclass
class Target:
    """One entry of the hash dump."""

    user: str
    algo: str
    digest: str
    plaintext: str  # answer key -- only shown to the GM / at round end
    recovered: bool = False
    recovered_at: float | None = None
    locked: bool = False

    def __post_init__(self) -> None:
        # Hex digests are stored lowercase for display; bcrypt strings are
        # case-sensitive base64 (A-Z is significant) so they must stay as-is.
        if hashes.canonical_algo(self.algo) != "bcrypt":
            self.digest = self.digest.lower()


@dataclass
class ScenarioDetails:
    """Scenario data that persists for the lifetime of one game state."""

    name: str = "untitled"
    description: str = ""
    time_budget: int = 300  # seconds
    targets: list[Target] = field(default_factory=list)


@dataclass
class RoundClock:
    """Mutable data maintained by the game master's round clock."""

    round_started: float | None = None
    round_paused: bool = False
    paused_remaining: float | None = None
    round_over: bool = False


@dataclass
class RedTeamSettings:
    """The red team's hardware configuration."""

    speed_multiplier: float = 1.0
    gpu_upgrades: int = 0


@dataclass
class BlueTeamSettings:
    """The blue team's active defensive mitigations."""

    monitoring: bool = False
    rate_limited: bool = False
    policy_enforced: bool = False
    rotation_done: bool = False


@dataclass
class AttackTelemetry:
    """Attack data shared between the cracking engine and blue team."""

    attempts: int = 0
    attack_active: bool = False
    attack_mode: str | None = None
    alert_fired: bool = False


# ---------- CLASS
class GameState:
    """Mutable, thread-safe state for one PassClash training round."""

    def __init__(
        self,
        name: str = "untitled",
        description: str = "",
        time_budget: int = 300,
        targets: list[Target] | None = None,
    ) -> None:
        """Create a game state from scenario data and independent subsystems."""
        if not targets:
            raise ValueError("a scenario needs at least one target")
        self._scenario = ScenarioDetails(name, description, time_budget, targets)
        self._round = RoundClock()
        self._red = RedTeamSettings()
        self._blue = BlueTeamSettings()
        self._attack = AttackTelemetry()
        self.lock = threading.RLock()

    @property
    def name(self) -> str:
        """Return the scenario name."""
        return self._scenario.name

    @property
    def description(self) -> str:
        """Return the scenario description."""
        return self._scenario.description

    @property
    def time_budget(self) -> int:
        """Return the round time budget in seconds."""
        return self._scenario.time_budget

    @property
    def targets(self) -> list[Target]:
        """Return the scenario targets."""
        return self._scenario.targets

    @property
    def round_started(self) -> float | None:
        """Return when the round began, if it has begun."""
        return self._round.round_started

    @round_started.setter
    def round_started(self, value: float | None) -> None:
        self._round.round_started = value

    @property
    def round_paused(self) -> bool:
        """Return whether the round clock is paused."""
        return self._round.round_paused

    @round_paused.setter
    def round_paused(self, value: bool) -> None:
        self._round.round_paused = value

    @property
    def paused_remaining(self) -> float | None:
        """Return the duration stored while the round is paused."""
        return self._round.paused_remaining

    @paused_remaining.setter
    def paused_remaining(self, value: float | None) -> None:
        self._round.paused_remaining = value

    @property
    def round_over(self) -> bool:
        """Return whether the round has ended."""
        return self._round.round_over

    @round_over.setter
    def round_over(self, value: bool) -> None:
        self._round.round_over = value

    @property
    def speed_multiplier(self) -> float:
        """Return the red team's current speed multiplier."""
        return self._red.speed_multiplier

    @speed_multiplier.setter
    def speed_multiplier(self, value: float) -> None:
        self._red.speed_multiplier = value

    @property
    def gpu_upgrades(self) -> int:
        """Return the number of red-team hardware upgrades."""
        return self._red.gpu_upgrades

    @gpu_upgrades.setter
    def gpu_upgrades(self, value: int) -> None:
        self._red.gpu_upgrades = value

    @property
    def monitoring(self) -> bool:
        """Return whether blue-team monitoring is enabled."""
        return self._blue.monitoring

    @monitoring.setter
    def monitoring(self, value: bool) -> None:
        self._blue.monitoring = value

    @property
    def rate_limited(self) -> bool:
        """Return whether rate limiting is enabled."""
        return self._blue.rate_limited

    @rate_limited.setter
    def rate_limited(self, value: bool) -> None:
        self._blue.rate_limited = value

    @property
    def policy_enforced(self) -> bool:
        """Return whether the password policy has been applied."""
        return self._blue.policy_enforced

    @policy_enforced.setter
    def policy_enforced(self, value: bool) -> None:
        self._blue.policy_enforced = value

    @property
    def rotation_done(self) -> bool:
        """Return whether a credential rotation has been applied."""
        return self._blue.rotation_done

    @rotation_done.setter
    def rotation_done(self, value: bool) -> None:
        self._blue.rotation_done = value

    @property
    def attempts(self) -> int:
        """Return the current attack attempt counter."""
        return self._attack.attempts

    @attempts.setter
    def attempts(self, value: int) -> None:
        self._attack.attempts = value

    @property
    def attack_active(self) -> bool:
        """Return whether a cracking job is active."""
        return self._attack.attack_active

    @attack_active.setter
    def attack_active(self, value: bool) -> None:
        self._attack.attack_active = value

    @property
    def attack_mode(self) -> str | None:
        """Return the candidate-generation mode of the active attack."""
        return self._attack.attack_mode

    @attack_mode.setter
    def attack_mode(self, value: str | None) -> None:
        self._attack.attack_mode = value

    @property
    def alert_fired(self) -> bool:
        """Return whether the current attack has already triggered an alert."""
        return self._attack.alert_fired

    @alert_fired.setter
    def alert_fired(self, value: bool) -> None:
        self._attack.alert_fired = value

    # Targets

    def target_for(self, user: str) -> Target | None:
        """Return the target for *user*, if it exists."""
        with self.lock:
            for t in self.targets:
                if t.user == user:
                    return t
        return None

    def unlocked_targets(self) -> list[Target]:
        """Return targets that can still be attacked."""
        with self.lock:
            return [t for t in self.targets if not t.locked and not t.recovered]

    def recover(self, user: str) -> Target | None:
        """Mark *user* as recovered. Returns the target, or None if already so."""
        with self.lock:
            t = self.target_for(user)
            if t is None or t.recovered:
                return None
            t.recovered = True
            t.recovered_at = time.time()
            self.attempts = 0  # fresh hashes reset the detection counter
            return t

    # Round Clock

    def start_round(self) -> None:
        """Start the round clock and clear any paused or over state."""
        with self.lock:
            self.round_started = time.time()
            self.round_paused = False
            self.paused_remaining = None
            self.round_over = False

    def pause_round(self) -> None:
        """Pause the round clock while preserving its remaining duration."""
        with self.lock:
            if self.round_started and not self.round_paused:
                self.paused_remaining = self._remaining_locked()
                self.round_paused = True

    def resume_round(self) -> None:
        """Resume a paused round clock from its saved remaining duration."""
        with self.lock:
            if self.round_paused and self.paused_remaining is not None:
                self.round_started = time.time()
                self.paused_remaining = None
                self.round_paused = False

    def end_round(self) -> None:
        """Mark the current round as finished."""
        with self.lock:
            self.round_over = True

    def _remaining_locked(self) -> float:
        if self.round_started is None:
            return float(self.time_budget)
        return max(0.0, self.time_budget - (time.time() - self.round_started))

    def time_remaining(self) -> float:
        """Seconds left in the round (honours pause and over state)."""
        with self.lock:
            if self.round_over:
                return 0.0
            if self.round_started is None:
                return float(self.time_budget)
            if self.round_paused:
                return self.paused_remaining or 0.0
            return max(0.0, self.time_budget - (time.time() - self.round_started))

    # Blue Team Actions

    def lock_account(self, user: str) -> bool:
        """Lock an unrecovered target and report whether it was changed."""
        with self.lock:
            t = self.target_for(user)
            if t is None or t.recovered:
                return False
            t.locked = True
            return True

    def unlock_account(self, user: str) -> bool:
        """Unlock a target and report whether it exists."""
        with self.lock:
            t = self.target_for(user)
            if t is None:
                return False
            t.locked = False
            return True

    def apply_rate_limit(self) -> None:
        """Enable the blue team's rate-limit mitigation."""
        with self.lock:
            self.rate_limited = True

    def apply_policy(self) -> None:
        """Enforce a strong-password policy.

        Every remaining target whose plaintext violates the policy gets
        rotated to bcrypt immediately; policy-compliant ones stay put.
        """
        with self.lock:
            self.policy_enforced = True
            for t in self.targets:
                if t.recovered or t.locked:
                    continue
                if not _is_weak(t.plaintext):
                    continue
                t.algo = "bcrypt"
                t.digest = hashes.bcrypt_hash(t.plaintext, rounds=10)
            self.rotation_done = True

    def rotate_all(self) -> None:
        """Rotate every remaining target: account reset to a new secret.

        Each un-recovered target gets a brand-new random plaintext wrapped in
        bcrypt, so the old password stops working and red team must start
        over from scratch on a secret they cannot know.
        """
        with self.lock:
            self.rotation_done = True
            for t in self.targets:
                if t.recovered:
                    continue
                t.algo = "bcrypt"
                t.plaintext = secrets.token_hex(8)
                t.digest = hashes.bcrypt_hash(t.plaintext, rounds=10)

    def reset_telemetry(self) -> None:
        """Clear the attack telemetry used by the detection rules."""
        with self.lock:
            self.attempts = 0
            self.attack_active = False
            self.attack_mode = None
            self.alert_fired = False

# ---------- FUNCTIONS
def _is_weak(plaintext: str) -> bool:
    """A lazy stand-in for a real password policy checker.

    A password is *weak* if it is shorter than 12 chars, lacks an uppercase
    letter, lacks a digit, or is a known leak (in the bundled wordlist).
    """
    if len(plaintext) < 12:
        return True
    if not any(c.isupper() for c in plaintext):
        return True
    if not any(c.isdigit() for c in plaintext):
        return True
    return False


# Loading
def load_scenario(path: str | Path) -> GameState:
    """Load a scenario JSON file into a fresh :class:`GameState`."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    targets = [
        Target(
            user=entry["user"],
            algo=hashes.canonical_algo(entry["algo"]),
            digest=entry["digest"],
            plaintext=entry["plaintext"],
        )
        for entry in raw["hashes"]
    ]
    return GameState(
        name=raw.get("name", "Untitled scenario"),
        description=raw.get("description", ""),
        time_budget=int(raw.get("time_budget", 300)),
        targets=targets,
    )

# Scenario Validation
def validate_scenario(path: str | Path) -> list[str]:
    """Verify every entry in *path* hashes correctly (used by tests/CI)."""
    problems: list[str] = []
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    for entry in raw["hashes"]:
        try:
            algo = hashes.canonical_algo(entry["algo"])
        except KeyError:
            problems.append(f"{entry['user']}: unknown algo {entry['algo']}")
            continue
        if not hashes.verify_digest(algo, entry["plaintext"], entry["digest"]):
            problems.append(f"{entry['user']}: digest does not match plaintext")
    return problems
