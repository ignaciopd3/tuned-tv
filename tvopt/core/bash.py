"""Dónde está bash: para el motor de Bash mientras exista y para la tele simulada de las pruebas."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def _git_bash_candidates() -> list[Path]:
    roots = [os.environ.get("PROGRAMFILES", r"C:\Program Files"), os.environ.get("PROGRAMFILES(X86)", "")]
    local = os.environ.get("LOCALAPPDATA")
    if local:
        roots.append(str(Path(local) / "Programs"))
    return [Path(root) / "Git" / "bin" / "bash.exe" for root in roots if root]


def find_bash() -> str:
    """TVOPT_BASH si está; en Windows, Git Bash (el bash.exe de System32 es WSL y no sirve); si no, el del PATH."""
    forced = os.environ.get("TVOPT_BASH")
    if forced:
        return forced
    if sys.platform == "win32":
        for candidate in _git_bash_candidates():
            if candidate.is_file():
                return str(candidate)
        found = shutil.which("bash")
        if found and "system32" not in found.lower():
            return found
        raise FileNotFoundError("No encuentro Git Bash: instala Git for Windows o indica su ruta en TVOPT_BASH")
    found = shutil.which("bash")
    if not found:
        raise FileNotFoundError("No encuentro bash en el PATH")
    return found
