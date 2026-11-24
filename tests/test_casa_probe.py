"""Pruebas de las funciones puras de tools/casa_probe.py: python -m unittest tests/test_casa_probe.py"""

import json
import sys
import unittest
from pathlib import Path
from typing import ClassVar

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import casa_probe as cp


class Summary(unittest.TestCase):
    def test_never_shows_the_local_key_or_the_public_ip(self):
        s = cp.summarize(
            {"name": "Luz Salón", "local_key": "abc123secret", "ip": "88.1.2.3", "status": {"switch_1": False}}
        )
        text = json.dumps(s)
        self.assertNotIn("abc123secret", text)
        self.assertNotIn("88.1.2.3", text)
        self.assertTrue(s["local_key"])
        self.assertEqual(s["status"], {"switch_1": False})

    def test_a_device_without_key_says_so(self):
        self.assertFalse(cp.summarize({"name": "Gas sensor"})["local_key"])

    def test_qr_payload(self):
        self.assertEqual(cp.qr_payload("t0k"), "tuyaSmart--qrLogin?token=t0k")

    def test_secrets_live_outside_the_repo(self):
        self.assertFalse(cp.inside_repo(cp.HOME))
        self.assertTrue(cp.inside_repo(Path(cp.__file__).resolve().parent))


class Push(unittest.TestCase):
    DEVS: ClassVar[dict[str, dict[str, str]]] = {
        "a": {"id": "luz1", "name": "Luz Salón ", "local_key": "k" * 16, "lan_ip": "192.168.1.5", "version": "3.5"},
        "b": {"id": "cal1", "name": "Calefactor ", "local_key": "c" * 16, "lan_ip": "192.168.1.6", "version": "3.3"},
        "c": {"id": "otro", "name": "Enchufe", "local_key": "e" * 16, "lan_ip": "192.168.1.7", "version": "3.3"},
    }

    def test_picks_the_light_and_the_heater_by_name(self):
        p = cp.push_payload(self.DEVS)
        self.assertEqual(set(p), {"luz", "calefactor"})
        self.assertEqual(p["luz"], {"id": "luz1", "key": "k" * 16, "ip": "192.168.1.5", "version": "3.5"})

    def test_cloud_only_sensors_go_by_id(self):
        devs = dict(self.DEVS, d={"id": "puerta1", "name": "Puerta de casa", "local_key": "x" * 16})
        p = cp.push_payload(devs, {"luz": "Luz Salón", "puerta": "Puerta de casa"})
        self.assertEqual(p["puerta"], {"id": "puerta1"})

    def test_a_role_set_to_null_is_sent_as_null_so_casa_forgets_it(self):
        p = cp.push_payload(self.DEVS, {"luz": "Luz Salón", "gas": None})
        self.assertIsNone(p["gas"])
        self.assertEqual(p["luz"]["id"], "luz1")

    def test_refuses_a_device_without_its_lan_address(self):
        devs = json.loads(json.dumps(self.DEVS))
        del devs["b"]["lan_ip"]
        with self.assertRaises(ValueError):
            cp.push_payload(devs)


if __name__ == "__main__":
    unittest.main()
