#!/usr/bin/env python3
"""Run NotebookLM bridge scripts inside the skill-local virtual environment."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def skill_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def venv_python() -> Path:
    root = skill_dir() / ".venv"
    if os.name == "nt":
        return root / "Scripts" / "python.exe"
    return root / "bin" / "python"


def ensure_environment() -> Path:
    root = skill_dir()
    python_exe = venv_python()
    requirements = root / "requirements.txt"
    stamp = root / ".venv" / ".requirements-stamp"
    requirements_current = requirements.read_text(encoding="utf-8") if requirements.exists() else ""

    if python_exe.exists() and stamp.exists():
        try:
            if stamp.read_text(encoding="utf-8") == requirements_current:
                return python_exe
        except Exception:
            pass

    if python_exe.exists() and not requirements.exists():
        return python_exe

    setup_script = root / "scripts" / "setup_environment.py"
    result = subprocess.run([sys.executable, str(setup_script)], check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    return python_exe


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/run.py <script_name> [args...]")
        return 1

    script_name = sys.argv[1]
    if script_name.startswith("scripts/"):
        script_name = script_name.split("/", 1)[1]
    if not script_name.endswith(".py"):
        script_name += ".py"

    target = skill_dir() / "scripts" / script_name
    if not target.exists():
        print(f"Script not found: {target}")
        return 1

    python_exe = ensure_environment()
    cmd = [str(python_exe), str(target), *sys.argv[2:]]
    return subprocess.run(cmd, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
