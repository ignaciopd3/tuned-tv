"""Las mejoras medidas de un perfil: las medidas de antes del primer cambio frente a las de después del último.

Lee lo que guarda run.py medir (backups/medidas/*.json) y las ejecuciones aplicadas del motor
(backups/<run>/rollback.sh; las deshechas llevan ROLLED_BACK). De cada grupo saca la mediana, que aguanta mejor el ruido
de una medida suelta. El resultado solo lleva cifras: los nombres de procesos podrían delatar las apps de cada uno.
Si no hay medida de antes, dice cuántos cambios ya estaban hechos y los paquetes activos de la foto ORIGINAL.
Diseño: docs/superpowers/specs/2026-11-25-metricas-en-aportaciones-design.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import median

from tvopt.android_tv import perf
from tvopt.android_tv.perf import PerfReport
from tvopt.core.i18n import tr

MINUS = "−"  # el signo menos de verdad, más legible que el guion en una tabla
_KINDS_ORDER = ("pkg", "set", "op", "prop")


class NoResults(Exception):
    """Faltan medidas o cambios para comparar; el mensaje dice qué hacer."""


@dataclass(frozen=True)
class Figures:
    available_mb: float
    swap_mb: float
    cpu_pct: float
    processes: float
    packages: float


@dataclass(frozen=True)
class Results:
    before: Figures
    after: Figures
    n_before: int
    n_after: int
    first_change: str  # fechas AAAA-MM-DD
    last_change: str
    baseline_is_first: bool  # no había medida de antes: «antes» es la primera medida, tomada tras otros cambios
    baseline_date: str
    earlier: tuple[tuple[str, int], ...] = ()  # sin medida de antes: cambios ya en vigor en la primera, por tipo
    original_enabled: int | None = None  # paquetes activos en la foto ORIGINAL, antes de cualquier cambio
    original_date: str = ""


def _date(stamp: str) -> str:
    return f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}"


def _figures(reports: list[PerfReport]) -> Figures:
    return Figures(
        available_mb=median(r.mem_available_kb / 1024 for r in reports),
        swap_mb=median((r.swap_total_kb - r.swap_free_kb) / 1024 for r in reports),
        cpu_pct=median(r.cpu_busy_pct for r in reports),
        processes=median(r.tasks for r in reports),
        packages=median(r.packages_enabled for r in reports),
    )


def _earlier_changes(backups: Path, before_stamp: str) -> tuple[tuple[str, int], ...]:
    """Los cambios en vigor de las ejecuciones anteriores a una medida, por tipo de línea de plan.txt (pkg, set…)."""
    counts: dict[str, int] = {}
    for run in sorted(backups.glob("2*")):
        if run.name[:15] >= before_stamp or not (run / "rollback.sh").is_file() or (run / "ROLLED_BACK").exists():
            continue
        plan = run / "plan.txt"
        for line in plan.read_text(encoding="utf-8").splitlines() if plan.is_file() else []:
            if line.strip():
                kind = line.split(maxsplit=1)[0]
                counts[kind] = counts.get(kind, 0) + 1
    return tuple(sorted(counts.items(), key=lambda kv: _KINDS_ORDER.index(kv[0]) if kv[0] in _KINDS_ORDER else 99))


def _original_enabled(backups: Path) -> tuple[int | None, str]:
    """Paquetes activos en la foto de antes de cualquier cambio (backups/ORIGINAL), y su fecha."""
    marker = backups / "ORIGINAL"
    if not marker.is_file():
        return None, ""
    run = marker.read_text(encoding="utf-8").strip()
    snap = backups / run / "before"
    try:
        installed = [x for x in (snap / "packages.installed").read_text(encoding="utf-8").splitlines() if x.strip()]
        disabled = [x for x in (snap / "packages.disabled").read_text(encoding="utf-8").splitlines() if x.strip()]
    except OSError:
        return None, ""
    return len(installed) - len(disabled), _date(run)


def compute(backups: Path) -> Results:
    """Antes y después de los cambios de un perfil, a partir de su carpeta backups/."""
    runs = sorted(d.name[:15] for d in backups.glob("2*") if d.is_dir() and (d / "rollback.sh").is_file())
    in_effect = sorted(
        d.name[:15] for d in backups.glob("2*") if (d / "rollback.sh").is_file() and not (d / "ROLLED_BACK").exists()
    )
    if not in_effect:
        raise NoResults(tr("No hay cambios en vigor: aplica el perfil con el motor antes de sacar resultados"))
    first, last = runs[0], in_effect[-1]
    measures = sorted(
        ((p.stem, perf.from_json(p.read_text(encoding="utf-8"))) for p in (backups / "medidas").glob("*.json")),
        key=lambda m: m[0],
    )
    before = [r for stamp, r in measures if stamp <= first]  # la del motor puede caer en el mismo segundo
    after = [r for stamp, r in measures if stamp > last]
    if not after:
        raise NoResults(
            tr(
                "No hay medidas después del último cambio ({date}): mide con run.py medir, con la tele en reposo"
                " en el inicio",
                date=_date(last),
            )
        )
    baseline_date, baseline_is_first = _date(first), not before
    earlier: tuple[tuple[str, int], ...] = ()
    original_enabled, original_date = None, ""
    if not before:
        stamp, report = measures[0]
        if stamp > last:
            raise NoResults(tr("No hay ninguna medida de antes de los cambios: la próxima vez, mide antes de aplicar"))
        before, baseline_date = [report], _date(stamp)
        earlier = _earlier_changes(backups, stamp)
        original_enabled, original_date = _original_enabled(backups)
    return Results(
        before=_figures(before),
        after=_figures(after),
        n_before=len(before),
        n_after=len(after),
        first_change=_date(first),
        last_change=_date(last),
        baseline_is_first=baseline_is_first,
        baseline_date=baseline_date,
        earlier=earlier,
        original_enabled=original_enabled,
        original_date=original_date,
    )


# Los textos del informe, en los dos idiomas: el results.md del repo va siempre en inglés y la pantalla, en el de
# quien lo usa.
_TEXT: dict[bool, dict[str, str]] = {
    True: {
        "title": "# Results · {name}",
        "intro": "Measured with `run.py measure`, idle on the home screen: median of {nb} {measures} before the"
        " first change\n({first}) and {na} after the last one ({last}).",
        "intro_first": "Measured with `run.py measure`, idle on the home screen: the first measurement ({base})"
        " against the\nmedian of {na} after the last change ({last}).",
        "not_before": "> **Not a true before.** By the first measurement, {n} changes made since {first} were"
        " already in effect\n> ({detail}), so the real gain is much larger than this table shows.",
        "not_before_vague": "> **Not a true before.** The first measurement was taken after earlier changes, so"
        " the real gain is much\n> larger than this table shows.",
        "original": "> At the very start ({date}, before any change) the TV had {orig} enabled packages; now"
        " {now} ({diff}).",
        "one": "measurement",
        "many": "measurements",
        "head": "| | Before | After | Change |",
        "available": "Available memory",
        "swap": "Swap in use",
        "cpu": "Busy CPU at idle",
        "processes": "Processes",
        "packages": "Enabled packages",
        "points": "points",
        "footer": "Generated by `run.py results --profile <tv>` from the measurements in `backups/medidas/`.",
    },
    False: {
        "title": "# Resultados · {name}",
        "intro": "Medido con `run.py medir`, en reposo en el inicio: mediana de {nb} {measures} antes del primer"
        " cambio\n({first}) y {na} después del último ({last}).",
        "intro_first": "Medido con `run.py medir`, en reposo en el inicio: la primera medida ({base}) frente a la "
        "mediana de\n{na} después del último cambio ({last}).",
        "not_before": "> **No es un antes de verdad.** En la primera medida ya estaban en vigor {n} cambios hechos"
        " desde el {first}\n> ({detail}), así que la mejora real es mucho mayor de lo que dice esta tabla.",
        "not_before_vague": "> **No es un antes de verdad.** La primera medida se tomó después de otros cambios,"
        " así que la mejora real es\n> mucho mayor de lo que dice esta tabla.",
        "original": "> Al principio del todo ({date}, antes de cualquier cambio) tenía {orig} paquetes activos;"
        " ahora, {now} ({diff}).",
        "one": "medida",
        "many": "medidas",
        "head": "| | Antes | Después | Cambio |",
        "available": "Memoria disponible",
        "swap": "Intercambio en uso",
        "cpu": "CPU ocupada en reposo",
        "processes": "Procesos",
        "packages": "Paquetes activos",
        "points": "puntos",
        "footer": "Hecho con `run.py resultados --perfil <tele>` a partir de las medidas de `backups/medidas/`.",
    },
}

# Cada tipo de línea de plan.txt, en singular y en plural.
_KIND_WORDS: dict[bool, dict[str, tuple[str, str]]] = {
    True: {
        "pkg": ("package disabled", "packages disabled"),
        "set": ("setting changed", "settings changed"),
        "op": ("app permission", "app permissions"),
        "prop": ("log level", "log levels"),
    },
    False: {
        "pkg": ("paquete deshabilitado", "paquetes deshabilitados"),
        "set": ("ajuste cambiado", "ajustes cambiados"),
        "op": ("permiso de app", "permisos de apps"),
        "prop": ("nivel de registro", "niveles de registro"),
    },
}


def _int(value: float, english: bool) -> str:
    text = f"{int(value + 0.5):,}"
    return text if english else text.replace(",", ".")


def _signed(diff: float, english: bool, unit: str = "") -> str:
    rounded = int(abs(diff) + 0.5)
    if rounded == 0:
        return f"0{unit}"
    return ("+" if diff > 0 else MINUS) + _int(rounded, english) + unit


def _pct(value: float, english: bool) -> str:
    return f"{value:.1f}%" if english else f"{value:.1f}".replace(".", ",") + " %"


def _not_before(r: Results, english: bool) -> str:
    """La nota de cuando no hay medida de antes: cuánto se había cambiado ya y, si hay foto ORIGINAL, los paquetes."""
    t, words = _TEXT[english], _KIND_WORDS[english]
    parts = [f"{n} {words[k][0] if n == 1 else words[k][1]}" for k, n in r.earlier if k in words]
    total = sum(n for _k, n in r.earlier)
    if total:
        note = t["not_before"].format(n=total, first=r.first_change, detail=", ".join(parts))
    else:
        note = t["not_before_vague"]
    if r.original_enabled is not None:
        note += "\n>\n" + t["original"].format(
            date=r.original_date,
            orig=_int(r.original_enabled, english),
            now=_int(r.after.packages, english),
            diff=_signed(r.after.packages - r.original_enabled, english),
        )
    return note


def to_markdown(r: Results, profile_name: str, english: bool) -> str:
    """El informe, en inglés (el results.md del repo) o en español."""
    t = _TEXT[english]
    b, a = r.before, r.after
    cpu_diff = a.cpu_pct - b.cpu_pct
    cpu_change = ("+" if cpu_diff > 0 else MINUS if cpu_diff < 0 else "") + f"{abs(cpu_diff):.1f}"
    if not english:
        cpu_change = cpu_change.replace(".", ",")
    if r.baseline_is_first:
        intro = t["intro_first"].format(base=r.baseline_date, na=r.n_after, last=r.last_change)
    else:
        intro = t["intro"].format(
            nb=r.n_before,
            measures=t["one"] if r.n_before == 1 else t["many"],
            first=r.first_change,
            na=r.n_after,
            last=r.last_change,
        )
    rows = [
        (
            t["available"],
            f"{_int(b.available_mb, english)} MB",
            f"{_int(a.available_mb, english)} MB",
            _signed(a.available_mb - b.available_mb, english, " MB"),
        ),
        (
            t["swap"],
            f"{_int(b.swap_mb, english)} MB",
            f"{_int(a.swap_mb, english)} MB",
            _signed(a.swap_mb - b.swap_mb, english, " MB"),
        ),
        (t["cpu"], _pct(b.cpu_pct, english), _pct(a.cpu_pct, english), f"{cpu_change} {t['points']}"),
        (
            t["processes"],
            _int(b.processes, english),
            _int(a.processes, english),
            _signed(a.processes - b.processes, english),
        ),
        (
            t["packages"],
            _int(b.packages, english),
            _int(a.packages, english),
            _signed(a.packages - b.packages, english),
        ),
    ]
    lines = [t["title"].format(name=profile_name), "", intro, ""]
    if r.baseline_is_first:
        lines += [_not_before(r, english), ""]
    lines += [t["head"], "|---|---|---|---|"]
    lines += [f"| {label} | {before} | {after} | {change} |" for label, before, after, change in rows]
    lines += ["", t["footer"], ""]
    return "\n".join(lines)
