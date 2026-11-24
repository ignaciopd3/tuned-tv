"""Del perfil a los APK: cleanyourtv en la versión de patches/BASE con sus parches, compilado una sola vez.

La caché guarda los APK con la huella de BASE, los parches, ADDONS y la clave que los firma: si nada de eso cambia,
no se vuelve a compilar.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from tvopt.core.i18n import tr
from tvopt.core.log import Fail, Log

_ADDON_RE = re.compile(r"^[a-z0-9-]+$")
_PKG_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$")


@dataclass(frozen=True)
class Source:
    url: str
    commit: str
    patches: tuple[Path, ...]
    addons: tuple[tuple[str, str], ...]  # (carpeta en addons/, paquete)
    base_line: str
    addons_text: str

    @classmethod
    def load(cls, launcher_dir: Path) -> Source:
        base = launcher_dir / "patches" / "BASE"
        if not base.is_file():
            raise Fail(2, tr("Falta launcher/patches/BASE ({path})", path=base))
        base_line = base.read_text(encoding="utf-8").strip()
        parts = base_line.split()
        if len(parts) != 2:
            raise Fail(2, tr("{path}: se espera «url commit»", path=base))
        addons_file = launcher_dir / "patches" / "ADDONS"
        addons_text = addons_file.read_text(encoding="utf-8") if addons_file.is_file() else ""
        addons: list[tuple[str, str]] = []
        for n, line in enumerate(addons_text.splitlines(), 1):
            fields = line.split("#", 1)[0].split()
            if not fields:
                continue
            if len(fields) != 2 or not _ADDON_RE.match(fields[0]) or not _PKG_RE.match(fields[1]):
                raise Fail(2, tr("{where}: se espera «carpeta paquete»", where=f"{addons_file}:{n}"))
            addons.append((fields[0], fields[1]))
        patches = tuple(sorted((launcher_dir / "patches").glob("*.patch")))
        return cls(parts[0], parts[1], patches, tuple(addons), base_line, addons_text)

    def fingerprint(self, signing_key: bytes) -> str:
        """Huella de todo lo que decide los APK: BASE, cada parche, ADDONS y la clave de firma."""
        h = hashlib.sha256()
        for chunk in (self.base_line.encode(), self.addons_text.encode(), signing_key):
            h.update(len(chunk).to_bytes(8, "big") + chunk)
        for patch in self.patches:
            data = patch.read_bytes()
            h.update(patch.name.encode() + len(data).to_bytes(8, "big") + data)
        return h.hexdigest()[:24]

    def modules(self) -> tuple[str, ...]:
        return ("launcher", *(name for name, _pkg in self.addons))


class ApkCache:
    """~/.tv-opt/cache/launcher/<huella>/<módulo>.apk"""

    def __init__(self, root: Path) -> None:
        self.root = root

    def get(self, fingerprint: str, modules: tuple[str, ...]) -> dict[str, Path] | None:
        folder = self.root / fingerprint
        apks = {m: folder / f"{m}.apk" for m in modules}
        return apks if all(p.is_file() for p in apks.values()) else None

    def put(self, fingerprint: str, apks: dict[str, Path]) -> dict[str, Path]:
        folder = self.root / fingerprint
        folder.mkdir(parents=True, exist_ok=True)
        saved: dict[str, Path] = {}
        for module, apk in apks.items():
            target = folder / f"{module}.apk"
            shutil.copyfile(apk, target)
            saved[module] = target
        return saved


def default_cache() -> ApkCache:
    return ApkCache(Path(os.environ.get("TVOPT_HOME") or Path.home() / ".tv-opt") / "cache" / "launcher")


def signing_key() -> bytes:
    """La clave con la que gradle firma (la de depuración de este equipo): cambiarla obliga a recompilar."""
    keystore = Path.home() / ".android" / "debug.keystore"
    return keystore.read_bytes() if keystore.is_file() else b""


def _git(cyt: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(cyt), *args], capture_output=True, text=True, check=False)


def checkout(src: Source, cyt: Path, profile_id: str, log: Log) -> None:
    """cleanyourtv en src.commit con los parches del perfil, en la rama tv-opt-<perfil>."""
    if not (cyt / ".git").is_dir():
        cyt.parent.mkdir(parents=True, exist_ok=True)
        if subprocess.run(["git", "clone", "-q", src.url, str(cyt)], check=False).returncode != 0:
            raise Fail(1, tr("No se pudo clonar {url}", url=src.url))
    if _git(cyt, "cat-file", "-e", f"{src.commit}^{{commit}}").returncode != 0:
        _git(cyt, "fetch", "-q", "origin")
    if _git(cyt, "checkout", "-q", "-B", f"tv-opt-{profile_id}", src.commit).returncode != 0:
        raise Fail(1, tr("No se pudo poner cleanyourtv en {commit}", commit=src.commit))
    applied = _git(cyt, "am", "-q", *(str(p) for p in src.patches))
    if applied.returncode != 0:
        _git(cyt, "am", "--abort")
        raise Fail(
            1,
            tr(
                "Los parches no aplican sobre {commit}: {detail}",
                commit=src.commit,
                detail=applied.stderr.strip()[:300],
            ),
        )
    log.ok(
        tr(
            "cleanyourtv en {commit} con {count} parches (rama tv-opt-{profile})",
            commit=src.commit,
            count=len(src.patches),
            profile=profile_id,
        )
    )


def build(cyt: Path, module_dir: str, log: Log) -> Path:
    """Compila y prueba un módulo (launcher o addons/<x>) y devuelve su APK firmado."""
    log.info(tr("Compilando {module}", module=module_dir))
    folder = cyt / module_dir
    props = folder / "local.properties"
    sdk = os.environ.get("ANDROID_HOME", "")
    if not props.is_file() and sdk:
        props.write_text(f"sdk.dir={sdk.replace(chr(92), '/')}\n", encoding="utf-8")
    gradlew = folder / ("gradlew.bat" if sys.platform == "win32" else "gradlew")
    result = subprocess.run(
        [str(gradlew), "-q", "--console=plain", "testReleaseUnitTest", "assembleRelease"],
        cwd=folder,
        check=False,
    )
    apk = folder / "app" / "build" / "outputs" / "apk" / "release" / "app-release.apk"
    if result.returncode != 0 or not apk.is_file():
        raise Fail(1, tr("Falló la compilación de {module}", module=module_dir))
    return apk


def apks(src: Source, cyt: Path, profile_id: str, log: Log, cache: ApkCache, force: bool = False) -> dict[str, Path]:
    """Los APK del perfil, de la caché si la huella coincide; si no, compilados y guardados en ella."""
    fingerprint = src.fingerprint(signing_key())
    if not force:
        cached = cache.get(fingerprint, src.modules())
        if cached is not None:
            log.ok(tr("APK en caché ({fingerprint}): no hace falta compilar", fingerprint=fingerprint))
            return cached
    checkout(src, cyt, profile_id, log)
    built = {"launcher": build(cyt, "launcher", log)}
    for name, _pkg in src.addons:
        built[name] = build(cyt, f"addons/{name}", log)
    saved = cache.put(fingerprint, built)
    log.ok(tr("Compilado y guardado en caché ({fingerprint})", fingerprint=fingerprint))
    return saved
