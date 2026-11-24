"""Órdenes de tv-opt (run.py)."""

from __future__ import annotations

import argparse
import io
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from tvopt import __version__
from tvopt.adb.client import Adb, AdbError
from tvopt.android_tv import perf
from tvopt.core.i18n import language, localize_argparse, tr
from tvopt.core.profile import PROFILE_ID_RE, ProfileError, load_env

ROOT = Path(__file__).resolve().parent.parent
SHARED_LAUNCHER = ROOT / "launcher"  # parches, complementos y fondos comunes a todas las teles


def profiles_dir() -> Path:
    """Donde están los perfiles: TV_OPT_PROFILES_DIR (pruebas) o profiles/, como el motor de Bash."""
    return Path(os.environ.get("TV_OPT_PROFILES_DIR") or ROOT / "profiles")


def motor(args: list[str]) -> int:
    """El motor de Android TV y Fire OS (tvopt/android_tv/engine.py): foto, auditoría, plan, aplicar y deshacer."""
    from tvopt.android_tv import engine  # solo se carga cuando hace falta

    return engine.main(args)


def medir(profile_id: str, serial: str | None) -> int:
    """Mide el rendimiento de la tele sin tocar nada, guarda el informe y lo compara con la medida anterior."""
    if not PROFILE_ID_RE.match(profile_id):
        print(tr("Nombre de perfil inválido: {profile}", profile=profile_id), file=sys.stderr)
        return 2
    profile_dir = profiles_dir() / profile_id
    try:
        env = load_env(profile_dir)
    except ProfileError as e:
        print(e, file=sys.stderr)
        return e.exit_code
    serial = serial or os.environ.get("TV_SERIAL")
    if not serial:
        print(tr("Indica la tele con --serial <ip:puerto> o la variable TV_SERIAL"), file=sys.stderr)
        return 2
    try:
        adb = Adb(serial)
        adb.connect()
        got = adb.shell(f"getprop {env['MATCH_PROP']}").strip()
        if got != env["MATCH_VALUE"]:
            print(
                tr(
                    "La tele no coincide con el perfil: {prop}='{got}' (esperado '{want}')",
                    prop=env["MATCH_PROP"],
                    got=got,
                    want=env["MATCH_VALUE"],
                ),
                file=sys.stderr,
            )
            return 3
        start = time.perf_counter()
        sections = adb.batch(perf.PERF_SECTIONS, timeout=180)
        seconds = round(time.perf_counter() - start, 1)
    except (AdbError, ValueError) as e:
        print(e, file=sys.stderr)
        return 1
    now = datetime.now()
    report = perf.parse(sections, taken_at=now.isoformat(timespec="seconds"), seconds=seconds)
    out_dir = profile_dir / "backups" / "medidas"
    out_dir.mkdir(parents=True, exist_ok=True)
    previous = sorted(out_dir.glob("*.json"))
    stamp = now.strftime("%Y%m%d-%H%M%S")
    (out_dir / f"{stamp}.json").write_text(perf.to_json(report), encoding="utf-8")
    markdown = perf.to_markdown(report, env.get("PROFILE_NAME", profile_id))
    (out_dir / f"{stamp}.md").write_text(markdown, encoding="utf-8")
    print(markdown)
    if previous:
        before = perf.from_json(previous[-1].read_text(encoding="utf-8"))
        print(tr("Comparado con la medida anterior ({stamp}):", stamp=previous[-1].stem))
        for line in perf.compare(before, report):
            print(f"  {line}")
    print("\n" + tr("Guardado en {path}", path=f"{out_dir / stamp}.md"))
    return 0


def launcher(profile_id: str, build_only: bool, force: bool) -> int:
    """El launcher del perfil: APK (de la caché si no cambian los parches), instalación de lo que cambia y tema."""
    from tvopt.android_tv.launcher import device, source, theme
    from tvopt.core.log import Fail, Log

    log = Log()
    try:
        if not PROFILE_ID_RE.match(profile_id):
            raise Fail(2, tr("Nombre de perfil inválido: {profile}", profile=profile_id))
        launcher_dir = profiles_dir() / profile_id / "launcher"
        stock = theme.stock_home(launcher_dir)  # valida config.json antes de compilar
        src = source.Source.load(SHARED_LAUNCHER)
        cyt = Path(os.environ.get("CYT_DIR") or ROOT.parent / "cleanyourtv")
        apks = source.apks(src, cyt, profile_id, log, source.default_cache(), force=force)
        if build_only:
            log.ok(tr("Compilado (sin instalar)"))
            return 0
        serial = os.environ.get("TV_SERIAL")
        if not serial:
            raise Fail(2, tr("Define TV_SERIAL (ip:puerto)"))
        adb = Adb(serial, warn=log.warn)
        adb.connect()
        wanted = {pkg: apks[name] for name, pkg in src.addons}
        wanted[device.LAUNCHER] = apks["launcher"]
        homes = (device.LAUNCHER, stock) if stock else (device.LAUNCHER,)
        device.install(adb, wanted, {pkg for _name, pkg in src.addons}, log, force=force, homes=homes)
        theme.apply(adb, launcher_dir, cyt, log, force=force, shared=SHARED_LAUNCHER)
        if theme.config(launcher_dir).get("restore_key_services") is True:
            device.keep_alive(adb, log)
        log.ok(tr("Launcher, complementos y tema del perfil {profile} al día", profile=profile_id))
        return 0
    except Fail as e:
        log.error(str(e))
        return e.code
    except AdbError as e:
        log.error(str(e))
        return 1


def _names(spanish: str, english: str) -> tuple[str, str]:
    """Las dos formas de una opción valen siempre; la ayuda enseña primero la del idioma de quien la lee."""
    return (english, spanish) if language() == "en" else (spanish, english)


def build_parser() -> argparse.ArgumentParser:
    localize_argparse()
    parser = argparse.ArgumentParser(prog="run.py", description=tr("tv-opt: conectar, limpiar y optimizar teles"))
    parser.add_argument("--version", action="version", version=f"tv-opt {__version__}")
    sub = parser.add_subparsers(dest="orden", required=True, metavar=tr("orden"))
    sub.add_parser(
        "motor", aliases=["engine"], help=tr("el motor: foto, auditoría, plan, aplicar y deshacer (motor --help)")
    )
    measure = sub.add_parser("medir", aliases=["measure"], help=tr("mide el rendimiento de la tele sin tocar nada"))
    measure.add_argument(
        *_names("--perfil", "--profile"),
        dest="perfil",
        metavar=tr("PERFIL"),
        required=True,
        help=tr("perfil de la tele (carpeta de profiles/)"),
    )
    measure.add_argument("--serial", help=tr("ip:puerto de la tele (por defecto, la variable TV_SERIAL)"))
    lch = sub.add_parser("launcher", help=tr("compila (con caché) e instala el launcher, los complementos y el tema"))
    lch.add_argument(
        *_names("--perfil", "--profile"),
        dest="perfil",
        metavar=tr("PERFIL"),
        required=True,
        help=tr("perfil de la tele (carpeta de profiles/)"),
    )
    lch.add_argument(
        *_names("--solo-compilar", "--build-only"),
        dest="solo_compilar",
        action="store_true",
        help=tr("compila sin tocar la tele"),
    )
    lch.add_argument(
        *_names("--forzar", "--force"),
        dest="forzar",
        action="store_true",
        help=tr("recompila y reinstala aunque no haya cambios"),
    )
    return parser


def _utf8_output() -> None:
    # La consola de Windows usa cp1252 por defecto y estropea los acentos y el «·» de los informes.
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    _utf8_output()
    args = sys.argv[1:] if argv is None else argv
    if args[:1] in (["motor"], ["engine"]):
        # Todo lo que sigue es del motor, también --help: argparse no debe interpretarlo.
        return motor(args[1:])
    parsed = build_parser().parse_args(args)
    if parsed.orden in ("medir", "measure"):
        return medir(parsed.perfil, parsed.serial)
    if parsed.orden == "launcher":
        return launcher(parsed.perfil, parsed.solo_compilar, parsed.forzar)
    return 2
