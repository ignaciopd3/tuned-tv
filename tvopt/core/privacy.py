"""Detector de datos privados para un repo que se comparte: correos, IPs de casa, claves y copias de seguridad.

Lo usan el CI de las PR (lista genérica) y la publicación desde el repo privado del mantenedor (genérica más la suya).

    uv run python -m tvopt.core.privacy [--rules archivo]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from tvopt.core.i18n import N_, localize_argparse, tr

Rule = tuple[str, re.Pattern[bytes]]

_EMAIL = re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
_EMAIL_OK = re.compile(rb"(?:@users\.noreply\.github\.com|@example\.(?:com|org|net)|^noreply@anthropic\.com)$")
_PRIVATE_IP = re.compile(rb"\b(?:192\.168|10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b")
_SECRETS: tuple[Rule, ...] = (
    (N_("token de GitHub"), re.compile(rb"\b(?:ghp|gho|ghu|ghs)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{40,}")),
    (N_("clave de AWS"), re.compile(rb"\bAKIA[0-9A-Z]{16}\b")),
    (N_("clave privada"), re.compile(rb"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")),
)
_NEVER = re.compile(r"(?:^|/)(?:backups/|\.env$|[^/]*\.(?:keystore|jks|p12)$)")
_DEVICE_OUTPUT = "tests/fixtures/"  # salidas reales de la tele: nombres de servicios con «@» que no son correos
_IP_PLACES = ("profiles/", "docs/", ".github/")  # donde la gente escribe sobre su tele


@dataclass(frozen=True)
class Finding:
    path: str
    line: int  # 0: el nombre del archivo
    rule: str
    text: str

    def __str__(self) -> str:
        where = self.path if self.line == 0 else f"{self.path}:{self.line}"
        return f"{where}: {tr(self.rule)}: {self.text}"


def _clip(raw: bytes) -> str:
    return raw.decode("utf-8", "replace")[:80]


def _ip_place(path: str) -> bool:
    return path.startswith(_IP_PLACES) or ("/" not in path and path.endswith(".md"))


def scan(files: Mapping[str, bytes], extra: Iterable[Rule] = ()) -> list[Finding]:
    """Lo que no debe salir, archivo a archivo y línea a línea. extra: reglas propias (nombres de casas, etc.)."""
    own = tuple(extra)
    found: list[Finding] = []
    for path in sorted(files):
        data = files[path]
        if _NEVER.search(path):
            found.append(Finding(path, 0, N_("archivo que no se comparte"), path))
        found.extend(Finding(path, 0, name, path) for name, rule in own if rule.search(path.encode()))
        if b"\0" in data[:8192]:
            continue  # binario: imágenes, APK
        generic = not path.startswith(_DEVICE_OUTPUT)
        ips = _ip_place(path)
        for n, line in enumerate(data.splitlines(), 1):
            for name, rule in (*_SECRETS, *own):
                hit = rule.search(line)
                if hit:
                    found.append(Finding(path, n, name, _clip(hit.group(0))))
            if generic:
                found.extend(
                    Finding(path, n, N_("correo"), _clip(m.group(0)))
                    for m in _EMAIL.finditer(line)
                    if not _EMAIL_OK.search(m.group(0))
                )
            if ips:
                hit = _PRIVATE_IP.search(line)
                if hit:
                    found.append(Finding(path, n, N_("IP privada"), _clip(hit.group(0))))
    return found


def scan_text(label: str, text: str, extra: Iterable[Rule] = ()) -> list[Finding]:
    """Un texto suelto (el mensaje de un commit) con las mismas reglas de contenido."""
    return [f for f in scan({label: text.encode()}, extra) if f.line]


def load_rules(path: Path) -> list[Rule]:
    """Una expresión regular por línea, sin distinguir mayúsculas; «#» comenta."""
    rules: list[Rule] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            rules.append((line, re.compile(line.encode(), re.IGNORECASE)))
    return rules


def _tracked() -> dict[str, bytes]:
    out = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True).stdout.decode("utf-8")
    return {name: Path(name).read_bytes() for name in out.split("\0") if name and Path(name).is_file()}


def main(argv: list[str] | None = None) -> int:
    localize_argparse()
    parser = argparse.ArgumentParser(prog="privacy", description=tr("Busca datos privados en los archivos del repo"))
    parser.add_argument("--rules", type=Path, help=tr("reglas propias, una expresión regular por línea"))
    args = parser.parse_args(argv)
    rules_path: Path | None = args.rules
    extra = load_rules(rules_path) if rules_path else []
    found = scan(_tracked(), extra)
    for finding in found:
        print(finding)
    print(
        tr("Sin datos privados") if not found else tr("{count} posibles datos privados", count=len(found)),
        file=sys.stderr,
    )
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
