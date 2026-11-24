"""Instalar el launcher y sus complementos en la tele sin molestar: solo con el inicio delante y solo lo que cambia."""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from pathlib import Path

from tvopt.adb.client import Adb, AdbError
from tvopt.core.log import Fail, Log

LAUNCHER = "com.gathin.tvhome"
_HOME = "am start -a android.intent.action.MAIN -c android.intent.category.HOME"
_OURS = f"am start -n {LAUNCHER}/.MainActivity"  # donde HOME es de otro (Fire OS)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def hash_sections(packages: list[str]) -> dict[str, str]:
    """Una lectura por paquete, todas en una ida y vuelta: la huella del APK instalado (vacía si no está)."""
    return {
        f"h{i}": f'p=$(pm path {pkg} 2>/dev/null | head -1 | cut -d: -f2); [ -n "$p" ] && sha256sum "$p"'
        for i, pkg in enumerate(packages)
    }


def parse_hashes(sections: dict[str, str], packages: list[str]) -> dict[str, str]:
    found: dict[str, str] = {}
    for i, pkg in enumerate(packages):
        words = sections.get(f"h{i}", "").split()
        if words and len(words[0]) == 64:
            found[pkg] = words[0]
    return found


def to_install(wanted: dict[str, Path], installed: dict[str, str]) -> list[str]:
    """Los paquetes cuyo APK no es el que ya tiene la tele, en orden."""
    return [pkg for pkg, apk in wanted.items() if installed.get(pkg) != sha256(apk)]


def is_home(resumed: str, homes: tuple[str, ...]) -> bool:
    """Si la actividad de delante (línea mResumedActivity) es de alguno de estos inicios."""
    return any(f" {pkg}/" in resumed for pkg in homes)


def home_front(adb: Adb, homes: tuple[str, ...] = (LAUNCHER,)) -> bool:
    try:
        # mResumedActivity en Android TV; Fire OS 7 solo escribe «ResumedActivity:».
        out = adb.shell("dumpsys activity activities | grep -m1 -E '^ *m?ResumedActivity'", timeout=30)
    except AdbError:
        return False
    return is_home(out, homes)


def wait_home(
    adb: Adb, log: Log, homes: tuple[str, ...] = (LAUNCHER,), sleep: Callable[[float], None] = time.sleep
) -> None:
    """Espera a que el inicio esté delante: instalar lo reinicia y no debe sacar al dueño de un canal o una app.

    homes: el nuestro y, donde el sistema no deja cambiar el inicio (Fire OS), el de serie que se redirige."""
    while not home_front(adb, homes):
        log.info("Esperando a que el inicio esté delante para no interrumpir lo que se está viendo…")
        sleep(15)


def install(
    adb: Adb,
    wanted: dict[str, Path],
    auto_start: set[str],
    log: Log,
    force: bool = False,
    homes: tuple[str, ...] = (LAUNCHER,),
) -> list[str]:
    """Instala los que cambian (los complementos antes que el launcher) y devuelve los instalados."""
    packages = list(wanted)
    installed = {} if force else parse_hashes(adb.batch(hash_sections(packages)), packages)
    pending = to_install(wanted, installed) if not force else packages
    if not pending:
        log.ok("La tele ya tiene estos mismos APK: no se instala nada")
        return []
    wait_home(adb, log, homes)
    for pkg in sorted(pending, key=lambda p: p == LAUNCHER):  # el launcher, el último
        ok, said = adb.install(wanted[pkg])
        if not ok:
            hint = " (¿firmado con otra clave?)" if pkg == LAUNCHER else ""
            raise Fail(1, f"Falló la instalación de {pkg}{hint}: {said}")
        # APP_AUTO_START es de TCL/MediaTek; Fire OS no lo conoce y no hace falta.
        allowed = pkg in auto_start and "permitido" in adb.shell(
            f"cmd appops set {pkg} APP_AUTO_START allow >/dev/null 2>&1 && echo permitido || echo no"
        )
        log.ok(f"Instalado {pkg}" + (" con arranque automático permitido" if allowed else ""))
        if pkg == LAUNCHER:
            keep_home_front(adb, _HOME if homes == (LAUNCHER,) else _OURS)
    return pending


def keep_alive(adb: Adb, log: Log) -> None:
    """restore_key_services donde el inicio es de otro (Fire OS). Un cierre forzado le quita al launcher la
    accesibilidad y nada lo vuelve a abrir, así que se quedaba el inicio de Amazon. GuardRevival es una escucha de
    avisos que Android vuelve a conectar tras el cierre; con permiso para escribir ajustes, repone la accesibilidad.
    Con el historial de uso, al volver sabe si el inicio de Amazon ya está delante y sale de él."""
    out = adb.shell(
        f"pm grant {LAUNCHER} android.permission.WRITE_SECURE_SETTINGS"
        f" && appops set {LAUNCHER} GET_USAGE_STATS allow"
        f" && cmd notification allow_listener {LAUNCHER}/.GuardRevival && echo listo || echo no"
    )
    if "listo" not in out:
        raise Fail(1, "No se pudo dar al launcher los permisos de ajustes e historial de uso ni activar GuardRevival")
    log.ok("El launcher vuelve solo tras un cierre forzado (GuardRevival, permisos de ajustes e historial de uso)")


def keep_home_front(adb: Adb, start: str = _HOME, sleep: Callable[[float], None] = time.sleep) -> None:
    """Instalar cierra el inicio y Android lo vuelve a cerrar un instante después («pkg removed»); entretanto se ve
    la tarea de debajo (p. ej. HDMI 2). Se reabre hasta que siga delante 3 s seguidos."""
    steady = 0
    for _ in range(20):
        if home_front(adb):
            steady += 1
            if steady >= 3:
                return
        else:
            steady = 0
            adb.shell(start)
        sleep(1)
