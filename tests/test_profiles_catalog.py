"""Cada perfil de profiles/ (también los que aporte la comunidad) está completo y carga sin errores."""

from pathlib import Path

import pytest

from tvopt.android_tv.launcher import theme
from tvopt.core.manifests import load_appops, load_packages, load_props, load_protected, load_settings
from tvopt.core.profile import PROFILE_ID_RE, load_env

ROOT = Path(__file__).resolve().parent.parent
PROFILES = sorted(p for p in (ROOT / "profiles").iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))


def test_there_are_profiles() -> None:
    assert PROFILES, "profiles/ sin perfiles"


@pytest.mark.parametrize("profile", PROFILES, ids=[p.name for p in PROFILES])
def test_every_profile_is_complete_and_loads(profile: Path) -> None:
    assert PROFILE_ID_RE.match(profile.name), f"nombre de carpeta no admitido: {profile.name}"
    env = load_env(profile)
    assert env.get("PROFILE_NAME"), f"{profile.name}/profile.env sin PROFILE_NAME"
    assert (profile / "README.md").is_file(), f"{profile.name}: falta README.md con las notas del modelo"
    protected = load_protected(ROOT / "lib" / "protected.list")
    load_packages(profile / "packages.remove", protected, {})
    load_packages(profile / "packages.caution", protected, {})
    load_settings(profile / "settings.conf", {}, [])
    load_settings(profile / "remap.conf", {}, [])
    load_appops(profile / "appops.conf", protected, {}, [])
    load_props(profile / "props.conf", {}, [])
    if (profile / "launcher").is_dir():
        theme.config(profile / "launcher")
