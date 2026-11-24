"""Los mensajes en el idioma de quien usa la herramienta: español o inglés.

El código escribe cada mensaje en español, con huecos de str.format: tr("Instalado {pkg}", pkg=pkg). En inglés,
el texto sale de i18n_en.EN. El idioma es el de TVOPT_LANG si está puesta (es, en) y, si no, el del sistema; cualquier
idioma que no sea español sale en inglés. tests/test_i18n.py comprueba que cada mensaje tenga su traducción con los
mismos huecos y que no quede ninguno sin pasar por tr().
"""

from __future__ import annotations

import argparse
import locale
import os
import sys
from functools import cache

from tvopt.core.i18n_en import ARGPARSE_ES, EN


@cache
def _system_language() -> str:
    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        value = os.environ.get(var, "")
        if value and value not in ("C", "POSIX", "C.UTF-8"):
            return value
    if sys.platform == "win32":
        import ctypes

        return locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage(), "")
    return locale.getlocale()[0] or ""


def language() -> str:
    """«es» o «en»."""
    chosen = os.environ.get("TVOPT_LANG", "").strip() or _system_language()
    return "es" if chosen.lower().startswith(("es", "spanish")) else "en"


def tr(text: str, /, **values: object) -> str:
    """El mensaje en el idioma de quien lo lee, con sus huecos rellenos."""
    if language() == "en":
        text = EN.get(text, text)
    return text.format(**values) if values else text


def N_(text: str) -> str:
    """Marca un texto para traducirlo más tarde con tr() (se guarda en español, se enseña traducido)."""
    return text


def _argparse_text(message: str) -> str:
    return ARGPARSE_ES.get(message, message) if language() == "es" else message


def localize_argparse() -> None:
    """Los textos propios de argparse («usage:», «show this help message…») también en español."""
    argparse._ = _argparse_text  # type: ignore[attr-defined]  # argparse busca su _ en cada mensaje
