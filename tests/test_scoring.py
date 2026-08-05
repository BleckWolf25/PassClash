"""
File: test_scoring.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Unit tests for scoring system and detection logic for both teams.

Description:
    This module tests the competitive scoring system, validating red team points
    (weighted by algorithm, speed bonuses, alert penalties) and blue team points
    (detection, locked accounts, rotations, residual hashes). Tests also verify
    detection logic triggers correctly based on attempt thresholds and monitoring
    status, and that round summaries report accurate verdicts for each target.

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from conftest import make_state

from passclash import scoring
from passclash.events import clear

# ---------- FIXTURES
def test_red_points_are_weighted_by_algo():
    """Red score gives each recovered algorithm its configured weight."""
    clear()
    st = make_state(("a", "md5", "x"), ("b", "sha256", "y"))
    st.recover("a")
    st.recover("b")
    r = scoring.red_score(st, events=[])
    assert r["cracks"] == 2
    assert r["crack_points"] == (1 + 3) * scoring.POINTS_PER_WEIGHT
    assert r["points"] == r["crack_points"]


def test_red_alert_penalty():
    """Each alert deducts the configured penalty from red's score."""
    clear()
    st = make_state(("a", "md5", "x"))
    st.recover("a")
    events = [
        {"kind": "alert", "t": 0, "msg": "x"},
        {"kind": "alert", "t": 0, "msg": "y"},
    ]
    r = scoring.red_score(st, events=events)
    assert r["alerts"] == 2
    assert r["alert_penalty"] == 2 * scoring.ALERT_PENALTY
    assert r["points"] == scoring.POINTS_PER_WEIGHT - r["alert_penalty"]


def test_red_speed_bonus_only_when_fast():
    """No speed bonus is awarded before a round clock has started."""
    st = make_state(("a", "md5", "x"), ("b", "md5", "y"))
    st.recover("a")
    st.recover("b")
    # No round clock started -> no speed bonus (finished_at is meaningless).
    r = scoring.red_score(st, events=[])
    assert r["speed_bonus"] == 0.0


def test_blue_residual_points():
    """Blue gains residual points for hashes that remain standing."""
    clear()
    st = make_state(("a", "md5", "x"), ("b", "sha256", "y"))
    b = scoring.blue_score(st, events=[])
    assert b["hashes_standing"] == 2
    assert b["residual"] == (1 + 3) * scoring.POINTS_PER_WEIGHT


def test_blue_locked_accounts_score():
    """Blue gains points for accounts it has locked."""
    clear()
    st = make_state(("a", "md5", "x"), ("b", "sha256", "y"))
    st.lock_account("a")
    b = scoring.blue_score(st, events=[])
    assert b["locked_points"] == scoring.POINTS_PER_WEIGHT
    assert b["hashes_standing"] == 2


def test_detection_fires_once_above_threshold():
    """Detection triggers once after the attempt threshold is reached."""
    clear()
    st = make_state(("a", "md5", "x"))
    st.monitoring = True
    st.attack_active = True
    st.attempts = scoring.DETECTION_ATTEMPT_THRESHOLD - 1
    assert scoring.check_detection(st) is False
    st.attempts = scoring.DETECTION_ATTEMPT_THRESHOLD
    assert scoring.check_detection(st) is True
    assert scoring.check_detection(st) is False  # alert_fired latches


def test_detection_requires_monitoring_and_attack():
    """Detection requires both monitoring and an active attack."""
    clear()
    st = make_state(("a", "md5", "x"))
    st.attempts = 100_000
    assert scoring.check_detection(st) is False  # no monitoring
    st.monitoring = True
    assert scoring.check_detection(st) is False  # no active attack
    st.attack_active = True
    assert scoring.check_detection(st) is True


def test_round_summary_verdicts():
    """The round summary reports the final verdict for each target."""
    st = make_state(("a", "md5", "x"), ("b", "sha256", "y"))
    st.recover("a")
    st.lock_account("b")
    summary = scoring.round_summary(st)
    by_user = {r["user"]: r for r in summary["rows"]}
    assert by_user["a"]["verdict"] == "cracked"
    assert by_user["a"]["plaintext"] == "x"
    assert by_user["b"]["verdict"] == "locked"
    assert by_user["b"]["plaintext"] == ""
