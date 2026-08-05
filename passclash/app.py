"""
File: app.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Streamlit application entry point for PassClash password cracking simulation.

Description:
    This module provides the main Streamlit application entry point for PassClash.
    It supports multiple roles (Red Team, Blue Team, Game Master) through a single
    web interface, enabling real-time password cracking simulation with detection
    and mitigation capabilities. The application can be run directly via Streamlit
    or as a console command after installation.

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from __future__ import annotations

import argparse
import sys

import streamlit as st
from streamlit.web import cli as stcli

from passclash.scoring import blue_score, red_score
from passclash.state import get_state
from passclash.ui import blueteam, common, gm, redteam

# ---------- CONSTANTS
ROLE_TAG = {"Red Team": "🔴", "Blue Team": "🔵", "Game Master": "🎮"}

# ---------- FUNCTIONS
def _sidebar(state) -> str:
    """Render the shared sidebar and return the selected team role."""
    role = common.role_selector()
    st.sidebar.divider()
    st.sidebar.caption(f"Scenario: **{state.name}**")
    st.sidebar.caption(state.description)
    st.sidebar.divider()

    m1, m2 = st.sidebar.columns(2)
    m1.metric("Red", f"{red_score(state)['points']:.0f}")
    m2.metric("Blue", f"{blue_score(state)['points']:.0f}")

    st.sidebar.caption(
        "PassClash, educational red/blue simulation. "
        "Only ever run this against hashes you own."
    )
    return role


def _scenario_arg() -> str | None:
    """Read ``--scenario PATH`` from the script args Streamlit passes after ``--``."""
    if "--scenario" in sys.argv:
        idx = sys.argv.index("--scenario")
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    return None


def main() -> None:
    """Configure and render the Streamlit application for the selected role."""
    st.set_page_config(
        page_title="PassClash",
        page_icon="⚔️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    common.inject_css()

    state = get_state(_scenario_arg())
    role = _sidebar(state)

    st.title(f"{ROLE_TAG[role]} {role} · PassClash")
    st.caption("Password cracking simulation · red vs blue")

    if role == "Red Team":
        redteam.render(state)
    elif role == "Blue Team":
        blueteam.render(state)
    else:
        gm.render(state)


def cli() -> None:
    """Console-script entry point: ``passclash [--port N] [--scenario PATH]``."""
    parser = argparse.ArgumentParser(
        description="PassClash, password cracking simulation"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="path to a scenario JSON file (see scenarios/)",
    )
    parser.add_argument(
        "--port", type=int, default=8501, help="Streamlit port (default: 8501)"
    )
    args = parser.parse_args()

    sys.argv = ["streamlit", "run", __file__]
    if args.port != 8501:
        sys.argv += ["--server.port", str(args.port)]
    if args.scenario:
        sys.argv += ["--", "--scenario", args.scenario]
    sys.exit(stcli.main())


# ---------- MAIN
if __name__ == "__main__":
    main()
