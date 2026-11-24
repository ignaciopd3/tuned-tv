"""Lectura de perfiles con las mismas reglas que lib/profile.sh. Nunca se ejecuta su contenido."""

from __future__ import annotations

import re
from pathlib import Path

from tvopt.core.i18n import tr

PROFILE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")
_KEY_RE = re.compile(r"^[A-Za-z0-9_.]+$")
_LINE_RE = re.compile(r"^([A-Z][A-Z0-9_]*)=(.*)$")
_BLANK_RE = re.compile(r"^\s*(#.*)?$")
_TRAILING_COMMENT_RE = re.compile(r"\s#.*$")
_QUOTED_RE = re.compile(r'^"(.*)"$|^\'(.*)\'$')


class ProfileError(Exception):
    """Perfil inválido: código de salida 2, como en el motor de Bash."""

    exit_code = 2


def load_env(profile_dir: Path) -> dict[str, str]:
    """profile.env como diccionario: «CLAVE=valor», comillas y « # comentario» opcionales; exige MATCH_PROP/VALUE."""
    path = profile_dir / "profile.env"
    if not path.is_file():
        raise ProfileError(tr("Falta {path}", path=path))
    values: dict[str, str] = {}
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if _BLANK_RE.match(line):
            continue
        match = _LINE_RE.match(line)
        if not match:
            raise ProfileError(tr("{where}: se espera CLAVE=valor", where=f"{path}:{n}"))
        value = _TRAILING_COMMENT_RE.sub("", match.group(2), count=1).rstrip()
        quoted = _QUOTED_RE.match(value)
        if quoted:
            value = quoted.group(1) if quoted.group(1) is not None else quoted.group(2)
        values[match.group(1)] = value
    for required in ("MATCH_PROP", "MATCH_VALUE"):
        if not values.get(required):
            raise ProfileError(tr("{path}: falta {key}", path=path, key=required))
    if not _KEY_RE.match(values["MATCH_PROP"]):
        raise ProfileError(tr("{path}: MATCH_PROP inválido", path=path))
    return values
