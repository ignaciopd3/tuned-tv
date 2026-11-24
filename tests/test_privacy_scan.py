"""El detector de datos privados que usan el CI de las PR y la publicación del repo privado."""

import re
from pathlib import Path

from tvopt.core import privacy

GH = "gh" + "p_" + "a" * 36  # por partes, para que el detector no salte con este archivo
KEY = "-----BEGIN RSA " + "PRIVATE KEY-----"
MAIL = "alguien" + "@empresa.es"


def _rules(found: list[privacy.Finding]) -> list[str]:
    return [f.rule for f in found]


def test_clean_files_pass() -> None:
    files = {"README.md": b"Tuned TV\nautor 210892957+ignaciopd3@users.noreply.github.com\n", "tool.py": b"x = 1\n"}
    assert privacy.scan(files) == []


def test_secrets_are_found_anywhere() -> None:
    found = privacy.scan({"tvopt/a.py": f"token = '{GH}'\n{KEY}\n".encode()})
    assert _rules(found) == ["token de GitHub", "clave privada"]
    assert [f.line for f in found] == [1, 2]


def test_emails_except_noreply_and_examples() -> None:
    text = f"a@users.noreply.github.com b@example.com noreply@anthropic.com {MAIL}\n".encode()
    found = privacy.scan({"docs/x.md": text})
    assert [(f.rule, f.text) for f in found] == [("correo", MAIL)]


def test_device_output_fixtures_skip_emails() -> None:
    service = "android.hardware.drm" + "@1.3-service.widevine\n"
    assert privacy.scan({"tests/fixtures/x.txt": service.encode()}) == []


def test_private_ips_only_where_people_write_about_their_tv() -> None:
    assert _rules(privacy.scan({"profiles/x/README.md": b"TV en 192.168.1.50\n"})) == ["IP privada"]
    assert _rules(privacy.scan({"docs/guides/a.md": b"10.0.0.7\n"})) == ["IP privada"]
    assert _rules(privacy.scan({"NOTES.md": b"172.20.1.2\n"})) == ["IP privada"]
    assert privacy.scan({"tests/test_a.py": b"ip = '192.168.1.5'\n"}) == []


def test_files_that_are_never_shared() -> None:
    files = {"profiles/x/backups/1/a.txt": b"x", "release.keystore": b"\0\1", ".env": b"A=1"}
    assert sorted(f.path for f in privacy.scan(files)) == sorted(files)


def test_binary_files_skip_content_rules() -> None:
    assert privacy.scan({"launcher/wallpapers/001.jpg": b"\xff\xd8\0" + GH.encode()}) == []


def test_extra_rules_apply_to_names_and_text() -> None:
    rules: list[privacy.Rule] = [("casa", re.compile(rb"xyzzy", re.IGNORECASE))]
    found = privacy.scan({"notas/Xyzzy.md": b"ok\n", "a.md": b"la casa de XYZZY\n"}, rules)
    assert sorted((f.path, f.line) for f in found) == [("a.md", 1), ("notas/Xyzzy.md", 0)]


def test_scan_text_for_commit_messages() -> None:
    rules: list[privacy.Rule] = [("casa", re.compile(rb"xyzzy", re.IGNORECASE))]
    assert _rules(privacy.scan_text("mensaje", "Fix in Xyzzy", rules)) == ["casa"]
    assert privacy.scan_text("mensaje", "Add TV model", rules) == []


def test_load_rules_skips_comments_and_blanks(tmp_path: Path) -> None:
    path = tmp_path / "r.txt"
    path.write_text("# nombres de casas\nxyzzy\n\n10\\.0\\.0\\.9\n", encoding="utf-8")
    rules = privacy.load_rules(path)
    assert [name for name, _ in rules] == ["xyzzy", "10\\.0\\.0\\.9"]
    assert rules[0][1].search(b"XYZZY")


def test_finding_reads_well() -> None:
    assert str(privacy.Finding("a.md", 3, "correo", "x")) == "a.md:3: correo: x"
    assert str(privacy.Finding("a.env", 0, "archivo que no se comparte", "a.env")) == (
        "a.env: archivo que no se comparte: a.env"
    )
