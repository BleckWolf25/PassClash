"""
File: terminal.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Terminal-style rendering components for hashcat/hydra simulation display.

Description:
    This module provides visual rendering helpers that mimic real password cracking tools
    (hashcat, hydra) using styled HTML blocks. Functions generate status displays, progress
    indicators, recovery banners, and algorithm badges. The terminal styling is purely
    visual, keeping PassClash dependency-free while maintaining authentic tool appearance
    through CSS styling injected in the main application.

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from __future__ import annotations

from . import hashes
from .engine import CrackingJob
from .scenario import GameState

# ---------- CONSTANTS
_STATUS_COLORS = {
    "idle": "dim",
    "running": "ok",
    "cracked": "ok",
    "exhausted": "warn",
    "stopped": "warn",
    "over": "warn",
}

# ---------- FUNCTIONS
def _fmt_secs(seconds: float) -> str:
    seconds = int(max(0, seconds))
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h} hrs {m} mins"
    if m:
        return f"{m} mins {s} secs"
    return f"{s} secs"


def _fmt_rate(rate: float) -> str:
    if rate >= 1_000_000:
        return f"{rate / 1_000_000:,.2f} MH/s"
    if rate >= 1_000:
        return f"{rate / 1_000:,.1f} kH/s"
    return f"{rate:,.0f} H/s"


def status_block(job: CrackingJob, state: GameState) -> str:
    """hashcat-style ``--status`` block as styled HTML."""
    total = job.candidates()
    recovered = [t for t in state.targets if t.recovered]
    progress = f"{job.attempts:,}" if total is None else (
        f"{job.attempts:,}/{total:,} ({job.attempts / max(total, 1) * 100:.2f}%)"
    )
    eta = _fmt_secs(job.eta) if job.eta is not None else "N/A"
    status = _STATUS_COLORS.get(job.status, "dim")
    budget = _fmt_secs(state.time_remaining())

    rows = [
        ("Session..........:", job.session_name),
        ("Status...........:", f'<span class="c-{status}">{job.status}</span>'),
        ("Hash.Mode........:", _mode_label(job)),
        ("Hash.Target......:", f"{len(recovered)}/{len(state.targets)} Digests"),
        ("Time.Started.....:", _fmt_secs(job.elapsed) + " ago"),
        ("Speed.#1.........:", _fmt_rate(job.rate)),
        (
            "Recovered........:",
            f"{len(recovered)}/{len(state.targets)} "
            f"({len(recovered) / max(len(state.targets), 1) * 100:.0f}%)",
        ),
        ("Progress.........:", progress),
        ("ETA..............:", eta),
        ("Round clock......:", budget + " remaining"),
        ("Restrictions.....:", _restrictions(state)),
    ]
    lines = [f"<span class='c-dim'>{k}</span> {v}" for k, v in rows]
    return "<pre class='hc'>" + "\n".join(lines) + "</pre>"


def _mode_label(job: CrackingJob) -> str:
    label = job.mode
    if job.mode == "mask":
        return f"mask ({job.mask})"
    if job.mode == "rules":
        return f"rules ({job.rule})"
    return label


def _restrictions(state: GameState) -> str:
    parts = []
    locked = sum(1 for t in state.targets if t.locked)
    if locked:
        parts.append(f"{locked} account(s) locked")
    if state.rate_limited:
        parts.append("rate-limited")
    if state.rotation_done:
        parts.append("rotated to bcrypt")
    if state.policy_enforced:
        parts.append("policy enforced")
    return ", ".join(parts) if parts else "none"


def crack_banner(user: str, plaintext: str, algo: str, index: int, total: int) -> str:
    """The classic all-caps recovery banner."""
    return (
        f"<pre class='hc'><span class='c-ok'>Cracked: {user}:{plaintext}</span>\n"
        f"<span class='c-dim'>Recovered {index}/{total} hashes ({algo})</span></pre>"
    )


def hydra_lines(entries: list[tuple[str, str, str]]) -> str:
    """hydra-style successful-login lines, newest first."""
    rows = [
        f"<span class='c-dim'>[22][ssh] host: 10.0.0.5 login: {user} "
        f"password: {pwd}</span>"
        for user, pwd, _ in entries
    ]
    return "<pre class='hc'>" + "\n".join(rows) + "</pre>"


def algo_badges(state: GameState) -> str:
    """Coloured per-target summary used by red and GM views."""
    parts = []
    for t in state.targets:
        color = "ok" if t.recovered else ("warn" if t.locked else "dim")
        parts.append(
            f"<span class='c-{color}'>{t.user} [{t.algo}]</span>"
        )
    return "&nbsp;&nbsp;".join(parts)


def algo_weight(algo: str) -> int:
    """Return the score weight configured for *algo*."""
    return hashes.ALGOS[algo]["weight"]
