"""El tema del perfil (config.json, fondos y créditos) en el launcher de la tele, como tools/theme.sh de cleanyourtv.

Diferencias por rendimiento:
- los archivos van con adb push (Android 7 o superior) en vez de en trozos base64;
- solo se envían los que cambian (por md5);
- si no cambia nada, ni se escribe ni se reinicia el inicio.

La escritura en la tele es la misma: el proveedor del launcher, o una copia a su carpeta si no lo admite, con
comprobación de tamaño.
"""

from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import cast

from tvopt.adb.client import Adb
from tvopt.core.log import Fail, Log

PKG = "com.gathin.tvhome"
DIR = f"/sdcard/Android/data/{PKG}/files"
URI = f"content://{PKG}.theme"
TMP = "/data/local/tmp/cyt-theme"
NOT_WRITTEN = "cyt-theme-not-written"
_IMAGE_RE = re.compile(r"\.(jpe?g|png|webp)$", re.IGNORECASE)
_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def stage(name: str) -> str:
    return f"{TMP}-{name.replace('/', '-')}"


def config(theme_dir: Path) -> dict[str, object]:
    """config.json del perfil, validado: un objeto JSON de claves del tema."""
    path = theme_dir / "config.json"
    if not path.is_file():
        raise Fail(2, f"No hay config.json en {theme_dir}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except ValueError as e:
        raise Fail(2, f"{path} no es JSON válido") from e
    if not isinstance(data, dict):
        raise Fail(2, f"{path} no es un objeto JSON de claves del tema: el launcher lo ignoraría")
    return cast("dict[str, object]", data)


def stock_home(theme_dir: Path) -> str:
    """El inicio de serie que el launcher redirige al suyo (stock_home_redirect), o «»."""
    value = config(theme_dir).get("stock_home_redirect", "")
    return value.strip() if isinstance(value, str) else ""


def files(theme_dir: Path, shared: Path | None = None) -> dict[str, Path]:
    """Lo que se envía, por nombre en la tele: config.json, wallpaper.jpg, wallpapers/* y sus créditos.

    Los fondos son los del perfil si tiene wallpapers/; si no, los compartidos (shared/wallpapers).
    """
    config(theme_dir)
    found: dict[str, Path] = {"config.json": theme_dir / "config.json"}
    if (theme_dir / "wallpaper.jpg").is_file():
        found["wallpaper.jpg"] = theme_dir / "wallpaper.jpg"
    walls = theme_dir / "wallpapers"
    if not walls.is_dir() and shared is not None:
        walls = shared / "wallpapers"
    if walls.is_dir():
        for image in sorted(walls.iterdir()):
            if image.is_file() and _IMAGE_RE.search(image.name):
                if not _NAME_RE.match(image.name) or ".." in image.name:
                    raise Fail(2, f"Nombre de fondo no admitido: {image.name} (letras, cifras, «.», «_» y «-»)")
                found[f"wallpapers/{image.name}"] = image
        if (walls / "captions.txt").is_file():
            found["wallpapers/captions.txt"] = walls / "captions.txt"
    return found


def remote_sections(names: list[str]) -> dict[str, str]:
    """El md5 de lo que tiene el launcher, por el proveedor (o su carpeta), en una sola ida y vuelta."""
    return {
        f"m{i}": f"(content read --uri {URI}/{name} 2>/dev/null || cat {DIR}/{name} 2>/dev/null) | md5sum"
        for i, name in enumerate(names)
    }


def parse_remote(sections: dict[str, str], names: list[str]) -> dict[str, str]:
    empty = hashlib.md5(b"").hexdigest()
    found: dict[str, str] = {}
    for i, name in enumerate(names):
        words = sections.get(f"m{i}", "").split()
        if words and len(words[0]) == 32 and words[0] != empty:
            found[name] = words[0]
    return found


def changed(local: dict[str, Path], remote: dict[str, str]) -> list[str]:
    return [name for name, path in local.items() if remote.get(name) != md5(path)]


def put(name: str) -> str:
    """La escritura de tools/theme.sh para un archivo ya subido a su ruta temporal: proveedor o copia, y tamaño."""
    s = stage(name)
    d = f"{DIR}/{name}"
    return (
        f'rm -f {d} 2>/dev/null; w=; {{ o=$(content write --uri {URI}/{name} < {s} 2>&1) && case "$o" in '
        f"*'Unsupported operation'*|*'Error while accessing provider'*) false ;; esac && w=1; }} || "
        f"{{ mkdir -p {posixpath.dirname(d)} 2>/dev/null; cp {s} {d} 2>/dev/null && w=1; }}; "
        f's=$(wc -c 2>/dev/null < {s}); rm -f {s}; [ -n "$w" ] && {{ {{ [ -e {d} ] && [ "$(wc -c < {d})" = "$s" ]; }} '
        f'|| [ "$(content read --uri {URI}/{name} 2>/dev/null | wc -c)" = "$s" ]; }} || echo {NOT_WRITTEN} {name}'
    )


def delete(name: str) -> str:
    return f"rm -f {DIR}/{name} 2>/dev/null; content delete --uri {URI}/{name} 2>/dev/null"


def apply(adb: Adb, theme_dir: Path, cyt: Path, log: Log, force: bool = False, shared: Path | None = None) -> bool:
    """Pone el tema; devuelve si cambió algo (y por tanto se reinició el inicio). force: todo, aunque esté igual."""
    local = files(theme_dir, shared)
    names = list(local)
    pending = names if force else changed(local, parse_remote(adb.batch(remote_sections(names)), names))
    if not pending:
        log.ok("El tema de la tele ya es este: no se envía nada")
        return False
    adb.shell(f"mkdir -p {DIR}")
    for name in pending:
        if not adb.push(local[name], stage(name)):
            raise Fail(1, f"No se pudo subir {name}")
    script = "; ".join(put(name) for name in pending)
    revision = uuid.uuid4().hex
    script += f"; printf '%s' '{revision}' > {stage('theme_revision')}; {put('theme_revision')}"
    out = adb.shell(script, timeout=300)
    failed = [line for line in out.splitlines() if line.startswith(NOT_WRITTEN)]
    if failed:
        raise Fail(1, f"La tele no aceptó {', '.join(f.split(' ', 1)[1] for f in failed)}")
    log.ok(f"Tema enviado: {len(pending)} de {len(names)} archivos (los demás ya estaban)")
    restart_home(adb, cyt, log)
    return True


def restart_home(adb: Adb, cyt: Path, log: Log) -> None:
    """Reinicia el inicio con theme_restart.py de cleanyourtv, que vuelve a enganchar los ayudantes del mando."""
    tools = cyt / "tools"
    python = tools / "venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not python.is_file():
        raise Fail(1, f"Falta el entorno de cleanyourtv ({python}): el tema sale al reiniciar el inicio")
    env = {**os.environ, "TV_HOST": adb.serial.split(":")[0], "TV_ADB_BINARY": adb.command[0]}
    result = subprocess.run([str(python), "-I", "theme_restart.py"], cwd=tools, env=env, check=False)
    if result.returncode != 0:
        raise Fail(1, "El inicio no se reinició tras el tema: lo cogerá la próxima vez que arranque")
    log.ok("Inicio reiniciado con el tema")
