"""Manifiestos de un perfil (paquetes y ajustes) y la lista de protegidos, con las reglas de lib/profile.sh."""

from __future__ import annotations

import re
from pathlib import Path

from tvopt.core.i18n import tr
from tvopt.core.profile import ProfileError

PKG_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$")
KEY_RE = re.compile(r"^[A-Za-z0-9_.:]+$")  # Fire OS usa «:» en algunas claves
# Sin espacios, comilla simple ni barra invertida: el valor va entre '…' en el script de la tele.
VAL_RE = re.compile(r"^[^\s'\\]+$")
NAMESPACES = ("system", "secure", "global")
OP_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
OP_MODES = ("allow", "ignore", "deny", "default", "foreground")
# Las únicas propiedades que el shell de Android cambia sin root: el nivel del registro por etiqueta.
PROP_RE = re.compile(r"^(persist\.)?log\.tag\.[A-Za-z0-9._-]+$")
LOG_LEVELS = frozenset(
    [
        "V",
        "D",
        "I",
        "W",
        "E",
        "F",
        "S",
        "VERBOSE",
        "DEBUG",
        "INFO",
        "WARN",
        "ERROR",
        "FATAL",
        "ASSERT",
        "SUPPRESS",
        "SILENT",
    ]
)
_SETTINGS_SKIP_RE = re.compile(r"^\s*(#|$)")
_SETTINGS_COMMENT_RE = re.compile(r"\s#.*$")


def load_protected(path: Path) -> frozenset[str]:
    """Paquetes que ningún perfil puede tocar: uno por línea, con comentarios «#»."""
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        name = "".join(line.split("#", 1)[0].split())
        if name:
            names.add(name)
    return frozenset(names)


def load_packages(path: Path, protected: frozenset[str], into: dict[str, str]) -> None:
    """«paquete [disable|uninstall]  # motivo» → into[paquete] = método. Sin el fichero, nada."""
    if not path.is_file():
        return
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        fields = raw.split("#", 1)[0].split()
        if not fields:
            continue
        pkg = fields[0]
        method = fields[1] if len(fields) > 1 else "disable"
        if len(fields) > 2:
            raise ProfileError(tr("{where}: sobran campos: {extra}", where=f"{path}:{n}", extra=" ".join(fields[2:])))
        if not PKG_RE.match(pkg):
            raise ProfileError(tr("{where}: nombre de paquete inválido: {pkg}", where=f"{path}:{n}", pkg=pkg))
        if method not in ("disable", "uninstall"):
            raise ProfileError(
                tr("{where}: método inválido '{method}' (disable|uninstall)", where=f"{path}:{n}", method=method)
            )
        if pkg in protected:
            raise ProfileError(tr("{where}: {pkg} está protegido (lib/protected.list)", where=f"{path}:{n}", pkg=pkg))
        if pkg in into:
            raise ProfileError(tr("{where}: {name} repetido", where=f"{path}:{n}", name=pkg))
        into[pkg] = method


def load_settings(path: Path, into: dict[str, str], order: list[str]) -> None:
    """«namespace clave valor  # motivo» → into["ns clave"] = valor, en el orden del fichero (unos dependen de otros).

    El comentario final necesita un espacio delante: los valores (JSON, intents) pueden llevar «#».
    """
    if not path.is_file():
        return
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if _SETTINGS_SKIP_RE.match(raw):
            continue
        fields = _SETTINGS_COMMENT_RE.sub("", raw, count=1).split()
        if not fields:
            continue
        if len(fields) != 3:
            raise ProfileError(tr("{where}: se espera «namespace clave valor»", where=f"{path}:{n}"))
        ns, key, value = fields
        if ns not in NAMESPACES:
            raise ProfileError(tr("{where}: namespace inválido: {ns}", where=f"{path}:{n}", ns=ns))
        if not KEY_RE.match(key):
            raise ProfileError(tr("{where}: clave inválida: {key}", where=f"{path}:{n}", key=key))
        if not VAL_RE.match(value):
            raise ProfileError(
                tr("{where}: valor con caracteres no permitidos: {value}", where=f"{path}:{n}", value=value)
            )
        name = f"{ns} {key}"
        if name in into:
            raise ProfileError(tr("{where}: {name} repetido", where=f"{path}:{n}", name=name))
        into[name] = value
        order.append(name)


def load_appops(path: Path, protected: frozenset[str], into: dict[str, str], order: list[str]) -> None:
    """«paquete OPERACIÓN modo  # motivo» → into["paquete OP"] = modo, en el orden del fichero."""
    if not path.is_file():
        return
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        fields = raw.split("#", 1)[0].split()
        if not fields:
            continue
        if len(fields) != 3:
            raise ProfileError(tr("{where}: se espera «paquete OPERACIÓN modo»", where=f"{path}:{n}"))
        pkg, op, mode = fields
        if not PKG_RE.match(pkg):
            raise ProfileError(tr("{where}: nombre de paquete inválido: {pkg}", where=f"{path}:{n}", pkg=pkg))
        if not OP_RE.match(op):
            raise ProfileError(tr("{where}: operación inválida: {op}", where=f"{path}:{n}", op=op))
        if mode not in OP_MODES:
            raise ProfileError(
                tr(
                    "{where}: modo inválido '{mode}' ({modes})",
                    where=f"{path}:{n}",
                    mode=mode,
                    modes="|".join(OP_MODES),
                )
            )
        if pkg in protected:
            raise ProfileError(tr("{where}: {pkg} está protegido (lib/protected.list)", where=f"{path}:{n}", pkg=pkg))
        name = f"{pkg} {op}"
        if name in into:
            raise ProfileError(tr("{where}: {name} repetido", where=f"{path}:{n}", name=name))
        into[name] = mode
        order.append(name)


def load_props(path: Path, into: dict[str, str], order: list[str]) -> None:
    """«propiedad valor  # motivo» → into[propiedad] = valor. Solo log.tag.* y persist.log.tag.* (sin root)."""
    if not path.is_file():
        return
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        fields = raw.split("#", 1)[0].split()
        if not fields:
            continue
        if len(fields) != 2:
            raise ProfileError(tr("{where}: se espera «propiedad valor»", where=f"{path}:{n}"))
        name, value = fields
        if not PROP_RE.match(name):
            raise ProfileError(
                tr(
                    "{where}: solo se admiten log.tag.<etiqueta> y persist.log.tag.<etiqueta>: {name}",
                    where=f"{path}:{n}",
                    name=name,
                )
            )
        if value not in LOG_LEVELS:
            raise ProfileError(
                tr("{where}: nivel inválido '{value}' (V, D, I, W, E, F o S)", where=f"{path}:{n}", value=value)
            )
        if name in into:
            raise ProfileError(tr("{where}: {name} repetido", where=f"{path}:{n}", name=name))
        into[name] = value
        order.append(name)
