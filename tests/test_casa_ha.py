"""Casa con Home Assistant desde el PC: conectar, proponer papeles y enviar, contra Home Assistant y tele falsos."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from tvopt.cli import build_parser
from tvopt.integrations.casa import ha

TOKEN = "eyJ.good.token"


def entity(entity_id: str, state: str = "on", **attributes: Any) -> dict[str, Any]:
    return {"entity_id": entity_id, "state": state, "attributes": attributes}


# Una casa con Ring (timbre en la puerta del piso y Ring Intercom en el portal), una Nuki y lo de siempre.
RING_HOME = [
    entity("event.puerta_ding", "2026-11-25T10:00:00+00:00", device_class="doorbell", friendly_name="Puerta Ding"),
    entity("event.puerta_motion", "2026-11-25T10:00:00+00:00", device_class="motion", friendly_name="Puerta Motion"),
    entity("camera.puerta_live_view", "idle", friendly_name="Puerta Live view"),
    entity("camera.puerta_last_recording", "idle", friendly_name="Puerta Last recording"),
    entity("event.portal_ding", "unknown", device_class="doorbell", friendly_name="Portal Ding"),
    entity("button.portal_open_door", "unknown", friendly_name="Portal Abrir puerta"),
    entity("lock.puerta_nuki", "locked", friendly_name="Puerta", supported_features=1),
    entity("light.salon", "on", friendly_name="Salón"),
    entity("light.cocina", "off", friendly_name="Cocina"),
    entity("switch.calefactor", "off", friendly_name="Calefactor"),
    entity("switch.router", "on", friendly_name="Router"),
    entity("sensor.salon_temperatura", "21.4", device_class="temperature", friendly_name="Salón temperatura"),
    entity("sensor.salon_humedad", "58", device_class="humidity", friendly_name="Salón humedad"),
    entity("binary_sensor.puerta_entrada", "off", device_class="door", friendly_name="Puerta entrada"),
    entity("binary_sensor.gas", "off", device_class="gas", friendly_name="Gas"),
]


class FakeHa(BaseHTTPRequestHandler):
    states: list[dict[str, Any]] = RING_HOME

    def do_GET(self) -> None:
        if self.headers.get("Authorization") != f"Bearer {TOKEN}":
            self.send_response(401)
            self.end_headers()
            return
        body = {
            "/api/config": {"version": "2026.11.3", "location_name": "Casa privada"},
            "/api/states": self.states,
        }.get(self.path)
        if body is None:
            self.send_response(404)
            self.end_headers()
            return
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: Any) -> None:
        pass


@pytest.fixture
def server() -> Iterator[str]:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), FakeHa)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def test_connects_with_the_token_and_never_shows_the_homes_name(server: str) -> None:
    assert ha.HaApi(server, TOKEN).version() == "2026.11.3"
    assert len(ha.HaApi(server + "/", TOKEN).states()) == len(RING_HOME)


def test_a_refused_token_says_how_to_make_a_new_one(server: str) -> None:
    with pytest.raises(ha.HaError, match="token"):
        ha.HaApi(server, "wrong").version()


def test_an_unreachable_server_is_a_clear_error() -> None:
    with pytest.raises(ha.HaError):
        ha.HaApi("http://127.0.0.1:9", TOKEN, timeout=2).version()


@pytest.mark.parametrize("url", ["192.168.1.10:8123", "http://h:8123/lovelace", "ftp://h", ""])
def test_only_the_servers_root_is_an_address(url: str) -> None:
    with pytest.raises(ha.HaError):
        ha.normalize_url(url)


def test_proposal_for_a_ring_and_nuki_home() -> None:
    p = ha.propose(RING_HOME)
    assert p["roles"] == {
        "luz": "light.salon",
        "calefactor": "switch.calefactor",
        "temperatura": "sensor.salon_temperatura",
        "humedad": "sensor.salon_humedad",
        "puerta": "binary_sensor.puerta_entrada",
        "gas": "binary_sensor.gas",
    }
    portal, puerta = p["timbres"]
    assert portal == {"nombre": "Portal", "llamada": "event.portal_ding", "abrir": ["button.portal_open_door"]}
    assert puerta == {
        "nombre": "Puerta",
        "llamada": "event.puerta_ding",
        "movimiento": "event.puerta_motion",
        "camara": "camera.puerta_live_view",
        "abrir": ["lock.puerta_nuki"],
    }
    assert p["aviso_movimiento"] == "aviso"
    assert p["abrir_tras_llamada_s"] == 180


def test_proposal_for_any_doorbell_brand() -> None:
    p = ha.propose(
        [
            entity("event.front_doorbell", "unknown", device_class="doorbell", friendly_name="Front Doorbell"),
            entity("binary_sensor.front_motion", "off", device_class="motion"),
            entity("camera.front", "idle"),
            entity("switch.tv", "on"),
        ]
    )
    assert p["timbres"] == [
        {
            "nombre": "Front",
            "llamada": "event.front_doorbell",
            "movimiento": "binary_sensor.front_motion",
            "camara": "camera.front",
        }
    ]
    assert "calefactor" not in p["roles"]  # a switch that is not a heater is not proposed as one


def test_describe_names_every_piece() -> None:
    lines = "\n".join(ha.describe(ha.propose(RING_HOME), RING_HOME))
    assert "light.salon (Salón)" in lines
    assert "lock.puerta_nuki" in lines
    assert TOKEN not in lines


def test_the_configuration_lives_outside_the_repo(tmp_path: Path) -> None:
    with pytest.raises(ha.HaError):
        ha.save({"token": TOKEN}, ha.REPO / "ha.json")
    path = ha.save({"url": "http://h:8123", "token": TOKEN}, tmp_path / "casa" / "ha.json")
    assert ha.load(path)["token"] == TOKEN
    assert not path.with_suffix(".tmp").exists()


class FakeTv:
    """La tele vista por ha.push: lo que se le manda por la entrada estándar y las órdenes."""

    def __init__(self, write_says: str = "", status: str = "Row: 0 configured=1, linked=1, doorbells=2") -> None:
        self.commands: list[str] = []
        self.stdin: list[str] = []
        self.write_says = write_says
        self.status_text = status

    def shell_input(self, script: str, data: str, timeout: float = 60) -> tuple[int, str]:
        self.commands.append(script)
        self.stdin.append(data)
        return 0, self.write_says

    def shell(self, script: str, timeout: float = 120) -> str:
        self.commands.append(script)
        return self.status_text if script.startswith("content query") else ""


def config() -> dict[str, Any]:
    return {"url": "http://192.168.1.10:8123/", "token": TOKEN, **ha.propose(RING_HOME)}


def test_push_sends_the_token_through_stdin_only() -> None:
    tv = FakeTv()
    assert ha.push(tv, config()) == {"configured": 1, "linked": 1, "doorbells": 2}
    assert tv.commands[0] == f"content write --uri {ha.CONFIG_URI}"
    sent = json.loads(tv.stdin[0])
    assert sent["token"] == TOKEN
    assert sent["url"] == "http://192.168.1.10:8123"
    assert all(TOKEN not in c for c in tv.commands)
    assert f"appops set {ha.PKG} SYSTEM_ALERT_WINDOW allow" in tv.commands


def test_push_refuses_when_casa_complains_or_nothing_is_set_up() -> None:
    with pytest.raises(ha.HaError, match="Casa"):
        ha.push(FakeTv(write_says="Error: Unknown URI"), config())
    with pytest.raises(ha.HaError):
        ha.push(FakeTv(), {"url": "http://h:8123"})
    with pytest.raises(ha.HaError):
        ha.push(FakeTv(), {"url": "http://h:8123", "token": TOKEN})


def test_status_without_casa_is_all_zero() -> None:
    assert ha.status(FakeTv(status="Error: no provider")) == {"configured": 0, "linked": 0, "doorbells": 0}


def test_simulate_starts_the_test_ring() -> None:
    tv = FakeTv()
    ha.simulate(tv, "timbre")
    assert tv.commands == [f"am start -n {ha.IMPORT} --es simulate timbre"]


@pytest.mark.parametrize(
    "words", [["casa", "enviar"], ["home", "send"], ["casa", "probar", "--serial", "1.2.3.4:5555"]]
)
def test_the_command_takes_both_languages(words: list[str]) -> None:
    parsed = build_parser().parse_args(words)
    assert parsed.orden in ("casa", "home")
