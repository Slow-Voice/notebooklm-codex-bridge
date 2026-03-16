"""Helpers for launching Patchright with persistent browser state."""

from __future__ import annotations

import json
import random
import time

from patchright.sync_api import BrowserContext, Page, Playwright

from config import BROWSER_ARGS, BROWSER_PROFILE_DIR, STATE_FILE, USER_AGENT


class BrowserFactory:
    @staticmethod
    def launch_persistent_context(playwright: Playwright, headless: bool = True) -> BrowserContext:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_PROFILE_DIR),
            channel="chrome",
            headless=headless,
            no_viewport=True,
            ignore_default_args=["--enable-automation"],
            user_agent=USER_AGENT,
            args=BROWSER_ARGS,
        )
        BrowserFactory.inject_cookies(context)
        return context

    @staticmethod
    def inject_cookies(context: BrowserContext) -> None:
        if not STATE_FILE.exists():
            return
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            cookies = data.get("cookies") or []
            if cookies:
                context.add_cookies(cookies)
        except Exception as exc:
            print(f"Warning: could not load cookies from {STATE_FILE}: {exc}")


class Humanize:
    @staticmethod
    def pause(min_ms: int = 100, max_ms: int = 400) -> None:
        time.sleep(random.uniform(min_ms / 1000.0, max_ms / 1000.0))

    @staticmethod
    def type_text(page: Page, selector: str, text: str) -> bool:
        try:
            element = page.wait_for_selector(selector, timeout=2500, state="visible")
        except Exception:
            return False

        element.click()
        for char in text:
            element.type(char, delay=random.uniform(20, 70))
            if random.random() < 0.04:
                time.sleep(random.uniform(0.1, 0.35))
        return True
