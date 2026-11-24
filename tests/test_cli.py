"""run.py: la entrada única de tv-opt."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_help_lists_the_commands() -> None:
    r = subprocess.run([sys.executable, str(ROOT / "run.py"), "--help"], capture_output=True, text=True, check=False)
    assert r.returncode == 0
    assert "motor" in r.stdout


def test_version() -> None:
    r = subprocess.run([sys.executable, str(ROOT / "run.py"), "--version"], capture_output=True, text=True, check=False)
    assert r.returncode == 0
    assert r.stdout.startswith("tv-opt ")


def test_motor_passes_everything_to_the_engine() -> None:
    r = subprocess.run(
        [sys.executable, str(ROOT / "run.py"), "motor", "--help"], capture_output=True, text=True, check=False
    )
    assert r.returncode == 0
    assert "Uso: run.py motor" in r.stdout


def test_launcher_rejects_bad_profiles() -> None:
    from tvopt import cli

    assert cli.main(["launcher", "--perfil", "../etc"]) == 2
    assert cli.main(["launcher", "--perfil", "perfil-que-no-existe"]) == 2
