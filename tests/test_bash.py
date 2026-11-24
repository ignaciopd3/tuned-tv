"""Encontrar bash: Git Bash en Windows, nunca el bash.exe de WSL."""

import pytest

from tvopt.core import bash


def test_tvopt_bash_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TVOPT_BASH", "/opt/mi/bash")
    assert bash.find_bash() == "/opt/mi/bash"


def test_never_the_wsl_launcher(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TVOPT_BASH", raising=False)
    monkeypatch.setattr(bash.sys, "platform", "win32")
    monkeypatch.setattr(bash, "_git_bash_candidates", lambda: [])
    monkeypatch.setattr(bash.shutil, "which", lambda _name: r"C:\Windows\System32\bash.exe")
    with pytest.raises(FileNotFoundError):
        bash.find_bash()
