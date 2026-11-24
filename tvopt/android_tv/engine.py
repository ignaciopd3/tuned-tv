"""Motor de tv-opt para Android TV y Fire OS: validar perfil, conectar, foto, auditoría, plan, aplicar y deshacer.

Hace lo mismo que el motor de Bash (tv-opt.sh) y escribe los mismos archivos, así que una ejecución hecha con uno
se puede deshacer con el otro. Novedad: el teclado activo de cada tele es intocable.
"""

from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from tvopt.adb.client import Adb, AdbError
from tvopt.android_tv import audit, plan, snapshot
from tvopt.core.i18n import tr
from tvopt.core.log import Fail, Log
from tvopt.core.manifests import load_appops, load_packages, load_props, load_protected, load_settings
from tvopt.core.profile import PROFILE_ID_RE, ProfileError, load_env

ROOT = Path(__file__).resolve().parent.parent.parent
PROTECTED_LIST = ROOT / "lib" / "protected.list"
RUN_RE = re.compile(r"^\d{8}-\d{6}(-\d+)?$")

USAGE = """Uso: run.py motor --profile <nombre> --action <audit|debloat|optimize|remap|all|rollback> [opciones]
  --serial <ip:puerto>  TV destino (por defecto, variable TV_SERIAL)
  --dry-run             calcula y guarda el plan sin tocar la TV
  --include-caution     incluye packages.caution en debloat/all
  --from <run>          rollback de un run concreto (nombre de su carpeta en backups/)
  --all                 rollback de todos los runs pendientes, del más reciente al más antiguo
Salida: 0 ok · 1 error · 2 uso/perfil inválido · 3 TV distinta al perfil · 4 verificación fallida"""

# El mismo rollback.sh autónomo que el motor de Bash: solo necesita adb (y bash) para deshacer a mano.
ROLLBACK_TEMPLATE = r"""#!/usr/bin/env bash
# Rollback autogenerado por tv-opt · perfil @PROFILE@ · run @RUN@
# Deshace ese run. Uso: bash rollback.sh [ip:puerto]   (solo necesita adb)
set -euo pipefail
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")"
ADB=${ADB:-adb}
SERIAL=${1:-@SERIAL@}
REMOTE=/data/local/tmp/tvopt-rollback-$$.sh
"$ADB" -s "$SERIAL" push rollback.remote.sh "$REMOTE" >/dev/null
"$ADB" -s "$SERIAL" shell "sh $REMOTE; rc=\$?; rm -f $REMOTE; exit \$rc" | tr -d "\r"
"""

# Qué carga cada acción: (paquetes, ajustes, mando, permisos por app, nivel del registro).
_WANTS = {
    "debloat": (True, False, False, False, False),
    "optimize": (False, True, False, True, True),
    "remap": (False, False, True, False, False),
    "all": (True, True, True, True, True),
    "audit": (False, False, False, False, False),
    "rollback": (False, False, False, False, False),
}


@dataclass
class Options:
    profile: str = ""
    action: str = ""
    serial: str = ""
    rb_from: str = ""
    dry_run: bool = False
    include_caution: bool = False
    rb_all: bool = False


def parse(argv: list[str]) -> Options | None:
    """Las opciones de siempre; None si se pidió la ayuda."""
    o = Options(serial=os.environ.get("TV_SERIAL", ""))
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--profile", "--action", "--serial", "--from"):
            if i + 1 >= len(argv):
                raise Fail(2, tr("Falta el valor de {arg}", arg=arg))
            value = argv[i + 1]
            if arg == "--profile":
                o.profile = value
            elif arg == "--action":
                o.action = value
            elif arg == "--serial":
                o.serial = value
            else:
                o.rb_from = value
            i += 2
            continue
        if arg == "--dry-run":
            o.dry_run = True
        elif arg == "--include-caution":
            o.include_caution = True
        elif arg == "--all":
            o.rb_all = True
        elif arg in ("-h", "--help"):
            return None
        else:
            print(tr(USAGE), file=sys.stderr)
            raise Fail(2, tr("Opción desconocida: {arg}", arg=arg))
        i += 1
    return o


def main(argv: list[str]) -> int:
    log = Log()
    try:
        return _main(argv, log)
    except Fail as e:
        log.error(str(e))
        return e.code
    except ProfileError as e:
        log.error(str(e))
        return e.exit_code


def _main(argv: list[str], log: Log) -> int:
    o = parse(argv)
    if o is None:
        print(tr(USAGE))
        return 0
    if not o.profile or not o.action:
        print(tr(USAGE), file=sys.stderr)
        raise Fail(2, tr("Faltan --profile y --action"))
    if not PROFILE_ID_RE.match(o.profile):
        raise Fail(2, tr("Nombre de perfil inválido: {profile}", profile=o.profile))
    if not o.serial:
        raise Fail(2, tr("Indica la TV con --serial <ip:puerto> o la variable TV_SERIAL"))
    profile_dir = Path(os.environ.get("TV_OPT_PROFILES_DIR") or ROOT / "profiles") / o.profile
    backups = profile_dir / "backups"
    if not profile_dir.is_dir():
        raise Fail(2, tr("No existe el perfil: {path}", path=profile_dir))

    # 1. Perfil y manifiestos, antes de tocar la red
    protected = load_protected(PROTECTED_LIST)
    env = load_env(profile_dir)
    if o.action not in _WANTS:
        print(tr(USAGE), file=sys.stderr)
        raise Fail(2, tr("Acción desconocida: {action}", action=o.action))
    with_pkgs, with_sets, with_remap, with_ops, with_props = _WANTS[o.action]
    want_pkgs: dict[str, str] = {}
    want_sets: dict[str, str] = {}
    order: list[str] = []
    want_ops: dict[str, str] = {}
    op_order: list[str] = []
    want_props: dict[str, str] = {}
    prop_order: list[str] = []
    if with_pkgs:
        load_packages(profile_dir / "packages.remove", protected, want_pkgs)
        if o.include_caution:
            load_packages(profile_dir / "packages.caution", protected, want_pkgs)
    if with_sets:
        load_settings(profile_dir / "settings.conf", want_sets, order)
    if with_remap:  # los botones del mando son ajustes, con el mismo formato
        load_settings(profile_dir / "remap.conf", want_sets, order)
    if with_ops:
        load_appops(profile_dir / "appops.conf", protected, want_ops, op_order)
    if with_props:
        load_props(profile_dir / "props.conf", want_props, prop_order)

    # 2. Conectar y confirmar que la tele es la del perfil
    try:
        adb = Adb(o.serial, warn=log.warn)
    except ValueError as e:
        raise Fail(2, str(e)) from e
    _connect(adb, log)
    _check_device(adb, env, log)
    if want_pkgs:
        _protect_active_keyboard(adb, want_pkgs)
    if o.action == "rollback":
        _rollback(o, adb, backups, log)
        return 0

    # 3. Ejecución con foto previa
    run_dir = snapshot.run_dir_new(backups)
    log.file = run_dir / "run.log"
    log.info(
        tr(
            "Run {run} · perfil {profile} · acción {action}{dry}",
            run=run_dir.name,
            profile=o.profile,
            action=o.action,
            dry=" (dry-run)" if o.dry_run else "",
        )
    )
    snapshot.take(adb, run_dir / "before", log, tuple(op_order))
    original = backups / "ORIGINAL"
    if not original.is_file():
        original.write_text(run_dir.name + "\n", encoding="utf-8", newline="\n")
        log.ok(tr("Estado ORIGINAL de la TV guardado en {path}", path=run_dir / "before"))
    if o.action in ("audit", "all"):
        audit.run(adb, run_dir, env.get("PROFILE_NAME") or o.profile, env["MATCH_PROP"], log)

    # 4. Plan → deshacer → aplicar → comprobar
    if with_pkgs or with_sets or with_remap or with_ops or with_props:
        before = run_dir / "before"
        states, settings = snapshot.load(before)
        p = plan.build(
            want_pkgs,
            want_sets,
            order,
            states,
            settings,
            log.warn,
            want_ops,
            op_order,
            snapshot.load_appops(before),
            want_props,
            prop_order,
            snapshot.load_props(before),
        )
        plan.write(p, run_dir)
        print(plan.describe(p.lines), end="", flush=True)
        if not p.lines:
            log.ok(tr("Sin cambios: la TV ya cumple el perfil"))
        elif o.dry_run:
            log.info(tr("Dry-run: plan en {path}; la TV no se ha tocado", path=run_dir / "plan.txt"))
        else:
            _write_rollback(run_dir, o.profile, o.serial, log)
            _apply(adb, run_dir, len(p.lines), o.profile, log)
    log.ok(tr("Hecho · {path}", path=run_dir))
    return 0


def _connect(adb: Adb, log: Log) -> None:
    try:
        adb.connect()
    except AdbError as e:
        raise Fail(1, str(e)) from e
    log.ok(tr("Conectado a {serial}", serial=adb.serial))


def _check_device(adb: Adb, env: dict[str, str], log: Log) -> None:
    try:
        got = adb.shell(f"getprop {env['MATCH_PROP']}").strip()
    except AdbError as e:
        raise Fail(1, str(e)) from e
    if got != env["MATCH_VALUE"]:
        raise Fail(
            3,
            tr(
                "La TV no coincide con el perfil: {prop}='{got}' (esperado '{want}')",
                prop=env["MATCH_PROP"],
                got=got,
                want=env["MATCH_VALUE"],
            ),
        )
    log.ok(tr("TV verificada: {name}", name=env.get("PROFILE_NAME") or env["MATCH_VALUE"]))


def _protect_active_keyboard(adb: Adb, want_pkgs: dict[str, str]) -> None:
    """El teclado que usa esta tele es intocable (sin él no se puede escribir nada), sea el que sea."""
    try:
        current = adb.shell("settings get secure default_input_method").strip()
    except AdbError as e:
        raise Fail(1, str(e)) from e
    keyboard = current.split("/", 1)[0]
    if keyboard in want_pkgs:
        raise Fail(2, tr("{keyboard} es el teclado activo de esta TV: no se puede quitar", keyboard=keyboard))


def _run_script(adb: Adb, script: Path) -> tuple[int, str]:
    try:
        return adb.run_script(script)
    except AdbError:
        return 1, ""


def _write_rollback(run_dir: Path, profile_id: str, serial: str, log: Log) -> None:
    text = ROLLBACK_TEMPLATE.replace("@PROFILE@", profile_id).replace("@RUN@", run_dir.name)
    path = run_dir / "rollback.sh"
    path.write_text(text.replace("@SERIAL@", serial), encoding="utf-8", newline="\n")
    path.chmod(0o755)
    log.info(tr("Rollback listo antes de tocar nada: {path}", path=path))


def _apply(adb: Adb, run_dir: Path, count: int, profile_id: str, log: Log) -> None:
    log.info(tr("Aplicando {count} cambios en un único lote…", count=count))
    started = time.perf_counter()
    rc, out = _run_script(adb, run_dir / "apply.remote.sh")
    (run_dir / "apply.out").write_text(out, encoding="utf-8", newline="\n")
    if rc != 0:
        log.warn(tr("El lote se interrumpió; reconectando para comprobar el estado real"))
        _connect(adb, log)
    for line in out.splitlines():
        if line.startswith("FAIL"):
            log.warn(f"TV: {line}")
    snapshot.take(adb, run_dir / "after", log, _plan_ops(run_dir))
    bad = verify(run_dir, "after", "apply", log)
    if bad:
        raise Fail(
            4,
            tr(
                "{bad} cambios sin aplicar. Para deshacer: run.py motor --profile {profile} --action rollback",
                bad=bad,
                profile=profile_id,
            ),
        )
    log.ok(
        tr(
            "{count} cambios aplicados y verificados ({seconds:.1f} s)",
            count=count,
            seconds=time.perf_counter() - started,
        )
    )


def _plan_ops(run_dir: Path) -> tuple[str, ...]:
    """Las operaciones (appops) que toca el plan de una ejecución, para leerlas en las fotos de después."""
    lines = (run_dir / "plan.txt").read_text(encoding="utf-8").splitlines()
    return tuple(f"{a} {b}" for kind, a, b, _c, _d in map(plan.fields, lines) if kind == "op")


def verify(run_dir: Path, snap: str, mode: str, log: Log) -> int:
    """Compara la foto snap con lo esperado según plan.txt («apply» o «rollback»); devuelve las diferencias."""
    states, settings = snapshot.load(run_dir / snap)
    ops = snapshot.load_appops(run_dir / snap)
    props = snapshot.load_props(run_dir / snap)
    bad = 0
    for line in (run_dir / "plan.txt").read_text(encoding="utf-8").splitlines():
        kind, a, b, c, d = plan.fields(line)
        if kind == "pkg":
            want = c if mode == "rollback" else ("disabled" if b == "disable" else "uninstalled")
            got = states.get(a, "absent")
        elif kind == "set":
            want = d if mode == "rollback" else c
            got = settings.get(f"{a} {b}", plan.UNSET)
        elif kind == "op":
            want = d if mode == "rollback" else c
            got = ops.get(f"{a} {b}", "absent")
        elif kind == "prop":
            want = c if mode == "rollback" else b
            got = props.get(a, plan.UNSET)
        else:
            continue
        if got != want:
            log.error(tr("Verificación: {key} = '{got}' (esperado '{want}')", key=f"{a} {b}", got=got, want=want))
            bad += 1
    return bad


def pending(backups: Path) -> list[Path]:
    """Ejecuciones con rollback.sh y sin ROLLED_BACK, de la más reciente a la más antigua."""
    runs = sorted(backups.glob("2*"), reverse=True)
    return [d for d in runs if (d / "rollback.sh").is_file() and not (d / "ROLLED_BACK").exists()]


def _rollback(o: Options, adb: Adb, backups: Path, log: Log) -> None:
    """Deshace la última ejecución pendiente (o --from, o --all) y comprueba que la tele vuelve a como estaba."""
    if o.rb_from:
        target = backups / o.rb_from
        if not RUN_RE.match(o.rb_from) or not (target / "rollback.sh").is_file():
            raise Fail(2, tr("No hay rollback para el run '{run}' en {path}", run=o.rb_from, path=backups))
        runs = [target]
    else:
        runs = pending(backups)
        if not runs:
            raise Fail(1, tr("No hay runs pendientes de revertir en {path}", path=backups))
        if not o.rb_all:
            runs = runs[:1]
    for run_dir in runs:
        log.file = run_dir / "run.log"
        log.info(tr("Revirtiendo run {run}…", run=run_dir.name))
        rc, out = _run_script(adb, run_dir / "rollback.remote.sh")
        (run_dir / "rollback.out").write_text(out, encoding="utf-8", newline="\n")
        if rc != 0:
            log.warn(tr("Rollback interrumpido; reconectando para comprobar el estado"))
            _connect(adb, log)
        snap_dir = snapshot.fresh(run_dir, f"rollback-{time.strftime('%Y%m%d-%H%M%S')}")
        snapshot.take(adb, snap_dir, log, _plan_ops(run_dir))
        bad = verify(run_dir, snap_dir.name, "rollback", log)
        if bad:
            raise Fail(
                4,
                tr(
                    "Rollback de {run} incompleto ({bad} diferencias). Es idempotente: vuelve a lanzarlo",
                    run=run_dir.name,
                    bad=bad,
                ),
            )
        (run_dir / "ROLLED_BACK").write_text(snap_dir.name.removeprefix("rollback-") + "\n", encoding="utf-8")
        log.ok(tr("Run {run} revertido y verificado", run=run_dir.name))
