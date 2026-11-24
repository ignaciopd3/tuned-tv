"""Registro del motor: fecha y nivel a stderr (en color solo en una terminal y sin NO_COLOR), copiado a run.log."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_COLORS = {"INFO": "0;36", "OK": "0;32", "WARN": "0;33", "ERROR": "0;31"}


class Fail(Exception):
    """Termina la ejecución con un código de salida, como die del motor de Bash."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


class Log:
    """Una línea por mensaje; mientras file está puesto, también va (sin color) al run.log de la ejecución."""

    def __init__(self) -> None:
        self.file: Path | None = None

    def _write(self, level: str, message: str) -> None:
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {message}"
        if sys.stderr.isatty() and not os.environ.get("NO_COLOR"):
            print(f"\033[{_COLORS[level]}m{line}\033[0m", file=sys.stderr, flush=True)
        else:
            print(line, file=sys.stderr, flush=True)
        if self.file is not None:
            with self.file.open("a", encoding="utf-8", newline="\n") as f:
                f.write(line + "\n")

    def info(self, message: str) -> None:
        self._write("INFO", message)

    def ok(self, message: str) -> None:
        self._write("OK", message)

    def warn(self, message: str) -> None:
        self._write("WARN", message)

    def error(self, message: str) -> None:
        self._write("ERROR", message)
