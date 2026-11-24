"""Manifiestos de un perfil: mismas reglas y mensajes que lib/profile.sh."""

from __future__ import annotations

from pathlib import Path

import pytest

from tvopt.core.manifests import load_packages, load_protected, load_settings
from tvopt.core.profile import ProfileError

PROTECTED = frozenset({"com.android.systemui"})


def _file(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "m.txt"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def test_protected_list_ignores_comments_and_spaces(tmp_path: Path) -> None:
    path = _file(tmp_path, "# cabecera\nandroid\n  com.a.b   # motivo\n\n")
    assert load_protected(path) == frozenset({"android", "com.a.b"})


def test_packages_default_to_disable_and_cut_comments(tmp_path: Path) -> None:
    got: dict[str, str] = {}
    load_packages(_file(tmp_path, "# x\ncom.a.b   # anuncios\ncom.c.d uninstall # t\n"), PROTECTED, got)
    assert got == {"com.a.b": "disable", "com.c.d": "uninstall"}


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("com.a.b disable extra\n", "sobran campos"),
        ("no_es_paquete\n", "nombre de paquete inválido"),
        ("com.a.b borrar\n", "método inválido"),
        ("com.android.systemui\n", "está protegido"),
        ("com.a.b\ncom.a.b\n", "repetido"),
    ],
)
def test_bad_package_lines(tmp_path: Path, text: str, message: str) -> None:
    with pytest.raises(ProfileError, match=message):
        load_packages(_file(tmp_path, text), PROTECTED, {})


def test_missing_manifest_is_empty(tmp_path: Path) -> None:
    got: dict[str, str] = {}
    load_packages(tmp_path / "no.txt", PROTECTED, got)
    order: list[str] = []
    load_settings(tmp_path / "no.txt", got, order)
    assert got == {} and order == []


def test_settings_keep_file_order_and_hashes_in_values(tmp_path: Path) -> None:
    got: dict[str, str] = {}
    order: list[str] = []
    text = '# c\nglobal b 1   # motivo\nsecure a x#y\nglobal K {"i":"#Intent;end"}   # json\n'
    load_settings(_file(tmp_path, text), got, order)
    assert order == ["global b", "secure a", "global K"]
    assert got == {"global b": "1", "secure a": "x#y", "global K": '{"i":"#Intent;end"}'}


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("global clave con espacios\n", "se espera"),
        ("global solo\n", "se espera"),
        ("otro clave 1\n", "namespace inválido"),
        ("global cla-ve 1\n", "clave inválida"),
        ("global clave a'b\n", "caracteres no permitidos"),
        ("global k 1\nglobal k 2\n", "repetido"),
    ],
)
def test_bad_settings_lines(tmp_path: Path, text: str, message: str) -> None:
    with pytest.raises(ProfileError, match=message):
        load_settings(_file(tmp_path, text), {}, [])


def test_the_tcl_manifests_load() -> None:
    root = Path(__file__).resolve().parent.parent
    profile = root / "profiles" / "tcl-c845-mt9615"
    protected = load_protected(root / "lib" / "protected.list")
    pkgs: dict[str, str] = {}
    load_packages(profile / "packages.remove", protected, pkgs)
    sets: dict[str, str] = {}
    order: list[str] = []
    load_settings(profile / "settings.conf", sets, order)
    load_settings(profile / "remap.conf", sets, order)
    assert "com.google.android.katniss" in pkgs
    assert sets["global window_animation_scale"] == "0.25"


def test_appops_lines(tmp_path: Path) -> None:
    from tvopt.core.manifests import load_appops

    got: dict[str, str] = {}
    order: list[str] = []
    load_appops(_file(tmp_path, "# c\ncom.a.b RUN_ANY_IN_BACKGROUND ignore   # motivo\n"), PROTECTED, got, order)
    assert got == {"com.a.b RUN_ANY_IN_BACKGROUND": "ignore"} and order == ["com.a.b RUN_ANY_IN_BACKGROUND"]


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("com.a.b RUN_ANY_IN_BACKGROUND\n", "se espera"),
        ("com.a.b run_any ignore\n", "operación inválida"),
        ("com.a.b RUN_ANY_IN_BACKGROUND quizá\n", "modo inválido"),
        ("com.android.systemui RUN_ANY_IN_BACKGROUND ignore\n", "está protegido"),
        ("com.a.b X ignore\ncom.a.b X allow\n", "repetido"),
    ],
)
def test_bad_appops_lines(tmp_path: Path, text: str, message: str) -> None:
    from tvopt.core.manifests import load_appops

    with pytest.raises(ProfileError, match=message):
        load_appops(_file(tmp_path, text), PROTECTED, {}, [])


def test_props_lines(tmp_path: Path) -> None:
    from tvopt.core.manifests import load_props

    got: dict[str, str] = {}
    order: list[str] = []
    load_props(_file(tmp_path, "# c\npersist.log.tag.sita.soc.System W   # ruido\nlog.tag.MI3 WARN\n"), got, order)
    assert got == {"persist.log.tag.sita.soc.System": "W", "log.tag.MI3": "WARN"}
    assert order == ["persist.log.tag.sita.soc.System", "log.tag.MI3"]


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("persist.log.tag.X\n", "se espera"),
        ("ro.build.type user\n", "solo se admiten"),
        ("persist.sys.locale es\n", "solo se admiten"),
        ("persist.log.tag.X ruido\n", "nivel inválido"),
        ("log.tag.X W\nlog.tag.X E\n", "repetido"),
    ],
)
def test_bad_props_lines(tmp_path: Path, text: str, message: str) -> None:
    from tvopt.core.manifests import load_props

    with pytest.raises(ProfileError, match=message):
        load_props(_file(tmp_path, text), {}, [])


def test_settings_keys_may_have_colons(tmp_path: Path) -> None:
    # Fire OS guarda algunos ajustes con «:» en la clave.
    got: dict[str, str] = {}
    load_settings(_file(tmp_path, "secure advertisingIdApp:interestBasedAds:value 0\n"), got, [])
    assert got == {"secure advertisingIdApp:interestBasedAds:value": "0"}


def test_the_fire_tv_profile_loads() -> None:
    from tvopt.core.manifests import load_appops

    root = Path(__file__).resolve().parent.parent
    profile = root / "profiles" / "fire-tv-4k-max-aftka"
    protected = load_protected(root / "lib" / "protected.list")
    pkgs: dict[str, str] = {}
    load_packages(profile / "packages.remove", protected, pkgs)
    sets: dict[str, str] = {}
    load_settings(profile / "settings.conf", sets, [])
    ops: dict[str, str] = {}
    load_appops(profile / "appops.conf", protected, ops, [])
    assert "com.amazon.tv.acr" in pkgs and "com.amazon.aca" in pkgs
    assert "com.amazon.firebat" not in pkgs, "Prime Video se queda"
    assert sets["secure advertisingIdApp:interestBasedAds:value"] == "0"
    # WhisperLink, permitido: es el mando de la app del móvil cuando no está el mando.
    assert ops.pop("com.amazon.whisperlink.core.android RUN_ANY_IN_BACKGROUND") == "allow"
    assert all(mode == "ignore" for mode in ops.values())
