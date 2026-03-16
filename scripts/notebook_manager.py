#!/usr/bin/env python3
"""Manage a local catalog of NotebookLM notebook URLs and metadata."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from typing import Any

from patchright.sync_api import sync_playwright

from browser_utils import BrowserFactory
from config import NOTEBOOKLM_HOME
from config import LIBRARY_FILE


class NotebookLibrary:
    def __init__(self) -> None:
        self.notebooks: dict[str, dict[str, Any]] = {}
        self.active_notebook_id: str | None = None
        self.load()

    def load(self) -> None:
        if not LIBRARY_FILE.exists():
            self.save()
            return
        data = json.loads(LIBRARY_FILE.read_text(encoding="utf-8"))
        self.notebooks = data.get("notebooks", {})
        self.active_notebook_id = data.get("active_notebook_id")

    def save(self) -> None:
        LIBRARY_FILE.write_text(
            json.dumps(
                {
                    "notebooks": self.notebooks,
                    "active_notebook_id": self.active_notebook_id,
                    "updated_at": datetime.now().isoformat(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def add_notebook(self, url: str, name: str, description: str, topics: list[str]) -> dict[str, Any]:
        notebook_id = name.strip().lower().replace(" ", "-").replace("_", "-")
        if notebook_id in self.notebooks:
            raise ValueError(f"Notebook already exists: {notebook_id}")

        item = {
            "id": notebook_id,
            "url": url,
            "name": name,
            "description": description,
            "topics": topics,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "use_count": 0,
            "last_used": None,
        }
        self.notebooks[notebook_id] = item
        if not self.active_notebook_id:
            self.active_notebook_id = notebook_id
        self.save()
        return item

    def add_or_update_notebook(self, url: str, name: str, description: str, topics: list[str]) -> dict[str, Any]:
        notebook_id = name.strip().lower().replace(" ", "-").replace("_", "-")
        existing = self.notebooks.get(notebook_id)
        if existing:
            existing["url"] = url
            existing["name"] = name
            existing["description"] = description
            existing["topics"] = topics
            existing["updated_at"] = datetime.now().isoformat()
            self.save()
            return existing
        return self.add_notebook(url=url, name=name, description=description, topics=topics)

    def list_notebooks(self) -> list[dict[str, Any]]:
        return list(self.notebooks.values())

    def get_notebook(self, notebook_id: str) -> dict[str, Any] | None:
        return self.notebooks.get(notebook_id)

    def activate(self, notebook_id: str) -> dict[str, Any]:
        notebook = self.get_notebook(notebook_id)
        if not notebook:
            raise ValueError(f"Notebook not found: {notebook_id}")
        self.active_notebook_id = notebook_id
        self.save()
        return notebook

    def remove(self, notebook_id: str) -> bool:
        if notebook_id not in self.notebooks:
            return False
        del self.notebooks[notebook_id]
        if self.active_notebook_id == notebook_id:
            self.active_notebook_id = next(iter(self.notebooks), None)
        self.save()
        return True

    def search(self, query: str) -> list[dict[str, Any]]:
        needle = query.lower()
        found = []
        for notebook in self.notebooks.values():
            haystack = " ".join(
                [
                    notebook["id"],
                    notebook["name"],
                    notebook["description"],
                    " ".join(notebook.get("topics", [])),
                ]
            ).lower()
            if needle in haystack:
                found.append(notebook)
        return found

    def mark_used(self, notebook_id: str) -> None:
        notebook = self.get_notebook(notebook_id)
        if not notebook:
            return
        notebook["use_count"] = int(notebook.get("use_count", 0)) + 1
        notebook["last_used"] = datetime.now().isoformat()
        notebook["updated_at"] = datetime.now().isoformat()
        self.save()

    @staticmethod
    def _extract_name(lines: list[str]) -> str | None:
        noise = {"public", "more_vert", "add", "recent"}
        for line in lines:
            compact = line.strip()
            if not compact:
                continue
            if compact.lower() in noise:
                continue
            if re.fullmatch(r"[\W_]+", compact):
                continue
            if "source" in compact.lower():
                continue
            if re.search(r"\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d+\s*sources", compact.lower()):
                continue
            return compact
        return None

    def refresh_from_home(self, personal_only: bool = True) -> list[dict[str, Any]]:
        playwright = None
        context = None
        discovered: list[dict[str, Any]] = []
        try:
            playwright = sync_playwright().start()
            context = BrowserFactory.launch_persistent_context(playwright, headless=True)
            page = context.new_page()
            page.goto(NOTEBOOKLM_HOME, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(4000)

            cards = page.locator("mat-card.project-button-card")
            total = cards.count()
            for index in range(total):
                page.goto(NOTEBOOKLM_HOME, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)
                card = page.locator("mat-card.project-button-card").nth(index)
                text = card.inner_text()
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                if not lines:
                    continue
                if personal_only and lines[0].lower() == "public":
                    continue

                name = self._extract_name(lines)
                if not name:
                    continue

                card.click()
                page.wait_for_timeout(4000)
                url = page.url
                if "/notebook/" not in url:
                    continue

                item = self.add_or_update_notebook(
                    url=url,
                    name=name,
                    description=f"NotebookLM notebook: {name}",
                    topics=[],
                )
                discovered.append(item)

            if discovered and not self.active_notebook_id:
                self.active_notebook_id = discovered[0]["id"]
                self.save()
            return discovered
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


def print_notebooks(items: list[dict[str, Any]], active_notebook_id: str | None) -> None:
    if not items:
        print("No notebooks in the local library.")
        return
    for item in items:
        active = " [ACTIVE]" if item["id"] == active_notebook_id else ""
        print(f"{item['id']}{active}")
        print(f"  name: {item['name']}")
        print(f"  url: {item['url']}")
        print(f"  topics: {', '.join(item.get('topics', []))}")
        print(f"  description: {item['description']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage NotebookLM notebook library")
    sub = parser.add_subparsers(dest="command")

    add = sub.add_parser("add")
    add.add_argument("--url", required=True)
    add.add_argument("--name", required=True)
    add.add_argument("--description", required=True)
    add.add_argument("--topics", required=True)

    sub.add_parser("list")

    search = sub.add_parser("search")
    search.add_argument("--query", required=True)

    activate = sub.add_parser("activate")
    activate.add_argument("--id", required=True)

    remove = sub.add_parser("remove")
    remove.add_argument("--id", required=True)

    refresh = sub.add_parser("refresh")
    refresh.add_argument("--include-public", action="store_true")

    args = parser.parse_args()
    library = NotebookLibrary()

    if args.command == "add":
        item = library.add_notebook(
            url=args.url,
            name=args.name,
            description=args.description,
            topics=[topic.strip() for topic in args.topics.split(",") if topic.strip()],
        )
        print(json.dumps(item, indent=2))
        return 0
    if args.command == "list":
        print_notebooks(library.list_notebooks(), library.active_notebook_id)
        return 0
    if args.command == "search":
        print_notebooks(library.search(args.query), library.active_notebook_id)
        return 0
    if args.command == "activate":
        print(json.dumps(library.activate(args.id), indent=2))
        return 0
    if args.command == "remove":
        print("removed" if library.remove(args.id) else "not-found")
        return 0
    if args.command == "refresh":
        items = library.refresh_from_home(personal_only=not args.include_public)
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
