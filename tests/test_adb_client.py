"""Cliente ADB: varias lecturas en una sola ida y vuelta, contra la tele simulada."""

from __future__ import annotations

import pytest
from conftest import FakeTv

from tvopt.adb.client import Adb, AdbError, build_script, split_sections


def test_build_and_split_round_trip() -> None:
    script = build_script({"a": "getprop x", "b.c": "echo 2"})
    assert script == "echo ==a==; getprop x; echo ==b.c==; echo 2"
    assert split_sections("ruido\n==a==\nuno\n==b.c==\ndos\ntres\n") == {"a": "uno", "b.c": "dos\ntres"}


def test_rejects_unsafe_names_and_serials() -> None:
    with pytest.raises(ValueError):
        build_script({"a; rm": "x"})
    with pytest.raises(ValueError):
        Adb("tele; rm -rf /")


def test_batch_reads_everything_in_one_call(fake_tv: FakeTv) -> None:
    adb = Adb("fake:5555")
    adb.connect()
    got = adb.batch({"brand": "getprop ro.product.brand", "model": "getprop ro.product.model"})
    assert got == {"brand": "FakeBrand", "model": "Fake TV"}


def test_unauthorized_warns_once_then_fails(fake_tv: FakeTv) -> None:
    (fake_tv.tv / "state").write_text("unauthorized\n", encoding="utf-8")
    warnings: list[str] = []
    adb = Adb("fake:5555", wait_secs=2, warn=warnings.append)
    with pytest.raises(AdbError):
        adb.connect()
    assert len(warnings) == 1
    assert "Permitir" in warnings[0]
