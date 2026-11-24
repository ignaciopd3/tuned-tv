"""Los mensajes en inglés y en español: todos traducidos, con los mismos huecos, y ninguno sin pasar por tr()."""

from __future__ import annotations

import subprocess
import sys

import pytest

from tests.i18n_scan import ROOT, placeholders, scan
from tvopt.android_tv import perf
from tvopt.core.i18n import language, tr
from tvopt.core.i18n_en import EN


def test_every_message_has_its_english_text() -> None:
    ids, _ = scan()
    missing = [text for text in ids if text not in EN]
    assert not missing, "Sin traducción en tvopt/core/i18n_en.py:\n" + "\n".join(map(repr, missing))


def test_no_english_text_is_left_over() -> None:
    ids, _ = scan()
    assert not [text for text in EN if text not in ids]


def test_both_languages_have_the_same_placeholders() -> None:
    wrong = {
        text: (placeholders(text), placeholders(EN[text]))
        for text in EN
        if placeholders(text) != placeholders(EN[text])
    }
    assert not wrong


def test_nothing_is_shown_without_tr() -> None:
    _, loose = scan()
    assert not loose, "Textos que se enseñan sin tr():\n" + "\n".join(loose)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("es", "es"), ("es_ES.UTF-8", "es"), ("Spanish_Spain", "es"), ("en", "en"), ("en_US", "en"), ("fr_FR", "en")],
)
def test_language_comes_from_tvopt_lang(monkeypatch: pytest.MonkeyPatch, value: str, expected: str) -> None:
    monkeypatch.setenv("TVOPT_LANG", value)
    assert language() == expected


def test_messages_and_numbers_follow_the_language(monkeypatch: pytest.MonkeyPatch) -> None:
    assert tr("Instalado {pkg}", pkg="x") == "Instalado x"
    assert perf._mb(1_234_000) == "1.205 MB"  # pyright: ignore[reportPrivateUsage]
    monkeypatch.setenv("TVOPT_LANG", "en")
    assert tr("Instalado {pkg}", pkg="x") == "Installed x"
    assert tr("un texto que no está en el catálogo") == "un texto que no está en el catálogo"
    assert perf._mb(1_234_000) == "1,205 MB"  # pyright: ignore[reportPrivateUsage]


@pytest.mark.parametrize(("lang", "says"), [("en", "measures the TV's performance"), ("es", "opciones")])
def test_run_py_help_in_each_language(lang: str, says: str) -> None:
    env = {"PATH": "", "SYSTEMROOT": "", "TVOPT_LANG": lang, "PYTHONIOENCODING": "utf-8"}
    out = subprocess.run(
        [sys.executable, "run.py", "--help"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", env=env
    )
    assert out.returncode == 0
    assert says in out.stdout
