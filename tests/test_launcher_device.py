"""Launcher: qué hay que instalar, comparando huellas, y la lectura de las huellas de la tele."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from tvopt.adb.client import Adb
from tvopt.android_tv.launcher import device
from tvopt.core.log import Fail, Log


def test_only_changed_packages_are_installed(tmp_path: Path) -> None:
    same, changed = tmp_path / "same.apk", tmp_path / "changed.apk"
    same.write_bytes(b"igual")
    changed.write_bytes(b"nuevo")
    wanted = {"io.a": same, "io.b": changed, "io.c": changed}
    installed = {"io.a": device.sha256(same), "io.b": "otra"}
    assert device.to_install(wanted, installed) == ["io.b", "io.c"]


def test_reads_installed_hashes() -> None:
    sections = {
        "h0": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08  /data/app/~~x/io.a-1/base.apk",
        "h1": "",
    }
    assert device.parse_hashes(sections, ["io.a", "io.b"]) == {
        "io.a": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
    }


def test_hash_script_is_one_batch() -> None:
    sections = device.hash_sections(["io.a", "io.b"])
    assert list(sections) == ["h0", "h1"]
    assert "pm path io.a" in sections["h0"] and "sha256sum" in sections["h0"]


def test_home_is_ours_or_the_stock_one_given() -> None:
    ours = "  mResumedActivity: ActivityRecord{1 u0 com.gathin.tvhome/.MainActivity t5}"
    amazon = "  mResumedActivity: ActivityRecord{2 u0 com.amazon.tv.launcher/.ui.HomeActivity_vNext t1}"
    hdmi = "  mResumedActivity: ActivityRecord{3 u0 com.amazon.tv.inputpreference.service/.TvInputActivity t9}"
    stock = (device.LAUNCHER, "com.amazon.tv.launcher")
    assert device.is_home(ours, (device.LAUNCHER,))
    assert not device.is_home(amazon, (device.LAUNCHER,))
    assert device.is_home(amazon, stock)
    assert not device.is_home(hdmi, stock)
    assert not device.is_home("", stock)


class _Shell:
    def __init__(self, answer: str) -> None:
        self.answer, self.sent = answer, ""

    def shell(self, script: str, timeout: float = 120) -> str:
        self.sent = script
        return self.answer


def test_keep_alive_grants_and_enables_guard_revival() -> None:
    ok = _Shell("listo\n")
    device.keep_alive(cast(Adb, ok), Log())
    assert "pm grant com.gathin.tvhome android.permission.WRITE_SECURE_SETTINGS" in ok.sent
    assert "appops set com.gathin.tvhome GET_USAGE_STATS allow" in ok.sent
    assert "cmd notification allow_listener com.gathin.tvhome/.GuardRevival" in ok.sent
    with pytest.raises(Fail):
        device.keep_alive(cast(Adb, _Shell("Security exception\nno\n")), Log())
