#!/usr/bin/env python3
"""Casa, fase 0: la cuenta de Smart Life con el SDK oficial de Tuya, probada desde el PC.

Lo sensible (sesión, claves locales, IP pública) se guarda solo en ~/Documents/casa-tuya (CASA_DIR), fuera del
repo; por pantalla nunca sale una clave. Se ejecuta con el Python de ~/Documents/casa-tuya/venv, que tiene
tuya-device-sharing-sdk, tinytuya y qrcode.

Uso: USAGE, más abajo.
"""
import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # para tvopt.core.i18n al lanzarlo como script
from tvopt.core.i18n import tr  # noqa: E402

USAGE = """Uso:
  casa_probe.py login <código>   código de usuario de Smart Life (Yo > Ajustes > Cuenta y seguridad); deja qr.png
                                 y espera hasta 3 min a que se escanee con la app
  casa_probe.py devices          lista los aparatos y los guarda en aparatos.json
  casa_probe.py scan             busca los aparatos en la red de casa: IP local y versión del protocolo LAN
  casa_probe.py listen [seg]     muestra lo que llega por MQTT (puerta, gas, enchufes) durante seg (120)
  casa_probe.py toggle <nombre>  enciende o apaga en local un enchufe, por su nombre en la app
  casa_probe.py push             pasa a la tele (complemento Casa, por ADB) los aparatos de roles.json y le da permiso
                                 para mostrar avisos encima de todo; entorno ADB y TV_SERIAL como run.py
  casa_probe.py tv-login <código> abre una sesión de la nube solo para la tele (QR nuevo) y se la pasa; el PC no la
                                 guarda

roles.json (en CASA_DIR, fuera del repo): papel en Casa → nombre en Smart Life, p. ej.
  {"luz": "Luz Salón", "calefactor": "Calefactor", "gas": "Gas sensor", "clima": "…", "puerta": "…"}
"""

HOME = Path(os.environ.get("CASA_DIR", Path.home() / "Documents" / "casa-tuya"))
SESSION, DEVICES, QR_PNG = HOME / "sesion.json", HOME / "aparatos.json", HOME / "qr.png"
# Registro público de Home Assistant en el sistema de compartir aparatos de Tuya (homeassistant/components/tuya).
CLIENT_ID, SCHEMA = "HA_3y9q4ak7g4ephrvke", "haauthorize"
REPO = Path(__file__).resolve().parents[1]


def inside_repo(path):
    path = Path(path).resolve()
    return REPO == path or REPO in path.parents


def qr_payload(token):
    return f"tuyaSmart--qrLogin?token={token}"


def summarize(dev):
    """Lo que se puede enseñar de un aparato: ni la clave local ni la IP pública de casa."""
    return {"name": dev.get("name"), "category": dev.get("category"), "product": dev.get("product_name"),
            "online": dev.get("online"), "local_key": bool(dev.get("local_key")),
            "ip": dev.get("lan_ip") or "", "version": dev.get("version") or "", "status": dev.get("status") or {}}


def save_json(path, data):
    if inside_repo(path):
        sys.exit(tr("Me niego a guardar datos de la cuenta dentro del repo: {path}", path=path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


PUSH_ROLES = {"luz": "Luz Salón", "calefactor": "Calefactor"}   # papel en Casa → nombre en Smart Life
ROLES = HOME / "roles.json"
CASA_PKG = "io.github.ignaciopd3.casa"
CASA_IMPORT = CASA_PKG + "/.ImportActivity"
CLOUD_ONLY = ("clima", "puerta")   # sensores a pilas: solo hablan con la nube, Casa solo necesita su id


def push_payload(devs, roles=PUSH_ROLES):
    """La configuración que recibe Casa: por papel, el id y, si va por la red de casa, clave local, IP y versión."""
    out = {}
    for role, name in roles.items():
        if name is None:   # roles.json "gas": null -> Casa forgets it (device broken or gone)
            out[role] = None
            continue
        rec = next((r for r in devs.values() if (r.get("name") or "").strip().casefold() == name.strip().casefold()), None)
        if rec and role in CLOUD_ONLY:
            out[role] = {"id": rec["id"]}
            continue
        if not rec or not all(rec.get(k) for k in ("local_key", "lan_ip", "version")):
            raise ValueError(tr("Falta «{name}» con clave, IP y versión: ejecuta devices y scan antes", name=name))
        out[role] = {"id": rec["id"], "key": rec["local_key"], "ip": rec["lan_ip"], "version": rec["version"]}
    return out


def adb(*args):
    exe, serial = os.environ.get("ADB", "adb"), os.environ.get("TV_SERIAL")
    if not serial:
        sys.exit(tr("Indica la tele con la variable TV_SERIAL (ip:puerto)"))
    r = subprocess.run([exe, "-s", serial, *args], capture_output=True, text=True)
    said = (r.stdout + r.stderr).strip()
    if r.returncode != 0 or "Error" in said or "Exception" in said:
        sys.exit(tr("La tele no aceptó la orden: {detail}", detail=said.splitlines()[-1][:200] if said else tr("sin respuesta")))
    return said


def cmd_push():
    try:
        roles = load_json(ROLES) if ROLES.exists() else PUSH_ROLES
        payload = push_payload(load_json(DEVICES), roles)
    except ValueError as e:
        sys.exit(str(e))
    b64 = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    adb("shell", "am", "start", "-n", CASA_IMPORT, "--es", "b64", b64)
    adb("shell", "appops", "set", CASA_PKG, "SYSTEM_ALERT_WINDOW", "allow")
    sent = [r for r, v in payload.items() if v is not None]
    gone = [r for r, v in payload.items() if v is None]
    forgotten = tr("; olvidado: {roles}", roles=", ".join(gone)) if gone else ""
    print(tr("Enviado a Casa: {roles}{forgotten}; avisos encima de todo permitidos",
             roles=", ".join(sent), forgotten=forgotten))   # nunca la clave


def cmd_tv_login(user_code):
    """Una sesión nueva, solo para la tele: el PC no la usa ni la guarda, así nunca se pisan las renovaciones."""
    from tuya_sharing import LoginControl
    import qrcode
    ctl = LoginControl()
    resp = ctl.qr_code(CLIENT_ID, SCHEMA, user_code)
    if not resp.get("success"):
        sys.exit(tr("Tuya no dio el QR: {detail}", detail=resp.get('msg') or resp.get('code')))
    token = resp["result"]["qrcode"]
    HOME.mkdir(parents=True, exist_ok=True)
    qrcode.make(qr_payload(token)).save(QR_PNG)
    print(tr("QR listo: {path}", path=QR_PNG), flush=True)
    try:
        for _ in range(90):
            time.sleep(2)
            ok, info = ctl.login_result(token, CLIENT_ID, user_code)
            if ok:
                session = {"user_code": user_code, "terminal_id": info["terminal_id"], "endpoint": info["endpoint"],
                           "token": info}
                b64 = base64.b64encode(json.dumps(session).encode("utf-8")).decode("ascii")
                adb("shell", "am", "start", "-n", CASA_IMPORT, "--es", "session_b64", b64)
                print(tr("Sesión de la tele enviada a Casa."), flush=True)
                return
        sys.exit(tr("No se escaneó el QR en 3 minutos."))
    finally:
        QR_PNG.unlink(missing_ok=True)


def cmd_login(user_code):
    from tuya_sharing import LoginControl
    import qrcode
    ctl = LoginControl()
    resp = ctl.qr_code(CLIENT_ID, SCHEMA, user_code)
    if not resp.get("success"):
        sys.exit(tr("Tuya no dio el QR: {detail}", detail=resp.get('msg') or resp.get('code')))
    token = resp["result"]["qrcode"]
    HOME.mkdir(parents=True, exist_ok=True)
    qrcode.make(qr_payload(token)).save(QR_PNG)
    print(tr("QR listo: {path}", path=QR_PNG), flush=True)
    for _ in range(90):
        time.sleep(2)
        ok, info = ctl.login_result(token, CLIENT_ID, user_code)
        if ok:
            save_json(SESSION, {"user_code": user_code, "terminal_id": info["terminal_id"],
                                "endpoint": info["endpoint"], "token": info})
            QR_PNG.unlink(missing_ok=True)
            print(tr("Sesión guardada."), flush=True)
            return
    QR_PNG.unlink(missing_ok=True)
    sys.exit(tr("No se escaneó el QR en 3 minutos."))


def open_manager():
    from tuya_sharing import Manager, SharingTokenListener
    s = load_json(SESSION)

    class Tokens(SharingTokenListener):
        def update_token(self, token_info):   # Tuya renueva el token: se guarda para la próxima vez
            s["token"] = token_info
            save_json(SESSION, s)

    return Manager(CLIENT_ID, s["user_code"], s["terminal_id"], s["endpoint"], s["token"], Tokens())


def cmd_devices():
    m = open_manager()
    m.update_device_cache()
    old = load_json(DEVICES) if DEVICES.exists() else {}
    out = {}
    for dev_id, d in m.device_map.items():
        rec = {k: getattr(d, k, None) for k in
               ("id", "name", "local_key", "category", "product_id", "product_name", "online", "support_local", "ip")}
        rec["status"] = dict(getattr(d, "status", {}) or {})
        rec["function"] = {k: getattr(v, "type", None) for k, v in (getattr(d, "function", {}) or {}).items()}
        rec.update({k: v for k, v in old.get(dev_id, {}).items() if k in ("lan_ip", "version") and v})
        out[dev_id] = rec
    save_json(DEVICES, out)
    for rec in out.values():
        print(json.dumps(summarize(rec), ensure_ascii=False, default=str))


def cmd_scan():
    import tinytuya
    found = tinytuya.deviceScan(False, poll=False)
    devs = load_json(DEVICES)
    for ip, info in found.items():
        dev_id = info.get("gwId") or info.get("id")
        if dev_id in devs:
            devs[dev_id]["lan_ip"] = info.get("ip") or ip
            devs[dev_id]["version"] = str(info.get("version") or "")
    save_json(DEVICES, devs)
    for rec in devs.values():
        print(json.dumps(summarize(rec), ensure_ascii=False, default=str))


def cmd_listen(seconds):
    from tuya_sharing import SharingDeviceListener
    m = open_manager()
    m.update_device_cache()
    for d in m.device_map.values():
        d.set_up = True   # refresh_mq() solo se suscribe a los aparatos marcados (Home Assistant lo hace al crearlos)
    names = {i: d.name for i, d in m.device_map.items()}

    class Show(SharingDeviceListener):
        def update_device(self, device, updated_status_properties=None, dp_timestamps=None):
            changed = {k: device.status.get(k) for k in (updated_status_properties or [])}
            print(time.strftime("%H:%M:%S"), names.get(device.id, "?"), json.dumps(changed, ensure_ascii=False),
                  flush=True)

        def add_device(self, device):
            pass

        def remove_device(self, device_id):
            pass

    m.add_device_listener(Show())
    m.refresh_mq()
    print(tr("Escuchando {seconds} s desde {time}", seconds=seconds, time=time.strftime('%H:%M:%S')), flush=True)
    time.sleep(seconds)
    # Stop only the MQTT thread: Manager.unload() would log this terminal out (/v1.0/m/token/terminal/expire), and
    # it leaves that thread running, so the process never ends.
    if m.mq is not None:
        m.mq.stop()


def cmd_toggle(name):
    import tinytuya
    devs = load_json(DEVICES)
    # Names in the app may carry a trailing space («Luz Salón »).
    rec = next((r for r in devs.values() if (r.get("name") or "").strip().casefold() == name.strip().casefold()), None)
    if rec is None:
        sys.exit(tr("No hay ningún aparato llamado «{name}»", name=name))
    if not (rec.get("local_key") and rec.get("lan_ip")):
        sys.exit(tr("Falta su clave local o su IP en casa: ejecuta devices y scan antes"))
    d = tinytuya.OutletDevice(rec["id"], rec["lan_ip"], rec["local_key"], version=float(rec.get("version") or 3.3))
    on = (d.status().get("dps") or {}).get("1")
    if on is None:
        sys.exit(tr("El aparato no respondió en local (¿versión de protocolo o clave?)"))
    d.set_status(not on, 1)
    print(f"{rec['name']}: {tr('encendido') if not on else tr('apagado')}")


def main(argv):
    cmds = {"login": lambda a: cmd_login(a[0]), "devices": lambda a: cmd_devices(), "scan": lambda a: cmd_scan(),
            "listen": lambda a: cmd_listen(int(a[0]) if a else 120), "toggle": lambda a: cmd_toggle(" ".join(a)), "push": lambda a: cmd_push(),
            "tv-login": lambda a: cmd_tv_login(a[0])}
    if not argv or argv[0] not in cmds or (argv[0] in ("login", "toggle", "tv-login") and len(argv) < 2):
        sys.exit(tr(USAGE))
    cmds[argv[0]](argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
