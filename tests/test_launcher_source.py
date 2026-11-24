"""Launcher: lectura de BASE y ADDONS, y huella de la caché de APK."""

from __future__ import annotations

from pathlib import Path

import pytest

from tvopt.android_tv.launcher import source
from tvopt.core.log import Fail


def _profile(tmp_path: Path, patch: str = "parche 1\n", addons: str = "weather io.x.weather\n") -> Path:
    patches = tmp_path / "launcher" / "patches"
    patches.mkdir(parents=True)
    (patches / "BASE").write_text("https://example.org/cyt.git abc123\n", encoding="utf-8")
    (patches / "0001-a.patch").write_text(patch, encoding="utf-8")
    (patches / "ADDONS").write_text(f"# complementos\n{addons}\n", encoding="utf-8")
    return tmp_path / "launcher"


def test_reads_base_and_addons(tmp_path: Path) -> None:
    src = source.Source.load(_profile(tmp_path))
    assert src.url == "https://example.org/cyt.git" and src.commit == "abc123"
    assert src.addons == (("weather", "io.x.weather"),)
    assert [p.name for p in src.patches] == ["0001-a.patch"]


def test_fingerprint_follows_patches_and_addons(tmp_path: Path) -> None:
    a = source.Source.load(_profile(tmp_path / "a")).fingerprint(b"clave")
    same = source.Source.load(_profile(tmp_path / "b")).fingerprint(b"clave")
    other_patch = source.Source.load(_profile(tmp_path / "c", patch="parche 2\n")).fingerprint(b"clave")
    other_addons = source.Source.load(_profile(tmp_path / "d", addons="casa io.x.casa\n")).fingerprint(b"clave")
    other_key = source.Source.load(_profile(tmp_path / "e")).fingerprint(b"otra")
    assert a == same
    assert len({a, other_patch, other_addons, other_key}) == 4


def test_missing_base_is_a_usage_error(tmp_path: Path) -> None:
    (tmp_path / "launcher").mkdir()
    with pytest.raises(Fail) as e:
        source.Source.load(tmp_path / "launcher")
    assert e.value.code == 2


def test_cache_round_trip(tmp_path: Path) -> None:
    cache = source.ApkCache(tmp_path / "cache")
    built = tmp_path / "out"
    built.mkdir()
    (built / "launcher.apk").write_bytes(b"apk-launcher")
    (built / "weather.apk").write_bytes(b"apk-weather")
    assert cache.get("f1", ("launcher", "weather")) is None
    cache.put("f1", {"launcher": built / "launcher.apk", "weather": built / "weather.apk"})
    got = cache.get("f1", ("launcher", "weather"))
    assert got is not None and got["weather"].read_bytes() == b"apk-weather"
    assert cache.get("f1", ("launcher", "casa")) is None, "si falta un APK, no vale la entrada"
