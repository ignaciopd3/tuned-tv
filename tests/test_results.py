"""run.py results: las medidas de antes del primer cambio frente a las de después del último, solo en cifras."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

import pytest
from conftest import Engine, FakeTv

from tvopt import cli
from tvopt.android_tv import perf, results
from tvopt.android_tv.perf import PerfReport, ProcMem

MB = 1024


def _report(available_mb: int, swap_mb: int, cpu: float, tasks: int, enabled: int) -> PerfReport:
    return PerfReport(
        taken_at="",
        seconds=7.0,
        mem_total_kb=2723 * MB,
        mem_available_kb=available_mb * MB,
        swap_total_kb=895 * MB,
        swap_free_kb=(895 - swap_mb) * MB,
        cores=4,
        load=(1.0, 1.0, 1.0),
        cpu_busy_pct=cpu,
        uptime_h=5.0,
        tasks=tasks,
        top_cpu=(),
        top_mem=(ProcMem("com.secret.personal.app", "cached", 150 * MB, 0),),
        packages=158,
        packages_enabled=enabled,
        packages_third=18,
        data_used_pct=28,
    )


def _measure(medidas: Path, stamp: str, report: PerfReport) -> None:
    medidas.mkdir(parents=True, exist_ok=True)
    (medidas / f"{stamp}.json").write_text(perf.to_json(report), encoding="utf-8")


def _run(
    backups: Path, stamp: str, applied: bool = True, rolled_back: bool = False, plan: tuple[str, ...] = ()
) -> None:
    run = backups / stamp
    run.mkdir(parents=True)
    if applied:
        (run / "rollback.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    if rolled_back:
        (run / "ROLLED_BACK").write_text("x\n", encoding="utf-8")
    if plan:
        (run / "plan.txt").write_text("".join(f"{line}\n" for line in plan), encoding="utf-8")


def test_without_a_before_it_says_how_much_was_already_changed(backups: Path) -> None:
    m = backups / "medidas"
    _run(backups, "20261117-150000", applied=False)  # la foto ORIGINAL
    snap = backups / "20261117-150000" / "before"
    snap.mkdir(parents=True)
    (snap / "packages.installed").write_text("".join(f"com.p{i}\n" for i in range(158)), encoding="utf-8")
    (snap / "packages.disabled").write_text("com.p0\ncom.p1\ncom.p2\ncom.p3\ncom.p4\n", encoding="utf-8")
    (backups / "ORIGINAL").write_text("20261117-150000\n", encoding="utf-8")
    _run(backups, "20261117-153000", plan=("pkg a disable enabled",) * 35 + ("set global x 1 0",))
    _run(backups, "20261117-160000", rolled_back=True, plan=("pkg b disable enabled",) * 9)  # deshecho: no cuenta
    _run(backups, "20261117-170000", plan=("pkg c disable enabled", "set global y 1 0", "op com.z OP ignore allow"))
    _measure(m, "20261122-230000", _report(1271, 288, 13.1, 373, 118))
    _run(backups, "20261123-100000", plan=("pkg d disable enabled",))  # después de la primera medida: no cuenta
    _measure(m, "20261124-100000", _report(1254, 242, 6.0, 377, 113))
    r = results.compute(backups)
    assert r.earlier == (("pkg", 36), ("set", 2), ("op", 1))
    assert (r.original_enabled, r.original_date) == (153, "2026-11-17")
    en = results.to_markdown(r, "TCL", english=True)
    assert "> **Not a true before.** By the first measurement, 39 changes made since 2026-11-17 were already" in en
    assert "> (36 packages disabled, 2 settings changed, 1 app permission), so the real gain is much larger" in en
    assert "> At the very start (2026-11-17, before any change) the TV had 153 enabled packages; now 113 (−40)." in en
    es = results.to_markdown(r, "TCL", english=False)
    assert "> **No es un antes de verdad.** En la primera medida ya estaban en vigor 39 cambios hechos" in es
    assert "(36 paquetes deshabilitados, 2 ajustes cambiados, 1 permiso de app)" in es
    assert "tenía 153 paquetes activos; ahora, 113 (−40)." in es
    assert "com.p" not in en + es  # ni un nombre de paquete


@pytest.fixture
def backups(tmp_path: Path) -> Path:
    return tmp_path / "backups"


def test_medians_before_the_first_change_and_after_the_last(backups: Path) -> None:
    m = backups / "medidas"
    _measure(m, "20261101-100000", _report(1270, 290, 12.0, 380, 118))
    _measure(m, "20261101-110000", _report(1280, 280, 13.0, 382, 118))
    _measure(m, "20261101-120000", _report(1260, 300, 14.0, 384, 118))
    _run(backups, "20261101-130000", applied=False)  # una auditoría: no es un cambio
    _run(backups, "20261101-140000")
    _measure(m, "20261102-100000", _report(1300, 275, 6.0, 376, 115))  # entre cambios: no cuenta
    _run(backups, "20261102-110000")
    _run(backups, "20261103-110000", rolled_back=True)  # deshecho: no es el último en vigor
    _measure(m, "20261104-100000", _report(1340, 270, 4.0, 374, 114))
    _measure(m, "20261104-110000", _report(1350, 268, 5.0, 372, 114))
    r = results.compute(backups)
    assert (r.n_before, r.n_after) == (3, 2)
    assert r.before == results.Figures(1270, 290, 13.0, 382, 118)
    assert r.after == results.Figures(1345, 269, 4.5, 373, 114)
    assert not r.baseline_is_first
    assert (r.first_change, r.last_change) == ("2026-11-01", "2026-11-02")


def test_without_a_measurement_before_the_first_change_the_first_one_is_the_baseline(backups: Path) -> None:
    m = backups / "medidas"
    _run(backups, "20261117-150000")
    _measure(m, "20261122-230000", _report(1271, 288, 12.5, 380, 118))
    _run(backups, "20261123-100000")
    _measure(m, "20261124-100000", _report(1345, 269, 4.5, 374, 114))
    r = results.compute(backups)
    assert r.baseline_is_first
    assert (r.n_before, r.n_after) == (1, 1)
    assert r.before.available_mb == 1271


@pytest.mark.parametrize(
    ("setup", "says"),
    [
        ("nothing applied", "No hay cambios en vigor"),
        ("only rolled back", "No hay cambios en vigor"),
        ("no measure after", "No hay medidas después del último cambio"),
        ("only measures after", "No hay ninguna medida de antes"),
    ],
)
def test_refuses_without_what_it_needs(backups: Path, setup: str, says: str) -> None:
    m = backups / "medidas"
    if setup == "nothing applied":
        _measure(m, "20261101-100000", _report(1270, 290, 12.0, 380, 118))
    elif setup == "only rolled back":
        _measure(m, "20261101-100000", _report(1270, 290, 12.0, 380, 118))
        _run(backups, "20261102-100000", rolled_back=True)
        _measure(m, "20261103-100000", _report(1270, 290, 12.0, 380, 118))
    elif setup == "no measure after":
        _measure(m, "20261101-100000", _report(1270, 290, 12.0, 380, 118))
        _run(backups, "20261102-100000")
    else:
        _run(backups, "20261102-100000")
        _measure(m, "20261103-100000", _report(1270, 290, 12.0, 380, 118))
    with pytest.raises(results.NoResults, match=says):
        results.compute(backups)


def test_markdown_in_english_with_only_figures(backups: Path) -> None:
    m = backups / "medidas"
    _measure(m, "20261101-100000", _report(1271, 288, 12.5, 380, 118))
    _run(backups, "20261101-140000")
    _measure(m, "20261104-100000", _report(1345, 269, 4.5, 374, 114))
    text = results.to_markdown(results.compute(backups), "TCL C845", english=True)
    assert text == (
        "# Results · TCL C845\n"
        "\n"
        "Measured with `run.py measure`, idle on the home screen: median of 1 measurement before the first change\n"
        "(2026-11-01) and 1 after the last one (2026-11-01).\n"
        "\n"
        "| | Before | After | Change |\n"
        "|---|---|---|---|\n"
        "| Available memory | 1,271 MB | 1,345 MB | +74 MB |\n"
        "| Swap in use | 288 MB | 269 MB | −19 MB |\n"
        "| Busy CPU at idle | 12.5% | 4.5% | −8.0 points |\n"
        "| Processes | 380 | 374 | −6 |\n"
        "| Enabled packages | 118 | 114 | −4 |\n"
        "\n"
        "Generated by `run.py results --profile <tv>` from the measurements in `backups/medidas/`.\n"
    )
    assert "secret" not in text


def test_markdown_in_spanish_and_the_first_measurement_note(backups: Path) -> None:
    m = backups / "medidas"
    _run(backups, "20261117-150000")
    _measure(m, "20261122-230000", _report(1271, 288, 12.5, 380, 118))
    _run(backups, "20261123-100000")
    _measure(m, "20261124-100000", _report(1345, 269, 4.5, 374, 114))
    r = results.compute(backups)
    es = results.to_markdown(r, "TCL", english=False)
    assert "| Memoria disponible | 1.271 MB | 1.345 MB | +74 MB |" in es
    assert "| CPU ocupada en reposo | 12,5 % | 4,5 % | −8,0 puntos |" in es
    assert "la primera medida (2026-11-22)" in es
    assert "the first measurement (2026-11-22)" in results.to_markdown(r, "TCL", english=True)


def test_reads_the_json_that_run_py_medir_saves(backups: Path) -> None:
    m = backups / "medidas"
    _measure(m, "20261101-100000", _report(1271, 288, 12.5, 380, 118))
    data = json.loads((m / "20261101-100000.json").read_text(encoding="utf-8"))
    assert data["mem_available_kb"] == 1271 * MB


def test_first_real_change_measures_before_and_results_md(engine: Engine, fake_tv: FakeTv) -> None:
    medidas = fake_tv.profile / "backups" / "medidas"
    assert engine("--action", "all", "--dry-run").returncode == 0
    assert not list(medidas.glob("*.json"))  # una simulación no mide
    first = engine("--action", "all")
    assert first.returncode == 0, first.stderr
    assert "Medida de antes de los cambios guardada" in first.stderr
    jsons = sorted(medidas.glob("*.json"))
    assert len(jsons) == 1
    assert jsons[0].stem <= fake_tv.last_run().name  # antes del cambio
    assert engine("--action", "all").returncode == 0
    assert len(list(medidas.glob("*.json"))) == 1  # solo la primera vez
    # Las fechas van al segundo, y la tele simulada es tan rápida que la medida podría caer en el mismo segundo que el
    # cambio; en una tele real aplicar y comprobar tarda varios. Se espera a que pase ese segundo, como en la realidad.
    last_change = max(r.name[:15] for r in fake_tv.runs() if (r / "rollback.sh").is_file())
    while datetime.now().strftime("%Y%m%d-%H%M%S") <= last_change:
        time.sleep(0.05)
    assert cli.main(["medir", "--perfil", "test"]) == 0  # la de después, a mano
    assert cli.main(["resultados", "--perfil", "test"]) == 0
    text = (fake_tv.profile / "results.md").read_text(encoding="utf-8")
    assert text.startswith("# Results · Perfil de test\n")
    assert "| Available memory |" in text
    assert "com." not in text  # ni un nombre de proceso


def test_results_without_changes_says_what_to_do(fake_tv: FakeTv, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["resultados", "--perfil", "test"]) == 1
    assert "No hay cambios en vigor" in capsys.readouterr().err
    assert not (fake_tv.profile / "results.md").exists()
