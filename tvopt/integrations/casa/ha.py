"""Home Assistant para Casa, desde el PC: conectar, proponer los papeles y enviarlos a la tele.

La dirección y el token se guardan en CASA_DIR/ha.json (por defecto ~/Documents/casa-tuya), fuera del repo. A la tele
van con `content write` por la entrada estándar de adb, así el token no sale en ninguna línea de órdenes ni queda en un
archivo de la tele. Por pantalla nunca sale el token ni el nombre de la casa. Diseño:
docs/guides/home-assistant.md.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Protocol, cast

from tvopt.core.i18n import tr

REPO = Path(__file__).resolve().parents[3]
PKG = "io.github.ignaciopd3.casa"
CONFIG_URI = f"content://{PKG}.config/ha.json"
STATUS_URI = f"content://{PKG}.config/status"
IMPORT = f"{PKG}/.ImportActivity"
DEFAULTS: dict[str, Any] = {"aviso_movimiento": "aviso", "abrir_tras_llamada_s": 180, "pausar": True}
MAX_OPENERS = 3
_URL = re.compile(r"^https?://[^/\s]+/?$")
_STATUS = re.compile(r"configured=(\d+), linked=(\d+), doorbells=(\d+)")
_DOORBELL_SUFFIXES = ("_ding", "_ring", "_doorbell", "_press", "_button", "_visitor")

Json = dict[str, Any]


class HaError(Exception):
    """Algo que impide seguir, con el mensaje ya traducido para quien lo lee."""


def casa_dir() -> Path:
    return Path(os.environ.get("CASA_DIR") or Path.home() / "Documents" / "casa-tuya")


def config_path() -> Path:
    return casa_dir() / "ha.json"


def inside_repo(path: Path) -> bool:
    path = Path(path).resolve()
    return path == REPO or REPO in path.parents


def normalize_url(url: str) -> str:
    """La raíz del servidor, sin barra final: http://192.168.1.10:8123."""
    url = url.strip()
    if not _URL.match(url):
        raise HaError(
            tr("La dirección de Home Assistant es la raíz, p. ej. http://192.168.1.10:8123 (no {url})", url=url)
        )
    return url.rstrip("/")


def load(path: Path | None = None) -> Json:
    path = path or config_path()
    if not path.is_file():
        return {}
    return cast(Json, json.loads(path.read_text(encoding="utf-8")))


def save(data: Json, path: Path | None = None) -> Path:
    path = path or config_path()
    if inside_repo(path):
        raise HaError(tr("Me niego a guardar datos de la cuenta dentro del repo: {path}", path=path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(path)
    return path


class HaApi:
    """La API REST de Home Assistant, solo para leer (GET) desde el PC."""

    def __init__(self, url: str, token: str, timeout: float = 10) -> None:
        self.url = normalize_url(url)
        self.token = token
        self.timeout = timeout

    def _get(self, path: str) -> Any:
        request = urllib.request.Request(
            self.url + path, headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # http/https: normalize_url
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise HaError(tr("Home Assistant rechazó el token: crea uno nuevo en tu perfil, Seguridad")) from e
            raise HaError(tr("Home Assistant respondió {code} a {path}", code=e.code, path=path)) from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise HaError(tr("No llego a Home Assistant en {url}: {detail}", url=self.url, detail=e)) from e

    def version(self) -> str:
        return str(cast(Json, self._get("/api/config")).get("version", "?"))

    def states(self) -> list[Json]:
        return cast(list[Json], self._get("/api/states"))


# ---- propuesta de papeles ----


def _domain(entity_id: str) -> str:
    return entity_id.split(".", 1)[0]


def _object(entity_id: str) -> str:
    return entity_id.split(".", 1)[1]


def _attrs(state: Json) -> Json:
    return cast(Json, state.get("attributes") or {})


def _device_class(state: Json) -> str:
    return str(_attrs(state).get("device_class") or "")


def _name(state: Json) -> str:
    return str(_attrs(state).get("friendly_name") or _object(str(state["entity_id"])))


def _prefix(object_id: str) -> str:
    for suffix in _DOORBELL_SUFFIXES:
        if object_id.endswith(suffix):
            return object_id[: -len(suffix)]
    return object_id


def _first(
    states: list[Json], domain: str, device_class: str | None = None, words: tuple[str, ...] = (), fallback: bool = True
) -> str | None:
    """La primera entidad del dominio (y clase) cuyo id o nombre lleve alguna de las palabras; si no, la primera."""
    found = [
        s
        for s in states
        if _domain(str(s["entity_id"])) == domain and (device_class is None or _device_class(s) == device_class)
    ]
    for s in found:
        text = (str(s["entity_id"]) + " " + _name(s)).casefold()
        if any(w in text for w in words):
            return str(s["entity_id"])
    return str(found[0]["entity_id"]) if found and fallback else None


def _doorbell(states: list[Json], ids: set[str], ring: Json) -> Json:
    ring_id = str(ring["entity_id"])
    prefix = _prefix(_object(ring_id))
    bell: Json = {"nombre": _bell_name(ring, prefix), "llamada": ring_id}
    motion = next(
        (
            str(s["entity_id"])
            for s in states
            if _object(str(s["entity_id"])).startswith(prefix)
            and _device_class(s) == "motion"
            and _domain(str(s["entity_id"])) in ("event", "binary_sensor")
        ),
        None,
    )
    if motion:
        bell["movimiento"] = motion
    for candidate in (f"camera.{prefix}_live_view", f"camera.{prefix}"):
        if candidate in ids:
            bell["camara"] = candidate
            break
    else:
        camera = next((i for i in sorted(ids) if i.startswith(f"camera.{prefix}") and "last_recording" not in i), None)
        if camera:
            bell["camara"] = camera
    if f"button.{prefix}_open_door" in ids:
        bell["abrir"] = [f"button.{prefix}_open_door"]
    return bell


def _bell_name(ring: Json, prefix: str) -> str:
    name = _name(ring)
    words = name.split()
    if len(words) > 1 and words[-1].casefold() in ("ding", "ring", "doorbell", "timbre", "press", "llamada"):
        name = " ".join(words[:-1])
    return name.strip() or prefix.replace("_", " ").capitalize()


def propose(states: list[Json]) -> Json:
    """Papeles y timbres a partir de lo que tiene Home Assistant: una propuesta para revisar, no una verdad."""
    states = sorted(states, key=lambda s: str(s["entity_id"]))
    ids = {str(s["entity_id"]) for s in states}
    picks = {
        "luz": _first(states, "light", words=("salon", "salón", "living", "comedor")),
        "calefactor": _first(states, "switch", words=("calef", "heater", "radiador", "estufa"), fallback=False),
        "temperatura": _first(states, "sensor", "temperature", words=("salon", "salón", "living", "interior")),
        "humedad": _first(states, "sensor", "humidity", words=("salon", "salón", "living", "interior")),
        "puerta": _first(states, "binary_sensor", "door", words=("entrada", "front", "puerta", "principal")),
        "gas": _first(states, "binary_sensor", "gas"),
    }
    roles = {role: entity for role, entity in picks.items() if entity}

    rings = [s for s in states if _domain(str(s["entity_id"])) == "event" and _device_class(s) == "doorbell"]
    bells = [_doorbell(states, ids, ring) for ring in rings][:4]
    locks = [i for i in sorted(ids) if _domain(i) == "lock"]
    if locks and bells:
        # una cerradura va con el timbre de la puerta de casa: el que no abre ya un portal con su botón
        home = next((b for b in bells if "abrir" not in b), bells[0])
        home["abrir"] = (cast(list[str], home.get("abrir", [])) + locks)[:MAX_OPENERS]
    return {"roles": roles, "timbres": bells, **DEFAULTS}


def describe(config: Json, states: list[Json]) -> list[str]:
    """Líneas para enseñar la propuesta: cada papel y cada timbre con el nombre que les da Home Assistant."""
    names = {str(s["entity_id"]): _name(s) for s in states}
    lines = [
        tr("  {role}: {entity} ({name})", role=r, entity=e, name=names.get(e, "?")) for r, e in config["roles"].items()
    ]
    for bell in cast(list[Json], config["timbres"]):
        parts = [tr("llamada {entity}", entity=bell["llamada"])]
        if "movimiento" in bell:
            parts.append(tr("movimiento {entity}", entity=bell["movimiento"]))
        if "camara" in bell:
            parts.append(tr("cámara {entity}", entity=bell["camara"]))
        for opener in cast(list[str], bell.get("abrir", [])):
            parts.append(tr("abre {entity}", entity=opener))
        lines.append(tr("  timbre «{name}»: {parts}", name=bell["nombre"], parts=", ".join(parts)))
    return lines


# ---- la tele ----


class Tv(Protocol):
    def shell(self, script: str, timeout: float = 120) -> str: ...

    def shell_input(self, script: str, data: str, timeout: float = 60) -> tuple[int, str]: ...


def payload(config: Json) -> str:
    """Lo que recibe Casa: la configuración entera, con la URL ya normalizada y los valores por defecto puestos."""
    if not config.get("url") or not config.get("token"):
        raise HaError(tr("Falta conectar con Home Assistant: run.py casa conectar"))
    if not config.get("roles") and not config.get("timbres"):
        raise HaError(tr("No hay nada que enviar: run.py casa descubrir propone los papeles"))
    out = {**DEFAULTS, **config, "url": normalize_url(str(config["url"]))}
    return json.dumps(out, ensure_ascii=False)


def push(tv: Tv, config: Json) -> dict[str, int]:
    """Envía ha.json a Casa, le permite los avisos encima de todo y devuelve lo que dice /status."""
    rc, said = tv.shell_input(f"content write --uri {CONFIG_URI}", payload(config))
    if rc != 0 or said.strip():
        raise HaError(
            tr("Casa no aceptó la configuración (¿Casa instalada y al día?): {detail}", detail=said.strip()[:200])
        )
    tv.shell(f"appops set {PKG} SYSTEM_ALERT_WINDOW allow")
    return status(tv)


def status(tv: Tv) -> dict[str, int]:
    m = _STATUS.search(tv.shell(f"content query --uri {STATUS_URI}"))
    if not m:
        return {"configured": 0, "linked": 0, "doorbells": 0}
    return {"configured": int(m.group(1)), "linked": int(m.group(2)), "doorbells": int(m.group(3))}


def simulate(tv: Tv, what: str) -> None:
    """Un timbre o un movimiento de mentira en la tele (solo ADB), para ver el aviso sin timbre."""
    tv.shell(f"am start -n {IMPORT} --es simulate {what}")
