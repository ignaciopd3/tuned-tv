"""Rendimiento de una tele Android (también Fire OS): qué se lee, en una sola ida y vuelta, y cómo se interpreta.

Solo lectura. La CPU se mide antes que nada con dos lecturas de /proc/stat separadas un segundo, para que top y
dumpsys, que son lentos, no cuenten en la medida.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from tvopt.core.i18n import N_, language, tr

PERF_SECTIONS: dict[str, str] = {
    "stat1": "head -1 /proc/stat",
    "nap": "sleep 1",
    "stat2": "head -1 /proc/stat",
    "meminfo": "cat /proc/meminfo",
    "loadavg": "cat /proc/loadavg",
    "uptime": "cat /proc/uptime",
    "cores": "grep -c ^processor /proc/cpuinfo",
    "top": "top -b -n 1 -m 15",
    "pss": "dumpsys meminfo -c | grep ^proc,",
    "df": "df /data",
    "pkgs": "pm list packages | wc -l",
    "pkgs_enabled": "pm list packages -e | wc -l",
    "pkgs_third": "pm list packages -3 | wc -l",
}

# Nuestras propias órdenes de medida, que no son de la tele.
_OURS = frozenset({"top", "sh", "dumpsys", "grep", "cat", "head", "sleep", "wc"})

_KINDS = {
    "native": N_("nativo"),
    "sys": N_("sistema"),
    "pers": N_("persistente"),
    "persvc": N_("servicio persistente"),
    "fore": N_("en pantalla"),
    "vis": N_("visible"),
    "percept": N_("perceptible"),
    "servicea": N_("servicio"),
    "serviceb": N_("servicio"),
    "prev": N_("anterior"),
    "home": N_("inicio"),
    "cached": N_("en caché"),
}


@dataclass(frozen=True)
class ProcCpu:
    name: str
    cpu: float


@dataclass(frozen=True)
class ProcMem:
    name: str
    kind: str
    pss_kb: int
    rss_kb: int


@dataclass(frozen=True)
class PerfReport:
    taken_at: str
    seconds: float
    mem_total_kb: int
    mem_available_kb: int
    swap_total_kb: int
    swap_free_kb: int
    cores: int
    load: tuple[float, float, float]
    cpu_busy_pct: float
    uptime_h: float
    tasks: int
    top_cpu: tuple[ProcCpu, ...]
    top_mem: tuple[ProcMem, ...]
    packages: int
    packages_enabled: int
    packages_third: int
    data_used_pct: int


def _int(text: str) -> int:
    match = re.search(r"\d+", text)
    return int(match.group()) if match else 0


def _meminfo_kb(meminfo: str, key: str) -> int:
    match = re.search(rf"^{re.escape(key)}:\s+(\d+) kB", meminfo, re.MULTILINE)
    return int(match.group(1)) if match else 0


def cpu_busy_pct(stat1: str, stat2: str) -> float:
    """Porcentaje de CPU ocupada entre dos líneas «cpu …» de /proc/stat (ni idle ni iowait)."""
    a = [int(x) for x in stat1.split()[1:]]
    b = [int(x) for x in stat2.split()[1:]]
    delta = [after - before for before, after in zip(a, b, strict=False)]
    total = sum(delta)
    idle = (delta[3] if len(delta) > 3 else 0) + (delta[4] if len(delta) > 4 else 0)
    return round(100 * (total - idle) / total, 1) if total > 0 else 0.0


def parse_top(text: str, limit: int = 8) -> tuple[int, list[ProcCpu]]:
    """Tareas totales y los procesos que más CPU usan según top (sin los nuestros ni los hilos del núcleo)."""
    tasks = 0
    header: list[str] = []
    seen: set[str] = set()
    procs: list[ProcCpu] = []
    for line in text.splitlines():
        if line.startswith("Tasks:"):
            tasks = _int(line)
        elif "PID" in line and "%CPU" in line:
            header = line.replace("S[%CPU]", "S %CPU").split()
        elif header and line.strip():
            parts = line.split(None, len(header) - 1)
            if len(parts) < len(header):
                continue
            row = dict(zip(header, parts, strict=True))
            name = row.get("ARGS", row.get("NAME", "")).strip()
            pid = row.get("PID", "")
            if pid in seen or not name or name.startswith("[") or name.split()[0] in _OURS:
                continue
            seen.add(pid)
            cpu = float(row["%CPU"])
            if cpu > 0:
                procs.append(ProcCpu(name.split()[0], cpu))
    procs.sort(key=lambda p: p.cpu, reverse=True)
    return tasks, procs[:limit]


def parse_pss(text: str, limit: int = 10) -> list[ProcMem]:
    """Los procesos que más memoria usan según dumpsys meminfo -c.

    Android 11 da primero un bloque de RSS y después otro de PSS con los mismos procesos; se ordena por PSS, que
    reparte la memoria compartida. Si solo hay un bloque (Android antiguo), es el de PSS.
    """
    first: dict[str, tuple[str, str, int]] = {}
    mem: dict[str, ProcMem] = {}
    for line in text.splitlines():
        fields = line.split(",")
        if len(fields) < 5 or fields[0] != "proc" or not fields[4].isdigit():
            continue
        kind, name, pid, value = fields[1], fields[2], fields[3], int(fields[4])
        if name in _OURS:
            continue
        if pid not in first:
            first[pid] = (kind, name, value)
        else:
            mem[pid] = ProcMem(name, kind, value, first[pid][2])
    if not mem:
        mem = {pid: ProcMem(name, kind, value, 0) for pid, (kind, name, value) in first.items()}
    return sorted(mem.values(), key=lambda p: p.pss_kb, reverse=True)[:limit]


def parse(sections: dict[str, str], taken_at: str, seconds: float) -> PerfReport:
    """El informe a partir de la salida de PERF_SECTIONS."""
    meminfo = sections.get("meminfo", "")
    load = [float(x) for x in sections.get("loadavg", "").split()[:3]]
    tasks, top_cpu = parse_top(sections.get("top", ""))
    df_lines = [line for line in sections.get("df", "").splitlines() if line.strip()]
    used = re.search(r"(\d+)%", df_lines[-1]) if df_lines else None
    uptime = sections.get("uptime", "").split()
    return PerfReport(
        taken_at=taken_at,
        seconds=seconds,
        mem_total_kb=_meminfo_kb(meminfo, "MemTotal"),
        mem_available_kb=_meminfo_kb(meminfo, "MemAvailable"),
        swap_total_kb=_meminfo_kb(meminfo, "SwapTotal"),
        swap_free_kb=_meminfo_kb(meminfo, "SwapFree"),
        cores=_int(sections.get("cores", "")),
        load=(load[0], load[1], load[2]) if len(load) == 3 else (0.0, 0.0, 0.0),
        cpu_busy_pct=cpu_busy_pct(sections.get("stat1", "cpu"), sections.get("stat2", "cpu")),
        uptime_h=round(float(uptime[0]) / 3600, 1) if uptime else 0.0,
        tasks=tasks,
        top_cpu=tuple(top_cpu),
        top_mem=tuple(parse_pss(sections.get("pss", ""))),
        packages=_int(sections.get("pkgs", "")),
        packages_enabled=_int(sections.get("pkgs_enabled", "")),
        packages_third=_int(sections.get("pkgs_third", "")),
        data_used_pct=int(used.group(1)) if used else 0,
    )


def _mb(kb: int) -> str:
    text = f"{kb // 1024:,} MB"
    return text if language() == "en" else text.replace(",", ".")


def to_markdown(r: PerfReport, profile_name: str) -> str:
    """Informe legible: memoria, CPU, procesos y paquetes."""
    swap_used = r.swap_total_kb - r.swap_free_kb
    lines = [
        tr("# Rendimiento · {profile} · {taken}", profile=profile_name, taken=r.taken_at),
        "",
        tr("| Medida | Valor |"),
        "|---|---|",
        tr(
            "| Memoria disponible | {available} de {total} ({pct} %) |",
            available=_mb(r.mem_available_kb),
            total=_mb(r.mem_total_kb),
            pct=100 * r.mem_available_kb // max(r.mem_total_kb, 1),
        ),
        tr("| Memoria de intercambio en uso | {used} de {total} |", used=_mb(swap_used), total=_mb(r.swap_total_kb)),
        tr("| CPU ocupada (1 s) | {pct} % de {cores} núcleos |", pct=r.cpu_busy_pct, cores=r.cores),
        tr("| Carga media (1, 5 y 15 min) | {a} · {b} · {c} |", a=r.load[0], b=r.load[1], c=r.load[2]),
        tr("| Procesos | {tasks} |", tasks=r.tasks),
        tr(
            "| Paquetes activos | {enabled} de {total} ({third} de terceros) |",
            enabled=r.packages_enabled,
            total=r.packages,
            third=r.packages_third,
        ),
        tr("| Almacenamiento usado | {pct} % |", pct=r.data_used_pct),
        tr("| Encendida desde hace | {hours} h |", hours=r.uptime_h),
        "",
        tr("## Lo que más CPU usa"),
        "",
        tr("| Proceso | CPU |"),
        "|---|---|",
        *(tr("| {name} | {pct} % |", name=p.name, pct=p.cpu) for p in r.top_cpu),
        "",
        tr("## Lo que más memoria usa"),
        "",
        tr("| Proceso | Estado | Memoria (PSS) |"),
        "|---|---|---|",
        *(f"| {p.name} | {tr(_KINDS[p.kind]) if p.kind in _KINDS else p.kind} | {_mb(p.pss_kb)} |" for p in r.top_mem),
        "",
        tr("Medido en {seconds} s, solo leyendo.", seconds=r.seconds),
        "",
    ]
    return "\n".join(lines)


def to_json(r: PerfReport) -> str:
    return json.dumps(asdict(r), ensure_ascii=False, indent=2)


def from_json(text: str) -> PerfReport:
    data: dict[str, Any] = json.loads(text)
    data["load"] = tuple(data["load"])
    data["top_cpu"] = tuple(ProcCpu(**p) for p in data["top_cpu"])
    data["top_mem"] = tuple(ProcMem(**p) for p in data["top_mem"])
    return PerfReport(**data)


def compare(before: PerfReport, after: PerfReport) -> list[str]:
    """Lo que ha cambiado entre dos medidas, en las cifras que importan."""

    def signed(value: int, unit: str = "") -> str:
        return f"{value:+d}{unit}"

    swap_before = before.swap_total_kb - before.swap_free_kb
    swap_after = after.swap_total_kb - after.swap_free_kb
    return [
        tr(
            "Memoria disponible: {before} → {after} ({diff})",
            before=_mb(before.mem_available_kb),
            after=_mb(after.mem_available_kb),
            diff=signed((after.mem_available_kb - before.mem_available_kb) // 1024, " MB"),
        ),
        tr(
            "Intercambio en uso: {before} → {after} ({diff})",
            before=_mb(swap_before),
            after=_mb(swap_after),
            diff=signed((swap_after - swap_before) // 1024, " MB"),
        ),
        tr("CPU ocupada: {before} % → {after} %", before=before.cpu_busy_pct, after=after.cpu_busy_pct),
        tr(
            "Procesos: {before} → {after} ({diff})",
            before=before.tasks,
            after=after.tasks,
            diff=signed(after.tasks - before.tasks),
        ),
        tr(
            "Paquetes activos: {before} → {after} ({diff})",
            before=before.packages_enabled,
            after=after.packages_enabled,
            diff=signed(after.packages_enabled - before.packages_enabled),
        ),
    ]
