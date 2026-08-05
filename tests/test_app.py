"""
File: test_app.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Smoke tests for the Streamlit application using Streamlit's AppTest framework.

Description:
    This module contains integration tests for the PassClash Streamlit application,
    verifying that the app starts correctly, loads the default scenario, and properly
    switches between different team roles (Red Team, Blue Team, Game Master). Tests
    use Streamlit's AppTest framework to simulate user interactions and validate UI
    rendering without exceptions.

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from pathlib import Path

from streamlit.testing.v1 import AppTest

# ---------- CONSTANTS
APP_PATH = str(Path(__file__).resolve().parent.parent / "passclash" / "app.py")

# ---------- FIXTURE
def test_app_starts_and_renders_red_team():
    """The default application view starts without a Streamlit exception."""
    at = AppTest.from_file(APP_PATH).run()
    assert not at.exception
    titles = [t.value for t in at.title]
    assert any("PassClash" in str(t) for t in titles)


def test_app_loads_default_scenario():
    """The default scenario metadata is visible in the application sidebar."""
    at = AppTest.from_file(APP_PATH).run()
    assert not at.exception
    captions = [c.value for c in at.caption]
    assert any("Nexus Corp" in str(c) for c in captions)


def test_app_switch_to_blue_team():
    """Selecting Blue Team renders the blue-team interface."""
    at = AppTest.from_file(APP_PATH).run()
    assert not at.exception
    at.radio[0].set_value("Blue Team")
    at.run()
    assert not at.exception
    titles = [t.value for t in at.title]
    assert any("Blue Team" in str(t) for t in titles)


def test_app_switch_to_game_master():
    """Selecting Game Master renders the game-master interface."""
    at = AppTest.from_file(APP_PATH).run()
    assert not at.exception
    at.radio[0].set_value("Game Master")
    at.run()
    assert not at.exception
    titles = [t.value for t in at.title]
    assert any("Game Master" in str(t) for t in titles)
