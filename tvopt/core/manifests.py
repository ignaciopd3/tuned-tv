"""Manifiestos de un perfil (paquetes y ajustes) y la lista de protegidos, con las reglas de lib/profile.sh."""

from __future__ import annotations

import re
from pathlib import Path

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
            raise ProfileError(f"{path}:{n}: sobran campos: {' '.join(fields[2:])}")
        if not PKG_RE.match(pkg):
            raise ProfileError(f"{path}:{n}: nombre de paquete inválido: {pkg}")
        if method not in ("disable", "uninstall"):
            raise ProfileError(f"{path}:{n}: método inválido '{method}' (disable|uninstall)")
        if pkg in protected:
            raise ProfileError(f"{path}:{n}: {pkg} está protegido (lib/protected.list)")
        if pkg in into:
            raise ProfileError(f"{path}:{n}: {pkg} repetido")
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
            raise ProfileError(f"{path}:{n}: se espera «namespace clave valor»")
        ns, key, value = fields
        if ns not in NAMESPACES:
            raise ProfileError(f"{path}:{n}: namespace inválido: {ns}")
        if not KEY_RE.match(key):
            raise ProfileError(f"{path}:{n}: clave inválida: {key}")
        if not VAL_RE.match(value):
            raise ProfileError(f"{path}:{n}: valor con caracteres no permitidos: {value}")
        name = f"{ns} {key}"
        if name in into:
            raise ProfileError(f"{path}:{n}: {name} repetido")
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
            raise ProfileError(f"{path}:{n}: se espera «paquete OPERACIÓN modo»")
        pkg, op, mode = fields
        if not PKG_RE.match(pkg):
            raise ProfileError(f"{path}:{n}: nombre de paquete inválido: {pkg}")
        if not OP_RE.match(op):
            raise ProfileError(f"{path}:{n}: operación inválida: {op}")
        if mode not in OP_MODES:
            raise ProfileError(f"{path}:{n}: modo inválido '{mode}' ({'|'.join(OP_MODES)})")
        if pkg in protected:
            raise ProfileError(f"{path}:{n}: {pkg} está protegido (lib/protected.list)")
        name = f"{pkg} {op}"
        if name in into:
            raise ProfileError(f"{path}:{n}: {name} repetido")
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
            raise ProfileError(f"{path}:{n}: se espera «propiedad valor»")
        name, value = fields
        if not PROP_RE.match(name):
            raise ProfileError(f"{path}:{n}: solo se admiten log.tag.<etiqueta> y persist.log.tag.<etiqueta>: {name}")
        if value not in LOG_LEVELS:
            raise ProfileError(f"{path}:{n}: nivel inválido '{value}' (V, D, I, W, E, F o S)")
        if name in into:
            raise ProfileError(f"{path}:{n}: {name} repetido")
        into[name] = value
        order.append(name)
