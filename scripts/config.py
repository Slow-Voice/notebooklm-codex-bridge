"""Shared paths and selectors for NotebookLM browser automation."""

from __future__ import annotations

from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
BROWSER_STATE_DIR = DATA_DIR / "browser_state"
BROWSER_PROFILE_DIR = BROWSER_STATE_DIR / "browser_profile"
STATE_FILE = BROWSER_STATE_DIR / "state.json"
AUTH_INFO_FILE = DATA_DIR / "auth_info.json"
LIBRARY_FILE = DATA_DIR / "library.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
BROWSER_STATE_DIR.mkdir(parents=True, exist_ok=True)
BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

NOTEBOOKLM_HOME = "https://notebooklm.google.com/"

QUERY_INPUT_SELECTORS = [
    "textarea.query-box-input",
    'textarea[aria-label="Input for queries"]',
    'textarea[aria-label*="query"]',
    "textarea",
]

RESPONSE_SELECTORS = [
    ".to-user-container .message-text-content",
    "[data-message-author='bot']",
    "[data-message-author='assistant']",
    "div.markdown",
]

BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--no-first-run",
    "--no-default-browser-check",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
)
