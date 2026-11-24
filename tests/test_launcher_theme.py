"""Tema: validación, qué archivos se envían y la misma escritura en la tele que tools/theme.sh."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tvopt.android_tv.launcher import theme
from tvopt.core.log import Fail


def _theme(tmp_path: Path, config: object = None) -> Path:
    (tmp_path / "config.json").write_text(json.dumps({"columns": 7} if config is None else config), encoding="utf-8")
    (tmp_path / "wallpapers").mkdir()
    (tmp_path / "wallpapers" / "001.jpg").write_bytes(b"jpg1")
    (tmp_path / "wallpapers" / "002.PNG").write_bytes(b"png2")
    (tmp_path / "wallpapers" / "captions.txt").write_text("001.jpg Autor\n", encoding="utf-8")
    (tmp_path / "wallpapers" / "notas.md").write_text("no es un fondo\n", encoding="utf-8")
    return tmp_path


def test_files_to_send(tmp_path: Path) -> None:
    files = theme.files(_theme(tmp_path))
    assert list(files) == ["config.json", "wallpapers/001.jpg", "wallpapers/002.PNG", "wallpapers/captions.txt"]


def test_shared_wallpapers_unless_the_profile_has_its_own(tmp_path: Path) -> None:
    (tmp_path / "compartido").mkdir()
    shared = _theme(tmp_path / "compartido")
    profile = tmp_path / "perfil"
    profile.mkdir()
    (profile / "config.json").write_text("{}", encoding="utf-8")
    files = theme.files(profile, shared)
    assert files["config.json"] == profile / "config.json"
    assert files["wallpapers/001.jpg"] == shared / "wallpapers" / "001.jpg"
    (profile / "wallpapers").mkdir()
    (profile / "wallpapers" / "propio.jpg").write_bytes(b"x")
    assert list(theme.files(profile, shared)) == ["config.json", "wallpapers/propio.jpg"]


@pytest.mark.parametrize("config", [[1, 2], "texto"])
def test_config_must_be_an_object(tmp_path: Path, config: object) -> None:
    with pytest.raises(Fail) as e:
        theme.files(_theme(tmp_path, config))
    assert e.value.code == 2


def test_bad_wallpaper_name(tmp_path: Path) -> None:
    folder = _theme(tmp_path)
    (folder / "wallpapers" / "mal nombre.jpg").write_bytes(b"x")
    with pytest.raises(Fail):
        theme.files(folder)


def test_changed_files_by_md5(tmp_path: Path) -> None:
    files = theme.files(_theme(tmp_path))
    remote = {"config.json": theme.md5(files["config.json"]), "wallpapers/001.jpg": "otra"}
    assert theme.changed(files, remote) == ["wallpapers/001.jpg", "wallpapers/002.PNG", "wallpapers/captions.txt"]


def test_put_matches_theme_sh() -> None:
    script = theme.put("wallpapers/001.jpg")
    assert "content write --uri content://com.gathin.tvhome.theme/wallpapers/001.jpg" in script
    assert "< /data/local/tmp/cyt-theme-wallpapers-001.jpg" in script
    assert "cp /data/local/tmp/cyt-theme-wallpapers-001.jpg /sdcard/Android/data/com.gathin.tvhome/files/" in script
    assert script.endswith("|| echo cyt-theme-not-written wallpapers/001.jpg")


def test_stock_home(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    assert theme.stock_home(_theme(tmp_path / "a")) == ""
    redirect = {"stock_home_redirect": " com.amazon.tv.launcher "}
    assert theme.stock_home(_theme(tmp_path / "b", redirect)) == "com.amazon.tv.launcher"
