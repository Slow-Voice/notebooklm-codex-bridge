#!/usr/bin/env python3
"""Persistent Google authentication for NotebookLM."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import time
from typing import Any

from patchright.sync_api import BrowserContext, sync_playwright

from browser_utils import BrowserFactory
from config import AUTH_INFO_FILE, BROWSER_STATE_DIR, NOTEBOOKLM_HOME, STATE_FILE


class AuthManager:
    def is_authenticated(self) -> bool:
        return STATE_FILE.exists()

    def get_auth_info(self) -> dict[str, Any]:
        info: dict[str, Any] = {
            "authenticated": self.is_authenticated(),
            "state_file": str(STATE_FILE),
            "state_exists": STATE_FILE.exists(),
        }
        if AUTH_INFO_FILE.exists():
            try:
                info.update(json.loads(AUTH_INFO_FILE.read_text(encoding="utf-8")))
            except Exception:
                pass
        if STATE_FILE.exists():
            info["state_age_hours"] = (time.time() - STATE_FILE.stat().st_mtime) / 3600.0
        return info

    def save_state(self, context: BrowserContext) -> None:
        context.storage_state(path=str(STATE_FILE))
        AUTH_INFO_FILE.write_text(
            json.dumps(
                {
                    "authenticated_at": time.time(),
                    "authenticated_at_iso": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def setup_auth(self, timeout_minutes: float = 10.0, headless: bool = False) -> bool:
        playwright = None
        context = None
        try:
            playwright = sync_playwright().start()
            context = BrowserFactory.launch_persistent_context(playwright, headless=headless)
            page = context.new_page()
            page.goto(NOTEBOOKLM_HOME, wait_until="domcontentloaded")

            timeout_ms = int(timeout_minutes * 60 * 1000)
            print("Browser opened. Complete Google login in the visible window.")
            page.wait_for_url(re.compile(r"^https://notebooklm\.google\.com/"), timeout=timeout_ms)

            self.save_state(context)
            return True
        except Exception as exc:
            print(f"Authentication failed: {exc}")
            return False
        finally:
            if context:
                try:
                    context.close()
                except Exception:
                    pass
            if playwright:
                try:
                    playwright.stop()
                except Exception:
                    pass

    def validate_auth(self) -> bool:
        if not self.is_authenticated():
            return False

        playwright = None
        context = None
        try:
            playwright = sync_playwright().start()
            context = BrowserFactory.launch_persistent_context(playwright, headless=True)
            page = context.new_page()
            page.goto(NOTEBOOKLM_HOME, wait_until="domcontentloaded", timeout=30000)
            return "accounts.google.com" not in page.url and "notebooklm.google.com" in page.url
        except Exception as exc:
            print(f"Validation failed: {exc}")
            return False
        finally:
            if context:
                try:
                    context.close()
                except Exception:
                    pass
            if playwright:
                try:
                    playwright.stop()
                except Exception:
                    pass

    def clear_auth(self) -> bool:
        try:
            if STATE_FILE.exists():
                STATE_FILE.unlink()
            if AUTH_INFO_FILE.exists():
                AUTH_INFO_FILE.unlink()
            if BROWSER_STATE_DIR.exists():
                shutil.rmtree(BROWSER_STATE_DIR)
            BROWSER_STATE_DIR.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as exc:
            print(f"Could not clear auth: {exc}")
            return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage NotebookLM authentication")
    sub = parser.add_subparsers(dest="command")

    setup = sub.add_parser("setup")
    setup.add_argument("--timeout", type=float, default=10.0)
    setup.add_argument("--headless", action="store_true")
    sub.add_parser("status")
    sub.add_parser("validate")
    sub.add_parser("clear")
    reauth = sub.add_parser("reauth")
    reauth.add_argument("--timeout", type=float, default=10.0)

    args = parser.parse_args()
    manager = AuthManager()

    if args.command == "setup":
        return 0 if manager.setup_auth(timeout_minutes=args.timeout, headless=args.headless) else 1
    if args.command == "status":
        print(json.dumps(manager.get_auth_info(), indent=2))
        return 0
    if args.command == "validate":
        ok = manager.validate_auth()
        print("valid" if ok else "invalid")
        return 0 if ok else 1
    if args.command == "clear":
        return 0 if manager.clear_auth() else 1
    if args.command == "reauth":
        manager.clear_auth()
        return 0 if manager.setup_auth(timeout_minutes=args.timeout, headless=False) else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
