"""Escenarios completos del motor contra la tele simulada: fijan cómo se comporta hoy (paridad)."""

from __future__ import annotations

import re
from pathlib import Path

from conftest import Engine, FakeTv, run_engine


def _append(path: Path, text: str) -> None:
    path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8", newline="\n")


def test_parser_rejects_bad_input(engine: Engine, fake_tv: FakeTv) -> None:
    remove = fake_tv.profile / "packages.remove"
    original = remove.read_text(encoding="utf-8")
    _append(remove, "com.android.systemui\n")
    assert engine("--action", "debloat", "--dry-run").returncode == 2, "paquete protegido"
    remove.write_text(original, encoding="utf-8", newline="\n")
    _append(fake_tv.profile / "settings.conf", "global clave con espacios\n")
    assert engine("--action", "optimize", "--dry-run").returncode == 2, "línea de settings inválida"
    assert not (fake_tv.profile / "backups").exists(), "un perfil inválido no debe llegar a conectar"
    fake_tv.assert_original()


def test_wrong_device_aborts(engine: Engine, fake_tv: FakeTv) -> None:
    env = fake_tv.profile / "profile.env"
    env.write_text(
        re.sub(r"(?m)^MATCH_VALUE=.*$", "MATCH_VALUE=OTRA-TV", env.read_text(encoding="utf-8")),
        encoding="utf-8",
        newline="\n",
    )
    assert engine("--action", "all").returncode == 3, "TV distinta"
    assert not (fake_tv.profile / "backups").exists(), "no debe crear backups para otra TV"
    fake_tv.assert_original()


def test_dry_run_changes_nothing(engine: Engine, fake_tv: FakeTv) -> None:
    assert engine("--action", "all", "--dry-run").returncode == 0
    fake_tv.assert_original()
    run = fake_tv.last_run()
    plan = (run / "plan.txt").read_text(encoding="utf-8")
    for line in (
        "pkg com.bloat.ads disable enabled",
        "pkg com.bloat.bi uninstall enabled",
        "set global window_animation_scale 0.5 1.0",
        "set global transition_animation_scale 0.5 __UNSET__",
        "op com.user.app RUN_ANY_IN_BACKGROUND ignore default",
        "prop persist.log.tag.Ruido W __UNSET__",
    ):
        assert line in plan
    # Los ajustes van en el orden del fichero (p. ej. el servicio de accesibilidad antes que su interruptor).
    first = re.search(r"set global (window|transition)_animation_scale", plan)
    assert first is not None and first.group(1) == "window", "orden de settings.conf"
    assert "FakeBrand / Fake TV" in (run / "audit.md").read_text(encoding="utf-8")
    assert run.name in (fake_tv.profile / "backups" / "ORIGINAL").read_text(encoding="utf-8")
    assert not (run / "rollback.sh").exists(), "dry-run no debe generar rollback.sh"
    assert "pkg com.user.app" not in plan, "packages.caution sin --include-caution"
    assert "com.tcl.already" not in plan, "paquete ya deshabilitado en el plan"
    assert engine("--action", "debloat", "--dry-run", "--include-caution").returncode == 0
    assert "pkg com.user.app disable enabled" in (fake_tv.last_run() / "plan.txt").read_text(encoding="utf-8")
    fake_tv.assert_original()


def test_apply_is_idempotent(engine: Engine, fake_tv: FakeTv) -> None:
    assert engine("--action", "all").returncode == 0
    assert fake_tv.pkg_state("com.bloat.ads") == "disabled"
    assert fake_tv.pkg_state("com.bloat.bi") == "uninstalled"
    assert fake_tv.pkg_state("com.user.app") == "enabled"
    assert fake_tv.setting("global", "window_animation_scale") == "0.5"
    assert fake_tv.setting("global", "transition_animation_scale") == "0.5"
    assert fake_tv.setting("secure", "some_list") == "x"
    assert fake_tv.appop("com.user.app", "RUN_ANY_IN_BACKGROUND") == "ignore"
    assert fake_tv.prop("persist.log.tag.Ruido") == "W"
    assert fake_tv.setting("global", "CustomKey_4144") == (
        '{"behavior":[{"intent":"#Intent;package=com.new;end"}],"keycode":4144}'
    ), "remap"
    second = engine("--action", "all")
    assert second.returncode == 0
    assert "Sin cambios" in second.stderr
    assert not (fake_tv.last_run() / "rollback.sh").exists(), "un run sin cambios no debe generar rollback.sh"


def test_rollback_all_restores_original(engine: Engine, fake_tv: FakeTv) -> None:
    assert engine("--action", "debloat").returncode == 0
    assert engine("--action", "optimize").returncode == 0
    assert fake_tv.setting("secure", "some_list") == "x"
    assert engine("--action", "rollback", "--all").returncode == 0
    fake_tv.assert_original()
    assert len(list((fake_tv.profile / "backups").glob("*/ROLLED_BACK"))) == 2, "runs revertidos"


def test_connection_drop_is_recoverable(engine: Engine, fake_tv: FakeTv) -> None:
    (fake_tv.tv / "die_after").write_text("1\n", encoding="utf-8", newline="\n")
    assert engine("--action", "all").returncode == 4, "verificación tras el corte"
    assert fake_tv.pkg_state("com.bloat.ads") == "disabled", "1.ª mutación"
    assert fake_tv.pkg_state("com.bloat.bi") == "enabled", "2.ª mutación (cortada)"
    assert (fake_tv.last_run() / "rollback.sh").exists(), "rollback.sh debe existir antes del corte"
    assert engine("--action", "rollback").returncode == 0
    fake_tv.assert_original()


def test_active_keyboard_is_protected(fake_tv: FakeTv) -> None:
    # Novedad del motor Python: el teclado que usa cada tele es intocable, sea el que sea.
    _append(fake_tv.tv / "settings.secure", "default_input_method=com.user.app/.Teclado\n")
    result = run_engine("python", "--action", "debloat", "--include-caution", "--dry-run")
    assert result.returncode == 2
    assert "teclado activo" in result.stderr
    assert not (fake_tv.profile / "backups").exists()
