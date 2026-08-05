"""
File: blueteam.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Blue Team interface for SOC dashboard, attack detection, and mitigation controls.

Description:
    This module implements the Blue Team user interface, providing a Security Operations
    Center dashboard with attack detection rules, monitoring capabilities, and defensive
    mitigations. Blue team can deploy sensors, lock accounts, apply rate limiting, enforce
    password policies, and perform credential rotations. The interface displays real-time
    attack telemetry and event feeds when monitoring is enabled.

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from __future__ import annotations

import streamlit as st

from ..events import emit, recent
from ..scoring import check_detection
from .common import banner, render_events, targets_row, visible_events


# ---------- FUNCTIONS
def render(state) -> None:
    """Render the blue-team SOC dashboard."""
    banner("🛡 BLUE TEAM &nbsp;·&nbsp; SOC dashboard")
    _render_soc(state)


@st.fragment(run_every=1.0)
def _render_soc(state) -> None:
    # Detection rules are evaluated on every (auto-)render of the dashboard.
    targets_row(state)
    fired = check_detection(state)

    col_metrics, col_soc = st.columns([1, 2], gap="large")

    with col_metrics:
        st.subheader("Sensor status")
        monitoring = st.toggle(
            "Deploy detection rules",
            value=state.monitoring,
            help="Once deployed, brute-force activity is logged and alerts fire.",
        )
        if monitoring != state.monitoring:
            state.monitoring = monitoring
            emit(
                "mitigate",
                "Detection rules deployed" if monitoring else "Detection rules disabled",
                team="blue",
            )
            st.rerun()

        if not state.monitoring:
            st.warning(
                "No sensors deployed, you are blind to the attacker's activity."
            )
        elif fired:
            st.error("🚨 ALERT: brute-force attack detected!")

        m1, m2, m3 = st.columns(3)
        m1.metric("Live attempts", f"{state.attempts:,}")
        m2.metric("Alerts", str(_alert_count()))
        m3.metric("Accounts locked", str(sum(1 for t in state.targets if t.locked)))

        st.divider()
        st.subheader("Mitigations")
        _mitigations(state)

    with col_soc:
        st.subheader("Attack telemetry")
        if not state.monitoring:
            st.caption("Activity appears here once detection rules are deployed.")
        else:
            _telemetry(state)

        st.divider()
        st.subheader("Event feed")
        render_events(visible_events(state, "Blue Team", limit=30))


def _alert_count() -> int:
    """Return the total number of alerts emitted in the current event history."""
    return len([e for e in recent("gm", limit=500) if e["kind"] == "alert"])


def _mitigations(state) -> None:
    locked = [t.user for t in state.targets if t.locked and not t.recovered]
    unlocked = [t.user for t in state.targets if not t.locked and not t.recovered]

    if unlocked:
        victim = st.selectbox(
            "Lock account",
            unlocked,
            help="Locked accounts are skipped by the attacker.",
        )
        if st.button("🔒 Lock account", use_container_width=True):
            if state.lock_account(victim):
                emit("mitigate", f"Account locked: {victim}", team="blue")
                st.rerun()

    if locked:
        if st.button("🔓 Unlock account", use_container_width=True):
            for user in locked[:1]:
                state.unlock_account(user)
                emit("mitigate", f"Account unlocked: {user}", team="blue")
            st.rerun()

    st.caption(
        "Rate limiting halves the attacker's effective speed. "
        "Enforcing policy rotates every weak remaining hash to bcrypt "
        "(genuinely ~100,000× slower)."
    )
    if st.button("🐢 Apply rate limiting", disabled=state.rate_limited,
                 use_container_width=True):
        state.apply_rate_limit()
        emit("mitigate", "Rate limiting applied (attacker speed halved)", team="blue")
        st.rerun()

    if st.button("📋 Enforce password policy", disabled=state.policy_enforced,
                 use_container_width=True):
        state.apply_policy()
        weak = sum(
            1 for t in state.targets
            if t.algo == "bcrypt" and not t.recovered and not t.locked
        )
        emit(
            "mitigate",
            f"Policy enforced, {weak} weak hash(es) rotated to bcrypt",
            team="blue",
        )
        st.rerun()

    if st.button("🔄 Rotate ALL remaining hashes", disabled=state.rotation_done,
                 use_container_width=True):
        state.rotate_all()
        emit("mitigate", "Full credential rotation, all hashes now bcrypt", team="blue")
        st.rerun()


def _telemetry(state) -> None:
    hist = st.session_state.setdefault("blue_history", [])
    if state.attempts and (not hist or hist[-1] != state.attempts):
        hist.append(state.attempts)
        del hist[:-300]

    st.line_chart(
        {"attempts": hist},
        height=180,
        use_container_width=True,
    )

    if state.attack_active:
        st.info(f"Attacker is running a **{state.attack_mode}** attack.")
    else:
        st.caption("No attack currently in progress.")
