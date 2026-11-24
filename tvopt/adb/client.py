"""Cliente ADB común a Android TV y Fire OS: lecturas agrupadas en una sola ida y vuelta a la tele."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
import time
from collections.abc import Callable, Mapping
from pathlib import Path

from tvopt.core.i18n import tr

SERIAL_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
_SECTION_NAME_RE = re.compile(r"^[a-z0-9_.]+$")
_SECTION_MARK_RE = re.compile(r"^==([a-z0-9_.]+)==$")


class AdbError(Exception):
    """La tele no responde o no se pudo conectar (código de salida 1)."""


def adb_command() -> list[str]:
    """TVOPT_ADB si está (orden completa con / como separador, p. ej. la tele simulada); si no, ADB o «adb»."""
    forced = os.environ.get("TVOPT_ADB")
    if forced:
        return shlex.split(forced)
    return [os.environ.get("ADB", "adb")]


def build_script(sections: Mapping[str, str]) -> str:
    """Un único script remoto: cada sección empieza con su marca ==nombre== para separarlas al volver."""
    parts: list[str] = []
    for name, command in sections.items():
        if not _SECTION_NAME_RE.match(name):
            raise ValueError(tr("Nombre de sección inválido: {name}", name=name))
        parts.append(f"echo =={name}==; {command}")
    return "; ".join(parts)


def split_sections(output: str) -> dict[str, str]:
    """La salida de build_script, separada por sus marcas; lo de antes de la primera marca se descarta."""
    sections: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in output.splitlines():
        mark = _SECTION_MARK_RE.match(line)
        if mark:
            current = sections.setdefault(mark.group(1), [])
        elif current is not None:
            current.append(line)
    return {name: "\n".join(lines) for name, lines in sections.items()}


def _stderr(message: str) -> None:
    print(message, file=sys.stderr)


class Adb:
    """Una tele por ADB. Cada llamada es un proceso adb; lo caro es la ida y vuelta, así que se agrupa con batch."""

    def __init__(
        self,
        serial: str,
        command: list[str] | None = None,
        wait_secs: int | None = None,
        warn: Callable[[str], None] = _stderr,
    ) -> None:
        if not SERIAL_RE.match(serial):
            raise ValueError(tr("Serial inválido: {serial}", serial=serial))
        self.serial = serial
        self.command = command or adb_command()
        self.wait_secs = int(os.environ.get("ADB_WAIT_SECS", "60")) if wait_secs is None else wait_secs
        self._warn = warn

    def _run(self, args: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                [*self.command, *args],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            raise AdbError(
                tr("La tele {serial} no respondió en {seconds:.0f} s", serial=self.serial, seconds=timeout)
            ) from e
        except FileNotFoundError as e:
            raise AdbError(tr("No encuentro adb ({path})", path=self.command[0])) from e

    def connect(self) -> None:
        """Conecta (si es ip:puerto) y espera a que la tele esté autorizada, como adb_connect del motor de Bash."""
        waited, warned = 0, False
        while True:
            if ":" in self.serial:
                self._run(["connect", self.serial], timeout=30)
            result = self._run(["-s", self.serial, "get-state"], timeout=30)
            state = (result.stdout + result.stderr).replace("\r", "").strip()
            if state == "device":
                return
            if "unauthorized" in state and not warned:
                self._warn(tr("Acepta en la tele el aviso «¿Permitir la depuración USB?» (marca «Permitir siempre»)"))
                warned = True
            if waited >= self.wait_secs:
                raise AdbError(
                    tr(
                        "No se pudo conectar a {serial} (estado: {state})",
                        serial=self.serial,
                        state=state or tr("sin respuesta"),
                    )
                )
            time.sleep(2)
            waited += 2

    def shell(self, script: str, timeout: float = 120) -> str:
        """Ejecuta script en el shell de la tele, en una sola sesión, y devuelve su salida sin \\r."""
        result = self._run(["-s", self.serial, "shell", script], timeout=timeout)
        if result.returncode != 0 and not result.stdout:
            raise AdbError(tr("La tele no respondió: {detail}", detail=result.stderr.strip()[:200]))
        return result.stdout.replace("\r", "")

    def shell_rc(self, script: str, timeout: float = 300) -> tuple[int, str]:
        """Como shell, pero devuelve también el código de salida en vez de fallar (para saber si un lote se cortó)."""
        result = self._run(["-s", self.serial, "shell", script], timeout=timeout)
        return result.returncode, result.stdout.replace("\r", "")

    def run_script(self, local: Path, timeout: float = 300) -> tuple[int, str]:
        """Sube un script, lo ejecuta en una sola sesión y lo borra: (código, salida). Si no se pudo subir, código 1."""
        remote = f"/data/local/tmp/tvopt-{os.getpid()}-{local.name}"
        pushed = self._run(["-s", self.serial, "push", local.as_posix(), remote], timeout=timeout)
        if pushed.returncode != 0:
            return 1, ""
        return self.shell_rc(f"sh {remote}; rc=$?; rm -f {remote}; exit $rc", timeout=timeout)

    def install(self, apk: Path, timeout: float = 600) -> tuple[bool, str]:
        """adb install -r (conserva los datos de la app): (bien, última línea de adb)."""
        result = self._run(["-s", self.serial, "install", "-r", apk.as_posix()], timeout=timeout)
        last = (result.stdout + result.stderr).replace("\r", "").strip().splitlines()[-1:] or [""]
        return last[0].startswith("Success"), last[0]

    def push(self, local: Path, remote: str, timeout: float = 600) -> bool:
        """adb push de un archivo; True si llegó."""
        return self._run(["-s", self.serial, "push", local.as_posix(), remote], timeout=timeout).returncode == 0

    def batch(self, sections: Mapping[str, str], timeout: float = 120) -> dict[str, str]:
        """Varias lecturas en una sola ida y vuelta: {nombre: orden} → {nombre: salida}."""
        return split_sections(self.shell(build_script(sections), timeout=timeout))
