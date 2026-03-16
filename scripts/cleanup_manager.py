#!/usr/bin/env python3
"""Reset NotebookLM local state while optionally keeping the library catalog."""

from __future__ import annotations

import argparse
import shutil

from config import AUTH_INFO_FILE, BROWSER_STATE_DIR, DATA_DIR, LIBRARY_FILE


def preview(preserve_library: bool) -> None:
    print("Will remove:")
    if BROWSER_STATE_DIR.exists():
        print(f"  {BROWSER_STATE_DIR}")
    if AUTH_INFO_FILE.exists():
        print(f"  {AUTH_INFO_FILE}")
    if LIBRARY_FILE.exists() and not preserve_library:
        print(f"  {LIBRARY_FILE}")


def cleanup(preserve_library: bool) -> int:
    if BROWSER_STATE_DIR.exists():
        shutil.rmtree(BROWSER_STATE_DIR)
    BROWSER_STATE_DIR.mkdir(parents=True, exist_ok=True)

    if AUTH_INFO_FILE.exists():
        AUTH_INFO_FILE.unlink()

    if LIBRARY_FILE.exists() and not preserve_library:
        LIBRARY_FILE.unlink()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean NotebookLM bridge local state")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--preserve-library", action="store_true")
    args = parser.parse_args()

    if not args.confirm:
        preview(args.preserve_library)
        print("Re-run with --confirm to execute cleanup.")
        return 0
    return cleanup(args.preserve_library)


if __name__ == "__main__":
    raise SystemExit(main())
