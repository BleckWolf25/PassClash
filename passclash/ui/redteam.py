"""
File: redteam.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Red Team interface for attack configuration, execution, and recovered credential display.

Description:
    This module implements the Red Team interface, providing hashcat-style attack configuration
    with multiple modes (dictionary, mask, hybrid, rules), wordlist selection, target specification,
    and hardware upgrades. The interface displays live cracking progress with terminal-style status
    output, shows recovered credentials in real-time, and provides event feeds for attack activities.
    Red team can upgrade GPU hardware to increase cracking speed.

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from __future__ import annotations

from pathlib import Path

import streamlit as st

from ..engine import CrackingJob
from ..events import emit
from ..state import DEFAULT_WORDLIST
from ..terminal import status_block
from .common import banner, render_events, targets_row, visible_events

# ---------- CONSTANTS
MODES = {
    "dictionary": "Dictionary attack",
    "mask": "Mask attack (brute force)",
    "hybrid": "Hybrid: wordlist + mask",
    "rules": "Rule-based mangling",
}

RULES = {
    "append_digits_2": "append 2 digits (00-99)",
    "append_digits_4": "append 4 digits (0000-9999)",
    "append_years": "append year (1990-2026)",
    "leet": "leet substitution",
    "capitalize": "capitalize / UPPER",
}

# ---------- FUNCTIONS
def _wordlists() -> list[Path]:
    base = DEFAULT_WORDLIST.parent
    return sorted(base.glob("*.txt"))


def _job() -> CrackingJob | None:
    return st.session_state.get("job")


def render(state) -> None:
    """Render attack controls, live status, and recovered credentials."""
    banner("⚔ RED TEAM &nbsp;·&nbsp; hashcat CLI simulation")
    targets_row(state)

    col_cfg, col_term = st.columns([1, 2], gap="large")

    with col_cfg:
        st.subheader("Attack setup")
        standing = [t for t in state.targets if not t.recovered]
        target_names = [t.user for t in standing]
        if not target_names:
            st.info("No hashes left to attack.")
            return
        selected = st.multiselect(
            "Target hashes",
            target_names,
            default=target_names,
            help="Attack a subset of the dump, empty means every remaining "
                 "hash. Throughput is gated by the slowest selected algorithm.",
        )
        st.caption(
            " ".join(
                f"<span class='c-dim'>{t.user}:</span> "
                f"<span class='c-cyan'>{t.algo}</span>"
                for t in standing if t.user in (selected or target_names)
            ),
            unsafe_allow_html=True,
        )
        mode = st.selectbox("Mode", list(MODES), format_func=MODES.get)
        wordlist = st.selectbox(
            "Wordlist",
            [p.name for p in _wordlists()],
            help="Stored under wordlists/, add your own .txt files",
        )
        mask = st.text_input("Mask", "?l?l?l?l?l", help="?l ?u ?d ?s ?a + literals")
        rule = st.selectbox("Rule", list(RULES), format_func=RULES.get)

        job = _job()
        running = bool(job and job.status == "running")
        if st.button("▶ Launch attack", disabled=running, use_container_width=True):
            job = CrackingJob(
                state=state,
                mode=mode,
                wordlist_path=str(DEFAULT_WORDLIST.parent / wordlist),
                mask=mask.strip() or "?l?l?l?l?l",
                rule=rule,
                target_users=list(selected),
            )
            st.session_state["job"] = job
            job.start()
            st.rerun()

        if st.button("■ Stop attack", disabled=not running, use_container_width=True):
            job.stop()
            st.rerun()

        st.divider()
        st.subheader("Hardware")
        st.caption(
            f"GPU farm: {state.gpu_upgrades}/2 upgrades applied "
            f"(×{int(2 ** state.gpu_upgrades)})"
        )
        if st.button(
            "⬆ Upgrade speed (×2)",
            disabled=state.gpu_upgrades >= 2 or running,
            use_container_width=True,
        ):
            with state.lock:
                state.speed_multiplier *= 2
                state.gpu_upgrades += 1
            emit("red", f"Red upgraded hardware (×{int(state.speed_multiplier)})",
                 team="red")
            st.rerun()

        _render_recovered_hashes(state, job)

    with col_term:
        st.subheader("Live status")
        if job is None:
            st.info("Configure an attack on the left and hit **Launch attack**.")
        else:
            _render_live(state, job)
            st.divider()
            st.subheader("Event feed")
            render_events(visible_events(state, "Red Team", limit=25))


@st.fragment(run_every=1.0)
def _render_live(state, job) -> None:
    """Render live job status and a progress bar."""
    st.markdown(status_block(job, state), unsafe_allow_html=True)
    st.progress(
        (job.attempts / job.candidates()) if job.candidates() else 0.0,
        text="candidate space explored",
    )
    if job.status == "cracked":
        st.success("ALL HASHES RECOVERED, round finished")
    elif job.status == "exhausted":
        st.warning("Candidate space exhausted. Try another mode.")
    elif job.status == "stopped":
        st.warning("Attack stopped by operator.")
    elif job.status == "over":
        st.warning("Round clock expired.")


def _render_recovered_hashes(state, job: CrackingJob | None) -> None:
    """Render credentials recovered by the current job, if one exists."""
    st.divider()
    st.subheader("Cracked hashes")
    if job:
        for user in job.recovered_users:
            target = state.target_for(user)
            if target:
                st.markdown(
                    f"<pre class='hc'><span class='c-ok'>{user}:{target.plaintext}</span>"
                    f" <span class='c-dim'>[{target.algo}]</span></pre>",
                    unsafe_allow_html=True,
                )
    else:
        st.caption("Nothing recovered yet.")
