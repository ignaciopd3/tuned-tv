#!/usr/bin/env python3
"""Reordena y oculta canales en «Editar canales» de una TCL (com.tcl.tv) por ADB.

TvProvider no admite escritura desde el shell (WRITE_EPG_DATA es un permiso de firma), así que se
maneja la pantalla nativa: casilla → OK → «Intercambiar» (2.ª opción) → mover → OK, y OK → «Ocultar».
El cursor es la casilla cuyo ojo es `iv_chmg_*_icon_focus`; cada intercambio se verifica leyendo los
nombres de las casillas en un volcado de uiautomator. El editor se cierra solo a los 15 s sin teclas.

Uso: USAGE, más abajo.
"""
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # para tvopt.core.i18n al lanzarlo como script
from tvopt.core.i18n import tr  # noqa: E402

USAGE = """Uso:  python tools/tcl_channels.py <mapa.txt> [--dry-run] [--check-every N]
  --check-every N: lee la pantalla solo cada N intercambios (10 por defecto); los demás van a ciegas
  con movimientos deterministas, y al final una lectura completa replanifica lo que falte.
  mapa.txt: un nombre por línea, en el orden deseado (los nombres repetidos se repiten); «!» delante
  oculta ese canal. Los canales que no aparezcan quedan detrás, en su orden actual. Las radios
  (diales ≥ 1000) no se tocan.
Entorno: ADB (ruta a adb), TV_SERIAL (ip:puerto).
"""
ADB = os.environ.get("ADB", "adb")
SERIAL = os.environ.get("TV_SERIAL") or sys.exit(tr("Indica la tele con la variable TV_SERIAL (ip:puerto)"))
ROWS = 7                                  # casillas por columna en la cuadrícula
MANAGER = "com.tcl.tv/.channelmanager.ChannelManagerActivity"
ID = "com.tcl.tv:id/"


def sh(cmd):
    r = subprocess.run([ADB, "-s", SERIAL, "shell", cmd], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout.replace("\r", "")


def key(name, pause=0.35):
    sh(f"input keyevent KEYCODE_{name}")
    time.sleep(pause)


def screen():
    """Volcado: casillas {dial: (nombre, oculto)}, dial con el cursor y texto de la cabecera."""
    xml = sh("uiautomator dump /data/local/tmp/u.xml >/dev/null 2>&1; cat /data/local/tmp/u.xml")
    cells, cursor, header = {}, None, ""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return cells, cursor, header
    for node in root.iter("node"):
        rid = node.get("resource-id", "")
        if rid == ID + "id_key_ok":
            header = node.get("text", "")
        if rid != ID + "channel_manager_item_content":
            continue
        num = name = None
        focus = hidden = False
        for child in node.iter("node"):
            cid = child.get("resource-id", "")
            if cid == ID + "tv_chmg_item_num":
                num = child.get("text")
            elif cid == ID + "tv_chmg_item_name":
                name = child.get("text")
            elif "_icon_" in cid and cid.startswith(ID + "iv_chmg_"):
                focus |= cid.endswith("_focus")
                hidden |= "_no_hide_" not in cid
        if num and num.isdigit():
            cells[int(num)] = (name or "", hidden)
            if focus:
                cursor = int(num)
    return cells, cursor, header


def is_open():
    return "ChannelManager" in sh("dumpsys window | grep -m1 mCurrentFocus")


def open_editor():
    """Abre el editor (o cancela un intercambio a medias) y devuelve el dial con el cursor."""
    if is_open():
        _, cur, header = screen()
        if header != "Confirmar" and cur:
            return cur
        key("BACK", 1.2)                  # cancela el modo intercambio
        if is_open():
            _, cur, _ = screen()
            if cur:
                return cur
            key("BACK", 1.5)
    sh(f"am start -n {MANAGER} >/dev/null 2>&1")
    time.sleep(3)
    for _ in range(4):
        _, cur, _ = screen()
        if cur:
            return cur
        time.sleep(0.8)
    sys.exit(tr("No encuentro el cursor en el editor de canales"))


def move(c, t):
    """Teclas de c a t: columnas de ROWS casillas; sube antes de cambiar de columna (la última es más corta)."""
    cc, cr, tc, tr = (c - 1) // ROWS, (c - 1) % ROWS, (t - 1) // ROWS, (t - 1) % ROWS
    for _ in range(max(cr - tr, 0)):
        key("DPAD_UP")
    for _ in range(abs(tc - cc)):
        key("DPAD_RIGHT" if tc > cc else "DPAD_LEFT")
    for _ in range(max(tr - cr, 0)):
        key("DPAD_DOWN")


def goto(c, t):
    """Mueve el cursor a t y lo confirma con el ojo enfocado; devuelve el dial real."""
    for _ in range(5):
        if c != t:
            move(c, t)
        time.sleep(0.4)
        _, real, _ = screen()
        if real == t:
            return t
        if real is None:                  # el editor se cerró solo (15 s): se reabre y se sigue
            real = open_editor()
        c = real
    return c


def read_all(cur):
    """Lee todas las casillas de TV recorriendo las columnas; devuelve ({dial: (nombre, oculto)}, cursor)."""
    cur = goto(cur, 1)
    tv, stale = {}, 0
    while stale < 2:                      # hasta ver radios o dos lecturas sin canales nuevos
        cells, real, _ = screen()
        cur = real or cur
        before = len(tv)
        tv.update({n: v for n, v in cells.items() if n < 1000})
        if any(n >= 1000 for n in cells):
            break
        stale = stale + 1 if len(tv) == before else 0
        key("DPAD_RIGHT", 0.6)
    _, real, _ = screen()
    return tv, real or cur


def parse_map(path):
    order, hide = [], []
    for line in open(path, encoding="utf-8"):
        name = line.split("#")[0].strip()
        if not name:
            continue
        if name.startswith("!"):
            name = name[1:].strip()
            hide.append(len(order) + 1)
        order.append(name)
    return order, hide


def plan(tv, order):
    """Intercambios (p, q) para llevar tv a `order` en los diales 1..len(order); el resto queda detrás."""
    at = {p: tv[p][0] for p in tv}
    swaps = []
    for p, want in enumerate(order, 1):
        if at.get(p) == want:
            continue
        q = next((q for q in sorted(at) if q > p and at[q] == want), None)
        if q is None:
            sys.exit(tr("«{name}» no está en la TV (o no quedan más copias) para el dial {dial}", name=want, dial=p))
        swaps.append((p, q))
        at[p], at[q] = at[q], at[p]
    return swaps, at


def swap(cur, p, q, tv_names):
    cur = goto(cur, p)
    if cur != p:
        return cur, f"no pude situarme en {p}"
    key("DPAD_CENTER", 0.9)
    key("DPAD_DOWN", 0.4)                 # el menú abre en «Ocultar»; la 2.ª opción es «Intercambiar»
    key("DPAD_CENTER", 0.9)
    move(p, q)
    key("DPAD_CENTER", 1.3)
    cells, real, _ = screen()
    expect_q, expect_p = tv_names[p], tv_names[q]
    if q in cells and cells[q][0] != expect_q:
        return real or q, f"en {q} hay «{cells[q][0]}» (esperaba «{expect_q}»)"
    if p in cells and cells[p][0] != expect_p:
        return real or q, f"en {p} hay «{cells[p][0]}» (esperaba «{expect_p}»)"
    tv_names[p], tv_names[q] = expect_p, expect_q
    return real or q, None


def swap_fast(cur, p, q):
    """Intercambio sin leer la pantalla: movimientos deterministas (±7 columnas, ±1 filas). Cursor final: q."""
    move(cur, p)
    key("DPAD_CENTER", 0.9)
    key("DPAD_DOWN", 0.4)
    key("DPAD_CENTER", 0.9)
    move(p, q)
    key("DPAD_CENTER", 1.0)
    return q


def run_swaps(cur, swaps, names, every):
    """Intercambia leyendo la pantalla solo cada `every` intercambios (y en el primero)."""
    for i, (p, q) in enumerate(swaps, 1):
        if i == 1 or i % every == 0:
            if not is_open():
                cur = open_editor()
            cur, err = swap(cur, p, q, names)
            print(f"{i:>2}. {p} <-> {q} {tr('OK (comprobado)') if not err else 'ERROR: ' + err}", flush=True)
            if err:
                return cur, False
        else:
            cur = swap_fast(cur, p, q)
            names[p], names[q] = names[q], names[p]
            print(f"{i:>2}. {p} <-> {q}", flush=True)
    return cur, True


def main():
    if len(sys.argv) < 2:
        sys.exit(tr(USAGE))
    order, hide = parse_map(sys.argv[1])
    dry = "--dry-run" in sys.argv
    every = int(sys.argv[sys.argv.index("--check-every") + 1]) if "--check-every" in sys.argv else 10
    cur = open_editor()
    for attempt in range(3):              # si un punto de control falla, se relee todo y se replanifica
        tv, cur = read_all(cur)
        swaps, _ = plan(tv, order)
        print(tr("{channels} canales leídos · {swaps} intercambios pendientes", channels=len(tv), swaps=len(swaps)), flush=True)
        if dry or not swaps:
            break
        cur, ok = run_swaps(cur, swaps, {p: v[0] for p, v in tv.items()}, every)
        if ok:
            tv, cur = read_all(cur)       # comprobación final completa
            left, _ = plan(tv, order)
            if not left:
                break
            print(tr("Comprobación final: quedan {left}; replanifico", left=len(left)), flush=True)
    if dry:
        return
    names = {p: v[0] for p, v in tv.items()}
    for p in hide:
        if not is_open():
            cur = open_editor()
        cur = goto(cur, p)
        cells, _, _ = screen()
        if cells.get(p, ("", False))[1]:
            print("  " + tr("{dial} {name} ya estaba oculto", dial=p, name=names[p]))
            continue
        key("DPAD_CENTER", 0.9)
        key("DPAD_CENTER", 1.0)           # 1.ª opción: «Ocultar»
        cells, _, _ = screen()
        print("  " + tr("ocultar {dial} {name}: {result}", dial=p, name=names[p],
                         result="OK" if cells.get(p, ("", False))[1] else tr("sin confirmar")), flush=True)
    key("BACK", 1.5)


if __name__ == "__main__":
    main()
