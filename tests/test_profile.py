"""profile.env: mismas reglas que lib/profile.sh."""

from pathlib import Path

import pytest

from tvopt.core.profile import ProfileError, load_env


def _profile(tmp_path: Path, text: str) -> Path:
    (tmp_path / "profile.env").write_text(text, encoding="utf-8", newline="\n")
    return tmp_path


def test_quotes_and_trailing_comments(tmp_path: Path) -> None:
    env = load_env(
        _profile(
            tmp_path,
            "# c\nPROFILE_NAME=\"Perfil de test\"   # final\nMATCH_PROP=a.b\nMATCH_VALUE='TEST'\nABI=armeabi-v7a\n",
        )
    )
    assert env == {"PROFILE_NAME": "Perfil de test", "MATCH_PROP": "a.b", "MATCH_VALUE": "TEST", "ABI": "armeabi-v7a"}


def test_hash_without_space_is_part_of_the_value(tmp_path: Path) -> None:
    env = load_env(_profile(tmp_path, "MATCH_PROP=a\nMATCH_VALUE=x#y\n"))
    assert env["MATCH_VALUE"] == "x#y"


@pytest.mark.parametrize(
    "text",
    [
        "MATCH_PROP=a\n",
        "MATCH_VALUE=b\n",
        "no es clave\nMATCH_PROP=a\nMATCH_VALUE=b\n",
        "MATCH_PROP=a b\nMATCH_VALUE=b\n",
    ],
)
def test_invalid_profiles(tmp_path: Path, text: str) -> None:
    with pytest.raises(ProfileError):
        load_env(_profile(tmp_path, text))


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ProfileError):
        load_env(tmp_path)


def test_the_tcl_profile_loads() -> None:
    env = load_env(Path(__file__).resolve().parent.parent / "profiles" / "tcl-c845-mt9615")
    assert env["MATCH_PROP"] == "persist.tcl.client_type"
