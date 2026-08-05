"""
File: test_engine.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Unit tests for the password cracking engine against test scenarios.

Description:
    This module contains comprehensive tests for the CrackingJob engine, validating
    dictionary attacks, target selection, error handling, speed gating by algorithm,
    blue-team mitigations (lockouts, rate limiting, rotations), and round clock
    enforcement. Tests use small in-memory scenarios for fast execution and verify
    both successful cracking paths and edge cases like missing files and stop commands.

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
import time
from pathlib import Path

from conftest import make_state

from passclash.engine import CrackingJob

# ---------- FIXTURES
def _wordlist(tmp_path: Path, words: list[str]) -> Path:
    p = tmp_path / "wl.txt"
    p.write_text("\n".join(words) + "\n", encoding="utf-8")
    return p


def _wait(job: CrackingJob, timeout: float = 20.0) -> None:
    end = time.time() + timeout
    while time.time() < end and job.status in ("idle", "running"):
        time.sleep(0.02)
    assert job.status not in ("idle", "running"), "job did not finish in time"


def test_dictionary_cracks_all(tmp_path):
    """A dictionary job recovers every selected matching target."""
    st = make_state(("alice", "md5", "letmein"), ("bob", "md5", "princess"))
    wl = _wordlist(tmp_path, ["wrong", "letmein", "princess"])
    job = CrackingJob(state=st, mode="dictionary", wordlist_path=str(wl))
    job.start()
    _wait(job)
    assert job.status == "cracked"
    assert sorted(job.recovered_users) == ["alice", "bob"]
    assert st.target_for("alice").recovered
    assert st.target_for("bob").recovered


def test_target_users_limits_the_job(tmp_path):
    """A target selection limits a job to the requested account."""
    st = make_state(("alice", "md5", "letmein"), ("bob", "md5", "princess"))
    wl = _wordlist(tmp_path, ["letmein", "princess"])
    job = CrackingJob(
        state=st, mode="dictionary", wordlist_path=str(wl), target_users=["alice"]
    )
    job.start()
    _wait(job)
    assert job.status == "cracked"
    assert st.target_for("alice").recovered
    assert not st.target_for("bob").recovered


def test_missing_wordlist_ends_exhausted(tmp_path):
    """A missing wordlist ends a dictionary job cleanly as exhausted."""
    st = make_state(("alice", "md5", "letmein"))
    job = CrackingJob(
        state=st,
        mode="dictionary",
        wordlist_path=str(tmp_path / "does-not-exist.txt"),
    )
    job.start()
    _wait(job)
    assert job.status == "exhausted"


def test_stop_sets_status(tmp_path):
    """Stopping an active job records the stopped status."""
    # bcrypt keeps the job running ~80 ms per candidate, so it is still
    # mid-flight (not already exhausted) when we stop it.
    st = make_state(("alice", "bcrypt", "letmein"))
    wl = _wordlist(tmp_path, ["x"] * 20000)
    job = CrackingJob(state=st, mode="dictionary", wordlist_path=str(wl))
    job.start()
    time.sleep(0.05)
    job.stop()
    _wait(job)
    assert job.status == "stopped"
    assert not st.target_for("alice").recovered


def test_bcrypt_target_gates_device_speed(tmp_path):
    """The slowest selected hash algorithm caps session throughput."""
    st = make_state(("fast", "md5", "letmein"), ("slow", "bcrypt", "hunter2"))
    wl = _wordlist(tmp_path, ["hunter2", "letmein"])
    job = CrackingJob(state=st, mode="dictionary", wordlist_path=str(wl))
    job.start()
    assert job.effective_speed() <= 12
    _wait(job)
    assert job.status == "cracked"
    assert sorted(job.recovered_users) == ["fast", "slow"]


def test_locked_account_is_skipped(tmp_path):
    """Locked targets are never recovered by a running job."""
    st = make_state(("alice", "md5", "letmein"))
    st.lock_account("alice")
    wl = _wordlist(tmp_path, ["letmein"])
    job = CrackingJob(state=st, mode="dictionary", wordlist_path=str(wl))
    job.start()
    _wait(job)
    assert job.status == "exhausted"
    assert not st.target_for("alice").recovered


def test_rate_limit_halves_effective_speed(tmp_path):
    """Rate limiting halves the effective speed cap."""
    st = make_state(("alice", "md5", "letmein"))
    st.speed_multiplier = 4.0
    st.apply_rate_limit()
    wl = _wordlist(tmp_path, ["letmein"])
    job = CrackingJob(state=st, mode="dictionary", wordlist_path=str(wl))
    assert job.effective_speed() == 4_000_000


def test_rotation_bites_mid_run(tmp_path):
    """Rotating credentials invalidates candidates already queued by a job."""
    # bcrypt verification takes ~80 ms per candidate, so with a 20 ms head
    # start the job is still mid-flight when blue rotates every account --
    # alice gets a brand-new secret and the old plaintext dies.
    st = make_state(("alice", "bcrypt", "letmein"))
    wl = _wordlist(tmp_path, ["wrong", "letmein"])
    job = CrackingJob(state=st, mode="dictionary", wordlist_path=str(wl))
    job.start()
    time.sleep(0.02)
    st.rotate_all()  # alice now has a fresh secret; "letmein" no longer matches
    _wait(job)
    assert job.status == "exhausted"
    assert not st.target_for("alice").recovered
    assert st.target_for("alice").plaintext != "letmein"


def test_round_clock_expiry_stops_job(tmp_path):
    """An expired round clock ends the job before it can recover a target."""
    st = make_state(("alice", "md5", "letmein"))
    st.start_round()
    st.round_started -= 1000  # clock already expired
    wl = _wordlist(tmp_path, ["letmein"])
    job = CrackingJob(state=st, mode="dictionary", wordlist_path=str(wl))
    job.start()
    _wait(job)
    assert job.status == "over"
    assert not st.target_for("alice").recovered


def test_mask_mode_counts_and_cracks():
    """Mask mode counts and recovers a matching generated candidate."""
    st = make_state(("alice", "md5", "abc"))
    job = CrackingJob(state=st, mode="mask", mask="?l?l?l")
    assert job.candidates() == 26**3
    job.start()
    _wait(job, timeout=60)
    assert job.status == "cracked"
