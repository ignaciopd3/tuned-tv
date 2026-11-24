"""Auditoría de solo lectura: diagnóstico Wi-Fi, rutas de APK e informe audit.md, como lib/audit.sh."""

from __future__ import annotations

import re
import stat
from pathlib import Path

from tvopt.adb.client import Adb, AdbError
from tvopt.core.log import Log

WIFI = (
    'echo "## cmd wifi status"; cmd wifi status 2>&1; echo "## cmd wifi get-country-code"; '
    'cmd wifi get-country-code 2>&1; echo "## dumpsys wifi"; dumpsys wifi 2>&1'
)
_PROP_RE = re.compile(r"^\[([^\]]+)\]: \[(.*)\]$")
_READ_ONLY = stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH


def _count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def report(run_dir: Path, profile_name: str, match_prop: str) -> str:
    """El informe Markdown a partir de before/ y audit/, igual que el del motor de Bash."""
    before = run_dir / "before"
    props: dict[str, str] = {}
    for line in (before / "props.txt").read_text(encoding="utf-8").splitlines():
        match = _PROP_RE.match(line)
        if match:
            props[match.group(1)] = match.group(2)

    def p(key: str) -> str:
        return props.get(key) or "-"

    cc = "-"
    wifi = run_dir / "audit" / "wifi.txt"
    if wifi.is_file():
        lines = wifi.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if line.startswith("## cmd wifi get-country-code"):
                cc = (lines[i + 1] if i + 1 < len(lines) else "") or "-"
                break
    n_all, n_inst = _count(before / "packages.all"), _count(before / "packages.installed")
    n_disabled, n_system = _count(before / "packages.disabled"), _count(before / "packages.system")
    n_third = _count(before / "packages.third")
    android = " / ".join(p(f"ro.build.version.{k}") for k in ("release", "sdk", "security_patch"))
    country = (
        f"wificountrycode={p('ro.boot.wificountrycode')} · persist.sys.country={p('persist.sys.country')}"
        f" · locale={p('ro.product.locale')}"
    )
    return f"""# Auditoría · {profile_name} · run {run_dir.name}

| Campo | Valor |
|---|---|
| Marca / modelo | {p("ro.product.brand")} / {p("ro.product.model")} |
| {match_prop} | {p(match_prop)} |
| Chip | {p("ro.hardware.version_id")} (plataforma {p("ro.board.platform")}) |
| Producto / dispositivo | {p("ro.product.name")} / {p("ro.product.device")} |
| Android / SDK / parche | {android} |
| Build | {p("ro.build.fingerprint")} |
| ABI | {p("ro.product.cpu.abilist")} |
| País (props) | {country} |
| Country code Wi-Fi (cmd wifi) | {cc} |

## Paquetes

| Instalados | Deshabilitados | Desinstalados (usuario 0) | Sistema | Terceros |
|---|---|---|---|---|
| {n_inst} | {n_disabled} | {n_all - n_inst} | {n_system} | {n_third} |

Ficheros: `before/` (estado completo, solo lectura) · `audit/wifi.txt` · `audit/packages.paths` (APK de cada paquete)
"""


def run(adb: Adb, run_dir: Path, profile_name: str, match_prop: str, log: Log) -> None:
    """Requiere run_dir/before (la foto ya tomada)."""
    audit_dir = run_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    try:
        wifi = adb.shell(WIFI)
    except AdbError:
        wifi = ""
        log.warn("Diagnóstico Wi-Fi incompleto (audit/wifi.txt)")
    (audit_dir / "wifi.txt").write_text(wifi, encoding="utf-8", newline="\n")
    try:
        paths = adb.shell("pm list packages -f -u")
    except AdbError:
        paths = ""
        log.warn("No se pudieron leer las rutas de APK")
    lines = [line.removeprefix("package:") for line in paths.splitlines()]
    (audit_dir / "packages.paths").write_text("".join(f"{line}\n" for line in lines), encoding="utf-8", newline="\n")
    (run_dir / "audit.md").write_text(report(run_dir, profile_name, match_prop), encoding="utf-8", newline="\n")
    for path in (*audit_dir.iterdir(), run_dir / "audit.md"):
        path.chmod(_READ_ONLY)
    log.ok(f"Auditoría: {run_dir / 'audit.md'}")
