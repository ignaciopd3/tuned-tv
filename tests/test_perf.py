"""Medición de rendimiento: interpretación de las salidas reales de la TCL C845."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from tvopt.android_tv import perf

FIX = Path(__file__).resolve().parent / "fixtures" / "android_perf"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8").rstrip("\n")


def _sections() -> dict[str, str]:
    return {
        "stat1": _read("stat"),
        "stat2": _read("stat.after"),
        "meminfo": _read("meminfo"),
        "loadavg": _read("loadavg"),
        "uptime": _read("uptime"),
        "cores": str(len(_read("cpuinfo").splitlines())),
        "top": _read("top.txt"),
        "pss": _read("meminfo-c.txt"),
        "df": _read("df.txt"),
        "pkgs": "158",
        "pkgs_enabled": "118",
        "pkgs_third": "18",
    }


def test_cpu_busy_from_two_stat_samples() -> None:
    assert perf.cpu_busy_pct("cpu  100 0 100 800 0 0 0 0 0 0", "cpu  150 0 150 850 50 0 0 0 0 0") == 50.0
    assert perf.cpu_busy_pct("cpu  1 1 1 1", "cpu  1 1 1 1") == 0.0


def test_top_skips_our_own_commands_and_kernel_threads() -> None:
    text = (
        "Tasks: 375 total,   1 running, 374 sleeping\n"
        "   PID USER         PR  NI VIRT  RES  SHR S[%CPU] %MEM     TIME+ ARGS\n"
        " 27758 shell        20   0 9.0M 3.6M 2.9M R 24.2   0.1   0:00.08 top -b -n 1 -m 15\n"
        " 25139 u0_a50       20   0 2.2G 172M 135M S 21.2   6.3 232:08.75 com.google.android.katniss:interactor\n"
        " 27707 root          0 -20    0    0    0 I  0.0   0.0   0:00.00 [kworker/3:0H-kblockd]\n"
        " 25139 u0_a50       20   0 2.2G 172M 135M S 21.2   6.3 232:08.75 com.google.android.katniss:interactor\n"
    )
    tasks, procs = perf.parse_top(text)
    assert tasks == 375
    assert procs == [perf.ProcCpu("com.google.android.katniss:interactor", 21.2)]


def test_pss_uses_the_second_block() -> None:
    text = (
        "proc,sys,system,853,315552,N/A,e\nproc,cached,com.a,9,1000,N/A,e\n"
        "proc,sys,system,853,138360,N/A,e\nproc,cached,com.a,9,400,N/A,e\n"
    )
    assert perf.parse_pss(text) == [
        perf.ProcMem("system", "sys", 138360, 315552),
        perf.ProcMem("com.a", "cached", 400, 1000),
    ]


def test_real_tcl_report() -> None:
    r = perf.parse(_sections(), taken_at="2026-11-22T23:40:00", seconds=6.8)
    assert r.mem_total_kb > 2_000_000
    assert 0 < r.mem_available_kb < r.mem_total_kb
    assert r.cores == 4
    assert r.tasks > 100
    assert r.packages == 158 and r.packages_enabled == 118 and r.packages_third == 18
    assert r.data_used_pct == 28
    assert 0 < r.cpu_busy_pct < 100
    assert r.top_mem and r.top_mem[0].pss_kb >= r.top_mem[-1].pss_kb
    assert all(p.name != "top" for p in r.top_cpu)
    md = perf.to_markdown(r, "TCL C845")
    assert "Memoria disponible" in md and "Lo que más memoria usa" in md


def test_json_round_trip_and_comparison() -> None:
    r = perf.parse(_sections(), taken_at="2026-11-22T23:40:00", seconds=6.8)
    back = perf.from_json(perf.to_json(r))
    assert back == r
    better = replace(
        back, mem_available_kb=back.mem_available_kb + 102_400, packages_enabled=back.packages_enabled - 10
    )
    lines = perf.compare(back, better)
    assert any("Memoria disponible" in line and "+100 MB" in line for line in lines)
    assert any("Paquetes activos" in line and "-10" in line for line in lines)
