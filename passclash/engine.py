"""
File: engine.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Password cracking engine with background thread processing and multiple attack modes.

Description:
    This module implements the core password cracking engine for PassClash. The CrackingJob
    class runs background threads that walk through candidate spaces (wordlists, masks,
    hybrid attacks, rule-based mangling) and verify candidates against selected hash sets.
    The engine supports hashcat-style attack modes and reads live game state for real-time
    blue-team mitigation effects. Throughput is gated by the slowest selected algorithm,
    mimicking real hashcat behavior.

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from __future__ import annotations

import itertools
import threading
import time
from dataclasses import dataclass, field

from . import hashes
from .events import emit
from .scenario import GameState

# ---------- CONSTANTS
CHARSETS = {
    "?l": "abcdefghijklmnopqrstuvwxyz",
    "?u": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "?d": "0123456789",
    "?s": "!@#$%^&*()-_=+[]{};:,.<>?",
    "?a": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
          "!@#$%^&*()-_=+[]{};:,.<>?",
}

_RULES = {
    "append_digits_2": lambda w: [f"{w}{i:02d}" for i in range(100)],
    "append_digits_4": lambda w: [f"{w}{i:04d}" for i in range(10000)],
    "append_years": lambda w: [f"{w}{y}" for y in range(1990, 2027)],
    "leet": lambda w: [
        w.replace("a", "@").replace("e", "3").replace("i", "1")
         .replace("o", "0").replace("s", "$"),
        w.replace("a", "4").replace("e", "3").replace("i", "1")
         .replace("o", "0").replace("s", "5"),
    ],
    "capitalize": lambda w: [w.capitalize(), w.upper()],
}

# ---------- DATACLASSES
@dataclass
class JobConfiguration:
    """Inputs that define a cracking session and remain stable while it runs."""

    state: GameState
    mode: str = "dictionary"
    wordlist_path: str = ""
    mask: str = "?l?l?l?l?l"
    rule: str = "append_digits_2"
    target_users: list[str] = field(default_factory=list)  # empty = all


@dataclass
class SessionTelemetry:
    """Session lifecycle and progress measurements."""

    status: str = "idle"
    attempts: int = 0
    candidates_total: int | None = None
    started_at: float | None = None
    finished_at: float | None = None


@dataclass
class RecoveryTelemetry:
    """Recovered credentials and terminal output for a session."""

    recovered_users: list[str] = field(default_factory=list)
    session_name: str = "passclash"
    log: list[str] = field(default_factory=list)


@dataclass
class JobTelemetry:
    """Mutable status and measurements produced by a cracking session."""

    session: SessionTelemetry = field(default_factory=SessionTelemetry)
    recovery: RecoveryTelemetry = field(default_factory=RecoveryTelemetry)


# ---------- MAIN CLASS
class CrackingJob:
    """A background cracking session against one or more scenario targets."""

    _CONFIGURATION_FIELDS = frozenset(
        {"state", "mode", "wordlist_path", "mask", "rule", "target_users"}
    )
    _SESSION_FIELDS = frozenset(
        {"status", "attempts", "candidates_total", "started_at", "finished_at"}
    )
    _RECOVERY_FIELDS = frozenset({"recovered_users", "session_name", "log"})

    def __init__(
        self,
        state: GameState,
        mode: str = "dictionary",
        wordlist_path: str = "",
        mask: str = "?l?l?l?l?l",
        rule: str = "append_digits_2",
        target_users: list[str] | None = None,
    ) -> None:
        """Create a job from stable configuration and isolated telemetry."""
        self._configuration = JobConfiguration(
            state, mode, wordlist_path, mask, rule, target_users or []
        )
        self._telemetry = JobTelemetry()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._last_pub = 0.0
        self.status = "idle"
        self.attempts = 0
        self.candidates_total = None
        self.started_at = None
        self.finished_at = None

    def __getattr__(self, name: str):
        """Expose configuration and telemetry fields through the job API."""
        if name in self._CONFIGURATION_FIELDS:
            return getattr(self._configuration, name)
        if name in self._SESSION_FIELDS:
            return getattr(self._telemetry.session, name)
        if name in self._RECOVERY_FIELDS:
            return getattr(self._telemetry.recovery, name)
        raise AttributeError(name)

    def __setattr__(self, name: str, value) -> None:
        """Route mutable telemetry updates to their owned data object."""
        if name in self._SESSION_FIELDS:
            setattr(self._telemetry.session, name, value)
        elif name in self._RECOVERY_FIELDS:
            setattr(self._telemetry.recovery, name, value)
        else:
            object.__setattr__(self, name, value)

    # Lifecycle methods

    def start(self) -> None:
        """Start the candidate-processing thread unless it is already running."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self.status = "running"
        self.started_at = time.time()
        self.candidates_total = self.candidates()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        with self.state.lock:
            self.state.attack_active = True
            self.state.attack_mode = self.mode
        emit("attack", f"Attack started: {self.mode} mode "
                       f"({len(self._selected())} hash(es))",
             team="both", mode=self.mode)

    def stop(self) -> None:
        """Request that the running candidate-processing thread stops."""
        self._stop.set()

    def candidates(self) -> int | None:
        """Total size of the candidate space (for progress bars)."""
        if self.mode == "dictionary":
            return self._count_lines()
        if self.mode == "mask":
            return self._mask_size(self.mask)
        if self.mode == "hybrid":
            n = self._count_lines()
            return None if n is None else n * self._mask_size("?d?d?d")
        if self.mode == "rules":
            n = self._count_lines()
            if n is None:
                return None
            variants = {
                "append_digits_2": 100,
                "append_digits_4": 10000,
                "append_years": 37,
                "leet": 2,
                "capitalize": 2,
            }
            return n * variants[self.rule]
        return None

    # Internals

    def _run(self) -> None:
        try:
            for candidate in self._iterate():
                if self._stop.is_set():
                    self.status = "stopped"
                    break
                if self.state.round_over:
                    self.status = "over"
                    break
                if self.state.time_remaining() <= 0:
                    self.state.end_round()
                    self.status = "over"
                    break
                self._check(candidate)
                if self._selected_done():
                    self.status = "cracked"
                    break
            else:
                if self.status == "running":
                    self.status = "exhausted"
        except (KeyError, OSError, UnicodeError, ValueError):
            # Candidate space collapsed (e.g. missing wordlist) -- the job
            # cannot continue; treat it like exhaustion.
            if self.status == "running":
                self.status = "exhausted"
        finally:
            self.finished_at = time.time()
            with self.state.lock:
                self.state.attack_active = False
            if self.status == "cracked":
                emit("round", "All selected hashes recovered!", team="both")

    def _check(self, candidate: str) -> None:
        if self.state.time_remaining() <= 0:
            return

        cracked_now: list[tuple[str, str, str]] = []
        for t in self._selected():
            if hashes.verify_digest(t.algo, candidate, t.digest):
                self.state.recover(t.user)
                cracked_now.append((t.user, candidate, t.algo))

        speed = self.effective_speed()
        if cracked_now:
            for user, plain, algo in cracked_now:
                self.recovered_users.append(user)
                self.log.append(f"$HEX[{plain.encode('utf-8').hex()}]")
                emit("crack", f"{user}:{plain} ({algo})", team="both",
                     user=user, plaintext=plain, algo=algo)
        else:
            self.attempts += 1
        self._pace(speed)
        self._publish_progress()

    def _pace(self, speed: int) -> None:
        """Respect the (possibly rate-limited) speed cap.

        ``wanted`` is recomputed every iteration so the pacing tracks real
        elapsed time instead of a stale snapshot. A speed of 1 means there is
        nothing left to pace (no remaining unlocked targets) -- any sleeping
        there would hang the job forever.
        """
        if speed <= 1:
            return
        while not self._stop.is_set():
            window = time.time() - (self.started_at or time.time())
            wanted = max(1.0, window * speed)
            if self.attempts < wanted:
                return
            time.sleep(0.005)

    def _publish_progress(self) -> None:
        # Throttle progress events to ~10/s so the event bus stays quiet.
        if time.time() - self._last_pub < 0.1:
            return
        self._last_pub = time.time()
        with self.state.lock:
            self.state.attempts = self.attempts
        emit("progress", f"{self.attempts:,} attempts", team="blue",
             attempts=self.attempts)

    def _selected(self) -> list:
        """Remaining, unlocked targets in this job's selection."""
        with self.state.lock:
            if self.target_users:
                return [t for t in self.state.targets
                        if t.user in self.target_users
                        and not t.recovered and not t.locked]
            return [t for t in self.state.targets
                    if not t.recovered and not t.locked]

    def effective_speed(self) -> int:
        """Device throughput: gated by the slowest selected algorithm."""
        remaining = self._selected()
        if not remaining:
            return 1
        bottleneck = min(
            hashes.crackable_speed(t.algo) for t in remaining
        )
        mult = self.state.speed_multiplier
        if self.state.rate_limited:
            mult *= 0.5
        return max(1, int(bottleneck * mult))

    def _selected_done(self) -> bool:
        with self.state.lock:
            if self.target_users:
                wanted = {t.user for t in self.state.targets
                          if t.user in self.target_users}
                recovered = {t.user for t in self.state.targets
                             if t.recovered and t.user in self.target_users}
                return wanted <= recovered
            return all(t.recovered for t in self.state.targets)

    # Candidate Generators

    def _iterate(self):
        if self.mode == "dictionary":
            yield from self._read_words()
        elif self.mode == "mask":
            yield from self._mask_iter(self.mask)
        elif self.mode == "hybrid":
            yield from (
                f"{word}{suffix}"
                for word in self._read_words()
                for suffix in self._mask_iter("?d?d?d")
            )
        elif self.mode == "rules":
            yield from (
                variant
                for word in self._read_words()
                for variant in _RULES[self.rule](word)
            )
        else:
            raise ValueError(f"unknown mode: {self.mode}")

    def _read_words(self):
        with open(self.wordlist_path, "r", encoding="utf-8", errors="ignore") as fh:
            yield from (line.strip() for line in fh)

    def _mask_iter(self, pattern: str):
        groups = []
        i = 0
        while i < len(pattern):
            if pattern[i] == "?" and i + 1 < len(pattern):
                groups.append(CHARSETS[pattern[i:i + 2]])
                i += 2
            else:
                groups.append(pattern[i])
                i += 1
        for combo in itertools.product(*groups):
            yield "".join(combo)

    def _mask_size(self, pattern: str) -> int:
        size = 1
        i = 0
        while i < len(pattern):
            if pattern[i] == "?" and i + 1 < len(pattern):
                size *= len(CHARSETS[pattern[i:i + 2]])
                i += 2
            else:
                i += 1
        return size

    def _count_lines(self) -> int | None:
        try:
            with open(self.wordlist_path, "rb") as fh:
                return sum(1 for _ in fh)
        except OSError:
            return None

    # Telemetry Properties

    @property
    def elapsed(self) -> float:
        """Return the session duration in seconds."""
        start = self.started_at or time.time()
        end = self.finished_at or time.time()
        return max(0.0, end - start)

    @property
    def rate(self) -> float:
        """Return processed candidates per second for this session."""
        if self.elapsed <= 0:
            return 0.0
        return self.attempts / self.elapsed

    @property
    def eta(self) -> float | None:
        """Estimate seconds until candidate exhaustion, if calculable."""
        total = self.candidates_total
        if not total or self.rate <= 0 or self.attempts >= total:
            return None
        return (total - self.attempts) / self.rate
