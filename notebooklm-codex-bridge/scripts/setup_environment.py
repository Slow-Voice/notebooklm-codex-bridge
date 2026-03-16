#!/usr/bin/env python3
"""Create and maintain the skill-local virtual environment."""

from __future__ import annotations

import os
import subprocess
import sys
import venv
from pathlib import Path


class EnvironmentManager:
    def __init__(self) -> None:
        self.root = Path(__file__).resolve().parent.parent
        self.venv_dir = self.root / ".venv"
        self.requirements = self.root / "requirements.txt"
        self.stamp = self.venv_dir / ".requirements-stamp"

        if os.name == "nt":
            self.python = self.venv_dir / "Scripts" / "python.exe"
            self.pip = self.venv_dir / "Scripts" / "pip.exe"
        else:
            self.python = self.venv_dir / "bin" / "python"
            self.pip = self.venv_dir / "bin" / "pip"

    def ensure(self) -> int:
        if not self.venv_dir.exists():
            print("Creating .venv for notebooklm-codex-bridge...")
            venv.create(self.venv_dir, with_pip=True)

        print("Installing Python dependencies...")
        subprocess.run([str(self.python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([str(self.python), "-m", "pip", "install", "-r", str(self.requirements)], check=True)

        try:
            subprocess.run([str(self.python), "-m", "patchright", "install", "chrome"], check=True)
        except subprocess.CalledProcessError:
            print("Warning: patchright could not auto-install Chrome.")
            print("You can retry manually with:")
            print(f"  {self.python} -m patchright install chrome")
        self.stamp.write_text(self.requirements.read_text(encoding="utf-8"), encoding="utf-8")
        return 0


def main() -> int:
    manager = EnvironmentManager()
    return manager.ensure()


if __name__ == "__main__":
    raise SystemExit(main())
