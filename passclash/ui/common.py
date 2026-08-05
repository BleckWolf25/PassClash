"""
File: common.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Shared UI components and styling utilities for PassClash interfaces.

Description:
    This module provides common UI utilities shared across all PassClash interfaces,
    including CSS styling injection, role selection, event feed rendering, and target
    status displays. The CSS defines the dark theme with color-coded elements for
    different event types and status indicators. Shared components ensure consistent
    visual appearance across Red Team, Blue Team, and Game Master views.

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from __future__ import annotations

import streamlit as st

from ..events import recent
from ..scenario import GameState
from ..terminal import algo_badges

# ---------- STYLING
CSS = """
<style>
:root {
  --pc-bg: #0b0f14;
  --pc-panel: #11161d;
  --pc-border: #1e2a38;
  --pc-ok: #4ade80;
  --pc-warn: #facc15;
  --pc-dim: #64748b;
  --pc-red: #f87171;
  --pc-cyan: #22d3ee;
}
.stApp { background: var(--pc-bg); }
[data-testid="stSidebar"] { background: var(--pc-panel); border-right: 1px solid var(--pc-border); }
h1, h2, h3 { color: var(--pc-cyan) !important; letter-spacing: 1px; }
pre.hc {
  background: #05080c; color: #cbd5e1; border: 1px solid var(--pc-border);
  border-radius: 8px; padding: 14px 16px; font-family: "JetBrains Mono", "Cascadia Code",
  "Fira Code", Consolas, monospace; font-size: 13px; line-height: 1.55; overflow-x: auto;
}
.c-ok   { color: var(--pc-ok); }
.c-warn { color: var(--pc-warn); }
.c-dim  { color: var(--pc-dim); }
.c-red  { color: var(--pc-red); }
.c-cyan { color: var(--pc-cyan); }
div[data-testid="stMetric"] {
  background: var(--pc-panel); border: 1px solid var(--pc-border);
  border-radius: 8px; padding: 10px;
}
.pc-event {
  background: var(--pc-panel); border: 1px solid var(--pc-border); border-radius: 8px;
  padding: 6px 10px; margin: 4px 0; font-family: Consolas, monospace; font-size: 13px;
  color: #cbd5e1;
}
.pc-event .t { color: var(--pc-dim); margin-right: 8px; }
.pc-event.k-crack   { border-left: 3px solid var(--pc-ok); }
.pc-event.k-alert   { border-left: 3px solid var(--pc-red); }
.pc-event.k-mitigate{ border-left: 3px solid var(--pc-warn); }
.pc-event.k-attack  { border-left: 3px solid var(--pc-cyan); }
.pc-banner {
  background: linear-gradient(90deg, #0e1510, #05080c); border: 1px solid var(--pc-border);
  border-radius: 10px; padding: 8px 18px; margin-bottom: 10px;
  font-family: Consolas, monospace; font-size: 14px; color: var(--pc-ok); letter-spacing: 2px;
}
</style>
"""

# ---------- FUNCTIONS
def inject_css() -> None:
    """Inject the shared PassClash stylesheet into the current page."""
    st.markdown(CSS, unsafe_allow_html=True)


def banner(text: str) -> None:
    """Render a styled page banner containing *text*."""
    st.markdown(f'<div class="pc-banner">{text}</div>', unsafe_allow_html=True)


def role_selector() -> str:
    """Render the role selector and return its chosen role."""
    return st.sidebar.radio(
        "Operate as",
        ("Red Team", "Blue Team", "Game Master"),
        index=0,
    )


def visible_events(state: GameState, role: str, limit: int = 50) -> list[dict]:
    """Events a role may see.

    Blue only sees attack telemetry (progress, cracks, attack starts) while
    its monitoring is enabled -- an SOC that hasn't deployed rules sees
    nothing.
    """
    events = recent(role="blue" if role == "Blue Team" else "gm", limit=limit)
    if role == "Blue Team" and not state.monitoring:
        events = [e for e in events if e["kind"] in ("mitigate", "gm")]
    return events


def render_events(events: list[dict]) -> None:
    """Render a supplied list of event-bus entries."""
    for e in events:
        kind = e["kind"]
        icon = {
            "attack": "▸", "crack": "✔", "alert": "⚠",
            "mitigate": "▣", "progress": "·", "round": "■", "gm": "◆",
        }.get(kind, "·")
        st.markdown(
            f'<div class="pc-event k-{kind}">'
            f'<span class="t">[{e["t"]:.0f}]</span> '
            f'<span>{icon} {e["msg"]}</span></div>',
            unsafe_allow_html=True,
        )


def targets_row(state: GameState) -> None:
    """Render the compact target-status summary."""
    st.markdown(algo_badges(state), unsafe_allow_html=True)
