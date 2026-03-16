#!/usr/bin/env python3
"""Auto-select a notebook and ask NotebookLM in one command."""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys

from deep_translator import GoogleTranslator

from ask_question import ask_notebooklm
from notebook_manager import NotebookLibrary


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def score_notebook(notebook: dict, request_text: str) -> int:
    haystack = " ".join(
        [
            notebook.get("id", ""),
            notebook.get("name", ""),
            notebook.get("description", ""),
            " ".join(notebook.get("topics", [])),
        ]
    ).lower()

    score = 0
    for token in tokens(request_text):
        if token and token in haystack:
            score += 1
    if notebook.get("use_count"):
        score += min(int(notebook["use_count"]), 3)
    return score


def choose_notebook(library: NotebookLibrary, request_text: str) -> dict | None:
    notebooks = library.list_notebooks()
    if not notebooks:
        return None

    ranked = sorted(
        notebooks,
        key=lambda notebook: (
            score_notebook(notebook, request_text),
            1 if notebook["id"] == library.active_notebook_id else 0,
            notebook.get("use_count", 0),
        ),
        reverse=True,
    )
    return ranked[0]


def build_question_en(request: str, explicit_question_en: str | None) -> str:
    if explicit_question_en:
        return explicit_question_en.strip()
    translated = GoogleTranslator(source="auto", target="en").translate(request)
    if translated:
        return translated.strip()
    return request.strip()


def load_request(args: argparse.Namespace) -> str:
    if args.request_file:
        return args.request_file.read().lstrip("\ufeff").strip()
    if args.request_b64:
        return base64.b64decode(args.request_b64).decode("utf-8").strip()
    return (args.request or "").strip()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Select a notebook automatically and query it")
    parser.add_argument("--request", required=False, help="Original user request for routing")
    parser.add_argument("--request-file", type=argparse.FileType("r", encoding="utf-8"), required=False)
    parser.add_argument("--request-b64", required=False)
    parser.add_argument(
        "--question-en",
        required=False,
        help="English NotebookLM question to send after Codex translates the user intent",
    )
    parser.add_argument("--show-browser", action="store_true")
    args = parser.parse_args()
    request = load_request(args)
    if not request:
        print("Provide --request, --request-file, or --request-b64.")
        return 1

    library = NotebookLibrary()
    question_en = build_question_en(request, args.question_en)
    routing_text = f"{request} {question_en}"
    notebook = choose_notebook(library, routing_text)
    if not notebook:
        items = library.refresh_from_home(personal_only=True)
        if not items:
            print("No notebooks in the local library. Run notebook_manager.py refresh or add one first.")
            return 1
        notebook = choose_notebook(library, routing_text)
        if not notebook:
            print("No suitable notebook found after refresh.")
            return 1

    result = ask_notebooklm(question_en, notebook["url"], show_browser=args.show_browser)
    if not result:
        return 1

    library.mark_used(notebook["id"])
    payload = {
        "selected_notebook": {
            "id": notebook["id"],
            "name": notebook["name"],
            "url": notebook["url"],
            "description": notebook["description"],
            "topics": notebook.get("topics", []),
        },
        "request": request,
        "question_en": question_en,
        "answer": result["answer"],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
