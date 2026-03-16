#!/usr/bin/env python3
"""Ask a question to NotebookLM through browser automation."""

from __future__ import annotations

import argparse
import json
import re
import time

from patchright.sync_api import sync_playwright

from auth_manager import AuthManager
from browser_utils import BrowserFactory, Humanize
from config import QUERY_INPUT_SELECTORS, RESPONSE_SELECTORS
from notebook_manager import NotebookLibrary

LOADING_MARKERS = {
    "reading your inputs...",
    "looking at sources...",
    "looking for answers...",
    "finding relevant info...",
    "retrieving details...",
    "analyzing your files...",
    "assessing relevance...",
    "reading through pages...",
    "finding key words...",
    "interpreting the prompt...",
    "deciphering the intent...",
    "clarifying the ambiguity...",
    "refining the interpretation...",
    "formulating the response...",
    "generating content options...",
    "reviewing the content...",
    "digging into details...",
    "processing material...",
    "opening your notes...",
    "checking your files...",
    "examining the specifics...",
    "confirming the scope...",
    "integrating relevant research...",
    "getting the context...",
    "reply ready.",
    "reply ready.",
}


def resolve_notebook_url(args: argparse.Namespace, library: NotebookLibrary) -> tuple[str | None, str | None]:
    if args.notebook_url:
        return args.notebook_url, None
    if args.notebook_id:
        notebook = library.get_notebook(args.notebook_id)
        if not notebook:
            return None, None
        return notebook["url"], notebook["id"]
    if library.active_notebook_id:
        notebook = library.get_notebook(library.active_notebook_id)
        if notebook:
            return notebook["url"], notebook["id"]
    return None, None


def find_query_input(page) -> str | None:
    for selector in QUERY_INPUT_SELECTORS:
        try:
            page.wait_for_selector(selector, timeout=4000, state="visible")
            return selector
        except Exception:
            continue
    return None


def read_latest_response(page) -> str | None:
    latest = None
    for selector in RESPONSE_SELECTORS:
        try:
            elements = page.query_selector_all(selector)
        except Exception:
            continue
        if elements:
            try:
                text = elements[-1].inner_text().strip()
            except Exception:
                text = ""
            if text:
                latest = text
    return latest


def is_meaningful_answer(text: str | None, baseline: str | None) -> bool:
    if not text:
        return False

    normalized = " ".join(text.strip().split()).lower()
    if not normalized:
        return False
    if baseline and normalized == " ".join(baseline.strip().split()).lower():
        return False
    if normalized in LOADING_MARKERS:
        return False
    if normalized.endswith("...") and len(normalized) < 120:
        return False
    return True


def ask_notebooklm(question: str, notebook_url: str, show_browser: bool = False) -> dict[str, str] | None:
    auth = AuthManager()
    if not auth.is_authenticated():
        print("Not authenticated. Run: python scripts/run.py auth_manager.py setup")
        return None

    playwright = None
    context = None
    try:
        playwright = sync_playwright().start()
        context = BrowserFactory.launch_persistent_context(playwright, headless=not show_browser)
        page = context.new_page()
        page.goto(notebook_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_url(re.compile(r"^https://notebooklm\.google\.com/"), timeout=20000)
        baseline_response = read_latest_response(page)

        selector = find_query_input(page)
        if not selector:
            print("Could not find NotebookLM query input. Retry with --show-browser.")
            return None

        if not Humanize.type_text(page, selector, question):
            print("Failed to type into NotebookLM query box.")
            return None

        page.keyboard.press("Enter")
        Humanize.pause(600, 1400)

        answer = None
        stable_hits = 0
        last_text = None
        deadline = time.time() + 120

        while time.time() < deadline:
            candidate = read_latest_response(page)
            if is_meaningful_answer(candidate, baseline_response):
                if candidate == last_text:
                    stable_hits += 1
                    if stable_hits >= 3:
                        answer = candidate
                        break
                else:
                    last_text = candidate
                    stable_hits = 0
            time.sleep(1)

        if not answer:
            page_text = page.locator("main").inner_text(timeout=5000)
            answer = page_text.strip() if page_text else None
        if not answer:
            return None

        return {
            "question": question,
            "notebook_url": notebook_url,
            "answer": answer,
        }
    except Exception as exc:
        print(f"NotebookLM query failed: {exc}")
        return None
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Ask NotebookLM a question")
    parser.add_argument("--question", required=True)
    parser.add_argument("--notebook-url")
    parser.add_argument("--notebook-id")
    parser.add_argument("--show-browser", action="store_true")
    args = parser.parse_args()

    library = NotebookLibrary()
    notebook_url, notebook_id = resolve_notebook_url(args, library)
    if not notebook_url:
        print("No notebook specified and no active notebook found.")
        print("Use --notebook-url, --notebook-id, or activate one in the library.")
        return 1

    result = ask_notebooklm(args.question, notebook_url, show_browser=args.show_browser)
    if not result:
        return 1

    if notebook_id:
        library.mark_used(notebook_id)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
