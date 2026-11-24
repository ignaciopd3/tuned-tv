"""Plan de cambios y sus scripts: mismo formato que lib/apply.sh."""

from __future__ import annotations

from pathlib import Path

from tvopt.android_tv import plan

STATES = {"com.ads": "enabled", "com.bi": "enabled", "com.off": "disabled", "com.dis": "disabled"}
SETTINGS = {"global w": "1.0", "secure s": "a b'c"}


def _build(warnings: list[str] | None = None) -> plan.Plan:
    sink: list[str] = [] if warnings is None else warnings
    return plan.build(
        {
            "com.bi": "uninstall",
            "com.ads": "disable",
            "com.off": "disable",
            "com.dis": "uninstall",
            "com.no": "disable",
        },
        {"global w": "0.5", "global t": "0.5", "secure s": "x"},
        ["global w", "global t", "secure s"],
        STATES,
        SETTINGS,
        sink.append,
    )


def test_plan_lines_in_package_then_file_order() -> None:
    warnings: list[str] = []
    p = _build(warnings)
    assert p.lines == (
        "pkg com.ads disable enabled",
        "pkg com.bi uninstall enabled",
        "pkg com.dis uninstall disabled",
        "set global w 0.5 1.0",
        "set global t 0.5 __UNSET__",
        "set secure s x a b'c",
    )
    assert warnings == ["com.no no está en esta TV; se omite"]


def test_undo_is_reversed_and_restores_previous_values() -> None:
    p = _build()
    assert p.undo[0] == "tvopt_run settings put secure s 'a b'\\''c'"
    assert p.undo[1] == "tvopt_run settings delete global t"
    assert (
        "tvopt_run cmd package install-existing --user 0 com.dis; tvopt_run pm disable-user --user 0 com.dis" in p.undo
    )
    assert p.undo[-1] == "tvopt_run pm enable --user 0 com.ads"


def test_written_files_match_the_bash_engine(tmp_path: Path) -> None:
    p = _build()
    plan.write(p, tmp_path)
    assert (tmp_path / "plan.txt").read_bytes().decode() == "".join(f"{line}\n" for line in p.lines)
    script = (tmp_path / "apply.remote.sh").read_bytes().decode()
    assert script.startswith(plan.REMOTE_HELPER + "\n")
    assert "\r" not in script
    assert script.endswith("tvopt_run settings put secure s 'x'\n")


def test_empty_plan_writes_empty_files(tmp_path: Path) -> None:
    p = plan.build({}, {}, [], {}, {}, lambda _m: None)
    plan.write(p, tmp_path)
    assert (tmp_path / "plan.txt").read_text(encoding="utf-8") == ""
    assert (tmp_path / "rollback.remote.sh").read_text(encoding="utf-8") == plan.REMOTE_HELPER + "\n"
    assert plan.describe(p.lines) == ""


def test_describe_and_fields() -> None:
    text = plan.describe(("pkg com.ads disable enabled", "set global t 0.5 __UNSET__", "set secure s x a b'c"))
    assert text.startswith("\nPlan: 3 cambios\n")
    assert "  disable   com.ads" in text and "(ahora: enabled)" in text
    assert "  settings  global t: (sin definir) -> 0.5" in text
    assert "  settings  secure s: a b'c -> x" in text
    assert text.endswith("\n\n")
    assert plan.fields("set secure s x a b'c") == ("set", "secure", "s", "x", "a b'c")


def test_appops_plan_and_undo() -> None:
    warnings: list[str] = []
    p = plan.build(
        {},
        {},
        [],
        {},
        {},
        warnings.append,
        want_ops={"com.a X": "ignore", "com.b X": "ignore", "com.c X": "ignore"},
        op_order=["com.a X", "com.b X", "com.c X"],
        ops={"com.a X": "default", "com.b X": "ignore"},
    )
    assert p.lines == ("op com.a X ignore default",)
    assert p.forward == ("tvopt_run cmd appops set com.a X ignore",)
    assert p.undo == ("tvopt_run cmd appops set com.a X default",)
    assert warnings == ["com.c no está en esta TV; se omite X"]
    assert "  appops    com.a X: default -> ignore" in plan.describe(p.lines)


def test_appop_modes_from_real_output() -> None:
    from tvopt.android_tv.snapshot import parse_appop

    assert parse_appop("No operations.\nDefault mode: allow", "X") == "default"
    assert parse_appop("RUN_ANY_IN_BACKGROUND: ignore; time=+1s ago", "RUN_ANY_IN_BACKGROUND") == "ignore"
    assert parse_appop("", "X") == "absent"


def test_props_plan_and_undo() -> None:
    p = plan.build(
        {},
        {},
        [],
        {},
        {},
        lambda _m: None,
        want_props={"persist.log.tag.A": "W", "persist.log.tag.B": "W", "persist.log.tag.C": "W"},
        prop_order=["persist.log.tag.A", "persist.log.tag.B", "persist.log.tag.C"],
        props={"persist.log.tag.B": "W", "persist.log.tag.C": "I"},
    )
    assert p.lines == ("prop persist.log.tag.A W __UNSET__", "prop persist.log.tag.C W I")
    assert p.forward == ("tvopt_run setprop persist.log.tag.A W", "tvopt_run setprop persist.log.tag.C W")
    assert p.undo == ("tvopt_run setprop persist.log.tag.C I", "tvopt_run setprop persist.log.tag.A ''")
    text = plan.describe(p.lines)
    assert "  propiedad persist.log.tag.A: (sin definir) -> W" in text
    assert "  propiedad persist.log.tag.C: I -> W" in text


def test_props_from_a_snapshot(tmp_path: Path) -> None:
    from tvopt.android_tv.snapshot import load_props

    (tmp_path / "props.txt").write_text("[a.b]: [1]\n[log.tag.X]: []\n[c]: [con espacios]\n", encoding="utf-8")
    assert load_props(tmp_path) == {"a.b": "1", "c": "con espacios"}
