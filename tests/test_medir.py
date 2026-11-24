"""run.py medir: mide sin tocar nada, guarda el informe y lo compara con el anterior."""

from __future__ import annotations

import re

import pytest
from conftest import FakeTv

from tvopt import cli


def test_measures_saves_and_compares(fake_tv: FakeTv, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["medir", "--perfil", "test"]) == 0
    first = capsys.readouterr().out
    assert "Memoria disponible" in first
    assert "4 núcleos" in first
    out_dir = fake_tv.profile / "backups" / "medidas"
    assert len(list(out_dir.glob("*.json"))) == 1
    assert len(list(out_dir.glob("*.md"))) == 1
    fake_tv.assert_original()
    assert cli.main(["medir", "--perfil", "test"]) == 0
    assert "Comparado con la medida anterior" in capsys.readouterr().out


def test_other_tv_is_refused(fake_tv: FakeTv) -> None:
    env = fake_tv.profile / "profile.env"
    env.write_text(
        re.sub(r"(?m)^MATCH_VALUE=.*$", "MATCH_VALUE=OTRA", env.read_text(encoding="utf-8")),
        encoding="utf-8",
        newline="\n",
    )
    assert cli.main(["medir", "--perfil", "test"]) == 3
    assert not (fake_tv.profile / "backups").exists()


def test_bad_profile_names(fake_tv: FakeTv) -> None:
    assert cli.main(["medir", "--perfil", "../etc"]) == 2
    assert cli.main(["medir", "--perfil", "no-existe"]) == 2
