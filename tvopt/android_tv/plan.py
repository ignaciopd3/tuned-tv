"""Plan de cambios (perfil frente a tele) y los scripts que lo aplican y lo deshacen, como lib/apply.sh."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

UNSET = "__UNSET__"
REMOTE_HELPER = 'tvopt_run() { if o=$("$@" 2>&1); then echo "OK $*"; else echo "FAIL $* :: $o"; fi; }'
_SQ = "'\\''"  # comilla simple escapada para sh


@dataclass(frozen=True)
class Plan:
    """lines es plan.txt: «pkg <paquete> <método> <estado previo>» y «set <ns> <clave> <valor> <valor previo>»."""

    lines: tuple[str, ...]
    forward: tuple[str, ...]
    undo: tuple[str, ...]  # ya en orden inverso


def build(
    want_pkgs: Mapping[str, str],
    want_sets: Mapping[str, str],
    set_order: list[str],
    states: Mapping[str, str],
    settings: Mapping[str, str],
    warn: Callable[[str], None],
    want_ops: Mapping[str, str] | None = None,
    op_order: list[str] | None = None,
    ops: Mapping[str, str] | None = None,
    want_props: Mapping[str, str] | None = None,
    prop_order: list[str] | None = None,
    props: Mapping[str, str] | None = None,
) -> Plan:
    """Lo que hay que cambiar: paquetes por orden alfabético; ajustes y permisos (appops) en el orden del fichero."""
    lines: list[str] = []
    forward: list[str] = []
    undo: list[str] = []
    for pkg in sorted(want_pkgs):
        want, cur = want_pkgs[pkg], states.get(pkg, "absent")
        if cur == "absent":
            warn(f"{pkg} no está en esta TV; se omite")
        elif want == "disable" and cur == "enabled":
            lines.append(f"pkg {pkg} disable {cur}")
            forward.append(f"tvopt_run pm disable-user --user 0 {pkg}")
            undo.append(f"tvopt_run pm enable --user 0 {pkg}")
        elif want == "uninstall" and cur in ("enabled", "disabled"):
            lines.append(f"pkg {pkg} uninstall {cur}")
            forward.append(f"tvopt_run pm uninstall -k --user 0 {pkg}")
            restore = f"tvopt_run cmd package install-existing --user 0 {pkg}"
            undo.append(f"{restore}; tvopt_run pm disable-user --user 0 {pkg}" if cur == "disabled" else restore)
    for name in set_order:
        ns, key = name.split(" ", 1)
        value, prev = want_sets[name], settings.get(name, UNSET)
        if prev == value:
            continue
        lines.append(f"set {ns} {key} {value} {prev}")
        forward.append(f"tvopt_run settings put {ns} {key} '{value}'")
        if prev == UNSET:
            undo.append(f"tvopt_run settings delete {ns} {key}")
        else:
            undo.append(f"tvopt_run settings put {ns} {key} '{prev.replace(chr(39), _SQ)}'")
    for name in op_order or []:
        pkg, op = name.split(" ", 1)
        mode, prev = (want_ops or {})[name], (ops or {}).get(name, "absent")
        if prev == "absent":
            warn(f"{pkg} no está en esta TV; se omite {op}")
        elif prev != mode:
            lines.append(f"op {pkg} {op} {mode} {prev}")
            forward.append(f"tvopt_run cmd appops set {pkg} {op} {mode}")
            undo.append(f"tvopt_run cmd appops set {pkg} {op} {prev}")
    for name in prop_order or []:
        value, prev = (want_props or {})[name], (props or {}).get(name, UNSET)
        if prev == value:
            continue
        lines.append(f"prop {name} {value} {prev}")
        forward.append(f"tvopt_run setprop {name} {value}")
        undo.append(f"tvopt_run setprop {name} {prev}" if prev != UNSET else f"tvopt_run setprop {name} ''")
    return Plan(tuple(lines), tuple(forward), tuple(reversed(undo)))


def remote_script(commands: tuple[str, ...]) -> str:
    """Script sh para la tele: cada línea informa OK/FAIL con tvopt_run (no «r»: en mksh es un alias de fc)."""
    return "".join(f"{line}\n" for line in (REMOTE_HELPER, *commands))


def write(p: Plan, run_dir: Path) -> None:
    """plan.txt, apply.remote.sh y rollback.remote.sh, con saltos de línea de Unix (los lee el sh de la tele)."""
    (run_dir / "plan.txt").write_text("".join(f"{line}\n" for line in p.lines), encoding="utf-8", newline="\n")
    (run_dir / "apply.remote.sh").write_text(remote_script(p.forward), encoding="utf-8", newline="\n")
    (run_dir / "rollback.remote.sh").write_text(remote_script(p.undo), encoding="utf-8", newline="\n")


def fields(line: str) -> tuple[str, str, str, str, str]:
    """Los cinco campos de una línea de plan.txt; el último es el resto (un valor previo puede llevar espacios)."""
    parts = line.split(maxsplit=4)
    parts += [""] * (5 - len(parts))
    return parts[0], parts[1], parts[2], parts[3], parts[4].rstrip()


def describe(lines: tuple[str, ...]) -> str:
    """El plan legible, como plan_print del motor de Bash; vacío si no hay cambios."""
    if not lines:
        return ""
    out = [f"\nPlan: {len(lines)} cambios"]
    for line in lines:
        kind, a, b, c, d = fields(line)
        if kind == "pkg":
            out.append(f"  {b:<9} {a:<50} (ahora: {c})")
        elif kind == "set":
            prev = "(sin definir)" + d[len(UNSET) :] if d.startswith(UNSET) else d
            out.append(f"  settings  {a} {b}: {prev} -> {c}")
        elif kind == "op":
            out.append(f"  appops    {a} {b}: {d} -> {c}")
        elif kind == "prop":
            out.append(f"  propiedad {a}: {'(sin definir)' if c == UNSET else c} -> {b}")
    return "\n".join(out) + "\n\n"
