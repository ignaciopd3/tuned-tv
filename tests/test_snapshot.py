"""Foto del estado de la tele contra la tele simulada, y scripts subidos y ejecutados en una sola sesión."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from conftest import FakeTv

from tvopt.adb.client import Adb
from tvopt.android_tv import snapshot
from tvopt.core.log import Fail, Log


def test_take_and_load(fake_tv: FakeTv) -> None:
    adb = Adb("fake:5555")
    snap = fake_tv.work / "snap"
    snapshot.take(adb, snap, Log())
    assert (snap / "packages.installed").read_text(encoding="utf-8").startswith("com.android.systemui\n")
    assert not os.access(snap / "props.txt", os.W_OK), "la foto queda en solo lectura"
    states, settings = snapshot.load(snap)
    assert states["com.tcl.already"] == "disabled"
    assert states["com.bloat.ads"] == "enabled"
    assert settings["global window_animation_scale"] == "1.0"
    assert settings["secure some_list"] == "a b'c"


def test_run_dirs_never_collide(tmp_path: Path) -> None:
    first, second = snapshot.run_dir_new(tmp_path), snapshot.run_dir_new(tmp_path)
    assert first != second and first.is_dir() and second.is_dir()


def test_fresh_skips_existing(tmp_path: Path) -> None:
    (tmp_path / "rollback-1").mkdir()
    assert snapshot.fresh(tmp_path, "rollback-1").name == "rollback-1-1"


def test_run_script_returns_code_and_output(fake_tv: FakeTv) -> None:
    script = fake_tv.work / "s.sh"
    script.write_text("echo hola\nexit 3\n", encoding="utf-8", newline="\n")
    assert Adb("fake:5555").run_script(script) == (3, "hola\n")


def test_unreachable_tv_fails_cleanly(fake_tv: FakeTv) -> None:
    (fake_tv.tv / "state").write_text("offline\n", encoding="utf-8")
    adb = Adb("fake:5555", command=["no-existe-este-adb"])
    with pytest.raises(Fail):
        snapshot.take(adb, fake_tv.work / "snap", Log())
