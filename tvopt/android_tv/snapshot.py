"""Foto del estado de la tele en una sola ida y vuelta, y las carpetas de cada ejecución, como lib/snapshot.sh."""

from __future__ import annotations

import re
import stat
import time
from pathlib import Path

from tvopt.adb.client import Adb, AdbError
from tvopt.core.log import Fail, Log

SECTIONS: dict[str, str] = {
    "props.txt": "getprop",
    "packages.all": "pm list packages -u",
    "packages.installed": "pm list packages",
    "packages.disabled": "pm list packages -d",
    "packages.system": "pm list packages -s",
    "packages.third": "pm list packages -3",
    "settings.system": "settings list system",
    "settings.secure": "settings list secure",
    "settings.global": "settings list global",
}
NAMESPACES = ("system", "secure", "global")
_READ_ONLY = stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH


def run_dir_new(backups: Path) -> Path:
    """backups/<AAAAMMDD-HHMMSS>[-n], nueva y vacía."""
    backups.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    for n in range(100):
        candidate = backups / (stamp if n == 0 else f"{stamp}-{n}")
        try:
            candidate.mkdir()
        except FileExistsError:
            continue
        return candidate
    raise Fail(1, f"No se pudo crear un directorio de run en {backups}")


def fresh(parent: Path, base: str) -> Path:
    """parent/base, o parent/base-n si ya existe: una foto nunca escribe sobre otra (quedan en solo lectura)."""
    candidate, n = parent / base, 0
    while candidate.exists():
        n += 1
        candidate = parent / f"{base}-{n}"
    return candidate


def parse_appop(text: str, op: str) -> str:
    """El modo de una operación según «cmd appops get»: el puesto, «default» si no hay ninguno, «absent» sin app."""
    match = re.search(rf"^{re.escape(op)}: (\w+)", text, re.MULTILINE)
    if match:
        return match.group(1)
    return "default" if "No operations" in text else "absent"


def take(adb: Adb, snap_dir: Path, log: Log, ops: tuple[str, ...] = ()) -> None:
    """Guarda el estado completo de la tele en snap_dir (y el modo de las operaciones ops), en solo lectura."""
    started = time.perf_counter()
    op_sections = {f"appops.{i}": f"cmd appops get {name}" for i, name in enumerate(ops)}
    try:
        sections = adb.batch({**SECTIONS, **op_sections})
    except AdbError as e:
        raise Fail(1, "No se pudo leer el estado de la TV (¿conexión caída?)") from e
    missing = [name for name in SECTIONS if name not in sections]
    if missing:
        raise Fail(1, f"Snapshot incompleto en {snap_dir}: falta {missing[0]}")
    snap_dir.mkdir(parents=True, exist_ok=True)
    for name in SECTIONS:
        lines = sections[name].splitlines()
        if name.startswith("packages."):
            lines = [line.removeprefix("package:") for line in lines]
        path = snap_dir / name
        path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8", newline="\n")
        path.chmod(_READ_ONLY)
    if ops:
        modes = [parse_appop(sections.get(f"appops.{i}", ""), name.split()[1]) for i, name in enumerate(ops)]
        path = snap_dir / "appops.txt"
        text = "".join(f"{name} {mode}\n" for name, mode in zip(ops, modes, strict=True))
        path.write_text(text, encoding="utf-8", newline="\n")
        path.chmod(_READ_ONLY)
    log.info(f"Snapshot guardado: {snap_dir} ({time.perf_counter() - started:.1f} s)")


def load(snap_dir: Path) -> tuple[dict[str, str], dict[str, str]]:
    """(estado de cada paquete: enabled|disabled|uninstalled, ajustes «ns clave» → valor, sin los «null»)."""
    states: dict[str, str] = {}
    for name, state in (
        ("packages.all", "uninstalled"),
        ("packages.installed", "enabled"),
        ("packages.disabled", "disabled"),
    ):
        for line in (snap_dir / name).read_text(encoding="utf-8").splitlines():
            if line:
                states[line] = state
    settings: dict[str, str] = {}
    for ns in NAMESPACES:
        for line in (snap_dir / f"settings.{ns}").read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and value != "null":
                settings[f"{ns} {key}"] = value
    return states, settings


def load_appops(snap_dir: Path) -> dict[str, str]:
    """«paquete OP» → modo, de appops.txt; vacío en las fotos que no lo tienen."""
    path = snap_dir / "appops.txt"
    if not path.is_file():
        return {}
    modes: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 3:
            modes[f"{parts[0]} {parts[1]}"] = parts[2]
    return modes


_PROP_RE = re.compile(r"^\[([^\]]+)\]: \[(.*)\]$")


def load_props(snap_dir: Path) -> dict[str, str]:
    """Las propiedades de props.txt; las vacías no cuentan (es como si no estuvieran)."""
    props: dict[str, str] = {}
    for line in (snap_dir / "props.txt").read_text(encoding="utf-8").splitlines():
        match = _PROP_RE.match(line)
        if match and match.group(2):
            props[match.group(1)] = match.group(2)
    return props
