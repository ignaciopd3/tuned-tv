"""Tele simulada por prueba (la de tests/fake_adb.sh) y el lanzador del motor."""

from __future__ import annotations

import os
import shlex
import shutil
import stat
import subprocess
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from tvopt.core.bash import find_bash

ROOT = Path(__file__).resolve().parent.parent
FAKE_ADB = ROOT / "tests" / "fake_adb.sh"
PERF_FIXTURES = ROOT / "tests" / "fixtures" / "android_perf"

PROFILE_ENV = """# perfil de test
PROFILE_NAME="Perfil de test"   # comentario final
MATCH_PROP=persist.tcl.client_type
MATCH_VALUE='TEST-CLIENT'
"""


def _write(path: Path, *lines: str) -> None:
    path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8", newline="\n")


@dataclass
class FakeTv:
    work: Path
    tv: Path
    orig: Path
    profiles: Path
    profile: Path

    def pkg_state(self, pkg: str) -> str:
        for line in (self.tv / "pkgs").read_text(encoding="utf-8").splitlines():
            name, state, _kind = line.split()
            if name == pkg:
                return state
        return ""

    def setting(self, ns: str, key: str) -> str:
        for line in (self.tv / f"settings.{ns}").read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{key}="):
                return line[len(key) + 1 :]
        return ""

    def prop(self, name: str) -> str:
        for line in (self.tv / "props").read_text(encoding="utf-8").splitlines():
            if line.startswith(f"[{name}]: ["):
                return line[len(name) + 5 : -1]
        return ""

    def appop(self, pkg: str, op: str) -> str:
        for line in (self.tv / "appops").read_text(encoding="utf-8").splitlines():
            fields = line.split()
            if fields[:2] == [pkg, op]:
                return fields[2]
        return "default"

    def runs(self) -> list[Path]:
        return sorted((self.profile / "backups").glob("2*"))

    def last_run(self) -> Path:
        return self.runs()[-1]

    def assert_original(self) -> None:
        for name in ("pkgs", "settings.system", "settings.secure", "settings.global", "appops", "props"):
            assert (self.tv / name).read_bytes() == (self.orig / name).read_bytes(), f"{name} difiere del original"


def _make_writable(root: Path) -> None:
    # Las fotos del motor quedan en solo lectura; sin esto no se pueden borrar al acabar.
    for path in root.rglob("*"):
        path.chmod(path.stat().st_mode | stat.S_IWRITE)


@pytest.fixture
def fake_tv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeTv]:
    tv, profiles = tmp_path / "tv", tmp_path / "profiles"
    profile = profiles / "test"
    tv.mkdir()
    profile.mkdir(parents=True)
    _write(
        tv / "props",
        "[persist.tcl.client_type]: [TEST-CLIENT]",
        "[ro.product.brand]: [FakeBrand]",
        "[ro.product.model]: [Fake TV]",
    )
    _write(
        tv / "pkgs",
        "com.android.systemui enabled s",
        "com.bloat.ads enabled s",
        "com.bloat.bi enabled s",
        "com.tcl.already disabled s",
        "com.user.app enabled 3",
    )
    _write(
        tv / "settings.global",
        'CustomKey_4144={"behavior":[{"intent":"#Intent;package=com.old;end"}],"keycode":4144}',
        "window_animation_scale=1.0",
    )
    _write(tv / "settings.secure", "some_list=a b'c")
    _write(tv / "settings.system")
    _write(tv / "appops")
    if PERF_FIXTURES.is_dir():
        shutil.copytree(PERF_FIXTURES, tv / "perf")
    shutil.copytree(tv, tmp_path / "tv.orig")
    (profile / "profile.env").write_text(PROFILE_ENV, encoding="utf-8", newline="\n")
    _write(
        profile / "packages.remove",
        "# nivel seguro",
        "com.bloat.ads              # anuncios",
        "com.bloat.bi   uninstall   # telemetría",
        "com.tcl.already",
        "com.not.installed",
    )
    _write(profile / "packages.caution", "com.user.app   # precaución")
    _write(
        profile / "settings.conf",
        "global window_animation_scale 0.5   # UI",
        "global transition_animation_scale 0.5",
        "secure some_list x",
    )
    _write(profile / "appops.conf", "com.user.app RUN_ANY_IN_BACKGROUND ignore   # en segundo plano no")
    _write(profile / "props.conf", "persist.log.tag.Ruido W   # registro más callado")
    _write(
        profile / "remap.conf",
        "# botón del mando",
        'global CustomKey_4144 {"behavior":[{"intent":"#Intent;package=com.new;end"}],"keycode":4144}   # → app nueva',
    )
    for key, value in {
        "FAKE_TV": tv.as_posix(),
        "TV_SERIAL": "fake:5555",
        "ADB_WAIT_SECS": "4",
        "NO_COLOR": "1",
        "LC_ALL": "C",
        "TV_OPT_PROFILES_DIR": profiles.as_posix(),
        "ADB": FAKE_ADB.as_posix(),
        "TVOPT_ADB": shlex.join([Path(find_bash()).as_posix(), FAKE_ADB.as_posix()]),
    }.items():
        monkeypatch.setenv(key, value)
    yield FakeTv(tmp_path, tv, tmp_path / "tv.orig", profiles, profile)
    _make_writable(tmp_path)


Engine = Callable[..., "subprocess.CompletedProcess[str]"]


@pytest.fixture(params=["python"])
def engine(request: pytest.FixtureRequest, fake_tv: FakeTv) -> Engine:
    """El motor que se prueba (el de Bash pasó estos mismos escenarios hasta retirarse, el 2026-11-23)."""

    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return run_engine(request.param, *args)

    return run


def run_engine(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    assert name == "python"
    return subprocess.run(
        [sys.executable, str(ROOT / "run.py"), "motor", "--profile", "test", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=os.environ.copy(),
        check=False,
    )
