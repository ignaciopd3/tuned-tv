"""Los mensajes de tv-opt, leídos del código: lo que pasa por tr() y N_(), y lo que se le escapa.

Lo usa tests/test_i18n.py; también sirve a mano: uv run python tests/i18n_scan.py (lista lo que falta en inglés).
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_WORDS = re.compile(r"[A-Za-zÀ-ÿ]{3,}[^\n]*\s[A-Za-zÀ-ÿ]{2,}")  # al menos dos palabras: un mensaje, no un nombre
_SHOWN_BY = {"info", "ok", "warn", "error", "print", "exit", "_warn"}  # log.*, print(), sys.exit()
_ERRORS = {"Fail", "ProfileError", "AdbError", "ValueError", "FileNotFoundError", "RuntimeError", "Stop"}


def files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "tvopt/*.py", "tools/*.py", "run.py"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return [ROOT / p for p in out.stdout.split() if (ROOT / p).name not in ("i18n.py", "i18n_en.py")]


def _constants(tree: ast.Module) -> dict[str, str]:
    found: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found[target.id] = node.value.value
    return found


def _name(func: ast.expr) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _is_text(node: ast.expr) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return bool(_WORDS.search(node.value))
    if isinstance(node, ast.JoinedStr):
        text = "".join(v.value for v in node.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
        return bool(_WORDS.search(text))
    if isinstance(node, ast.BinOp):
        return _is_text(node.left) or _is_text(node.right)
    return False


def scan() -> tuple[dict[str, list[str]], list[str]]:
    """(mensaje → dónde se usa, textos que se enseñan sin pasar por tr())."""
    msgids: dict[str, list[str]] = {}
    loose: list[str] = []
    for path in files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        consts = _constants(tree)
        rel = path.relative_to(ROOT).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _name(node.func)
            if name in ("tr", "N_") and node.args:
                first = node.args[0]
                text = (
                    first.value
                    if isinstance(first, ast.Constant) and isinstance(first.value, str)
                    else consts.get(first.id)
                    if isinstance(first, ast.Name)
                    else None
                )
                if text is not None:
                    msgids.setdefault(text, []).append(f"{rel}:{node.lineno}")
                continue
            shown = list(node.args) if name in _SHOWN_BY or name in _ERRORS else []
            shown += [k.value for k in node.keywords if k.arg in ("help", "description")]
            loose += [f"{rel}:{a.lineno}: {ast.unparse(a)[:90]}" for a in shown if _is_text(a)]
    return msgids, loose


def placeholders(text: str) -> list[str]:
    return sorted(re.findall(r"\{([a-z_]+)[^}]*\}", text))


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    from tvopt.core.i18n_en import EN

    ids, escaped = scan()
    for text in ids:
        if text not in EN:
            print(repr(text))
    for line in escaped:
        print("SIN tr():", line)
