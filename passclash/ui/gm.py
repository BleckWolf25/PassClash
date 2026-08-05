"""
File: gm.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Game Master interface for round control, scoring, and scenario management.

Description:
    This module implements the Game Master interface, providing comprehensive controls
    for managing the PassClash simulation round. Features include round clock management
    (start, pause, end), scenario reset, scoreboard display with red/blue team breakdowns,
    story injection capabilities for simulating credential leaks, and full event log access.
    The GM interface serves as the central control point for the simulation.

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from __future__ import annotations

import pandas as pd
import streamlit as st

from ..events import emit, recent
from ..scoring import round_summary
from ..state import reset_state
from .common import banner, render_events, targets_row


# ---------- FUNCTIONS
def render(state) -> None:
    """Render game-master controls, the scoreboard, and the event history."""
    banner("🎮 GAME MASTER &nbsp;·&nbsp; scenario control")
    targets_row(state)

    col_ctrl, col_scores = st.columns([1, 2], gap="large")

    with col_ctrl:
        st.subheader("Round clock")
        m1, m2 = st.columns(2)
        m1.metric("Time remaining", _fmt_clock(state.time_remaining()))
        m2.metric("Round state", "paused" if state.round_paused else (
            "running" if state.round_started else "not started"))

        c1, c2, c3 = st.columns(3)
        if c1.button("▶ Start", disabled=bool(state.round_started),
                     use_container_width=True):
            state.start_round()
            emit("gm", f"Round started, {state.time_budget}s on the clock",
                 team="both")
            st.rerun()
        if c2.button("⏸ Pause", disabled=not state.round_started or state.round_over,
                     use_container_width=True):
            state.pause_round()
            emit("gm", "Clock paused", team="both")
            st.rerun()
        if c3.button("⏹ End", disabled=not state.round_started,
                     use_container_width=True):
            state.end_round()
            emit("gm", "Round ended", team="both")
            st.rerun()

        if st.button("🔄 New round (reset)", use_container_width=True):
            reset_state()
            st.session_state.pop("job", None)
            st.session_state.pop("blue_history", None)
            emit("gm", "New round loaded", team="both")
            st.rerun()

        _story_injection(state)

    with col_scores:
        st.subheader("Scoreboard")
        summary = round_summary(state)
        _scoreboard(summary)

        st.divider()
        if state.round_over or all(t.recovered for t in state.targets):
            st.subheader("Final verdict")
            _final_table(summary)
        else:
            st.caption("Final table unlocks when the round ends.")

        st.divider()
        st.subheader("Full event log")
        render_events(recent("gm", limit=80))


def _fmt_clock(seconds: float) -> str:
    """Format a duration as a two-part minutes-and-seconds clock."""
    seconds = int(max(0, seconds))
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"


def _scoreboard(summary: dict) -> None:
    """Render the red and blue score totals and their breakdown."""
    red, blue = summary["red"], summary["blue"]
    c1, c2 = st.columns(2)
    c1.metric("🔴 RED", f"{red['points']:.0f} pts")
    c2.metric("🔵 BLUE", f"{blue['points']:.0f} pts")

    with st.expander("Score breakdown"):
        st.markdown(
            f"- **Red**: cracks `{red['crack_points']}` · alerts −`{red['alert_penalty']}` "
            f"· speed bonus `+{red['speed_bonus']}`"
        )
        st.markdown(
            f"- **Blue**: detection `{blue['detection']}` · locked `{blue['locked_points']}` "
            f"· rotation `{blue['rotation_points']}` · residual `{blue['residual']}`"
        )
        st.caption(
            "Residual = hashes still standing at round end. Blue wins the "
            "accounts that never fall."
        )


def _final_table(summary: dict) -> None:
    """Render the final account verdict table and winning team."""
    rows = []
    for r in summary["rows"]:
        rows.append(
            {
                "user": r["user"],
                "algo": r["algo"],
                "plaintext": r["plaintext"] or "—",
                "verdict": r["verdict"],
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    red, blue = summary["red"], summary["blue"]
    if blue["points"] > red["points"]:
        winner = "🟦 BLUE TEAM"
    elif red["points"] > blue["points"]:
        winner = "🟥 RED TEAM"
    else:
        winner = "🤝 DRAW"
    st.success(f"**Winner: {winner}**")


def _story_injection(state) -> None:
    """Render the game master's password-leak story event controls."""
    st.divider()
    st.subheader("Story injections")
    st.caption(
        "Leaking a password simulates a credential dump hitting the news, "
        "it counts as a red-team breach."
    )
    standing = [target for target in state.targets if not target.recovered]
    if not standing:
        st.caption("Nothing left to leak.")
        return
    victim = st.selectbox("Leak", [target.user for target in standing])
    if st.button("📢 Leak password", use_container_width=True):
        target = state.target_for(victim)
        state.recover(victim)
        emit(
            "gm",
            f"BREAKING: {victim}'s password leaked: {target.plaintext}",
            team="both",
        )
        st.rerun()
