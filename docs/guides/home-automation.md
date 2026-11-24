# Smart home: your house on the TV

[Español](home-automation.es.md) · [Back to the README](../../README.md)

The **Casa** add-on connects the TV to **Smart Life / Tuya** devices. It alerts you on screen, over whatever you are
watching, and lets you switch the light or the heater from the home screen or with a remote button. It installs with
the launcher (`run.py launcher`) on Android TV, Google TV and Fire TV.

| | What it does | How it arrives |
|---|---|---|
| 🚪 **Door** | Alerts when it opens, reminds you every 5 minutes while it stays open, and tells you when it closes and for how long it was open. | Tuya cloud, instantly |
| 🔥 **Gas** | Darkens the screen, shows a large red alarm and beeps every 3 seconds until you press OK. | Home network, instantly |
| 💡 **Light** · ♨️ **Heater** | Buttons on the home screen, next to the top bar, and on a remote button if you want. | Home network, no internet |
| 🌡️ **Temperature and humidity** | Your home's, on the home screen and the idle clock, beside the weather outside. | Tuya cloud |

Alerts show over any channel, app or HDMI input, while the TV is on.

## What you need

**Smart devices at home.** The TV detects nothing on its own: each feature needs its device, added to the **Smart
Life** app (or Tuya Smart). Look for "Smart Life" or "Tuya" on the box. Add only the ones you want; what you don't have
is left out.

| For | You need |
|---|---|
| 💡 Light | A **Wi-Fi smart plug**, with the lamp plugged in and switched on at its own switch. |
| ♨️ Heater | Another **Wi-Fi smart plug** rated for its power (check the heater's watts; many plugs take 16 A, about 3,600 W), with the heater switched on at its own switch. |
| 🚪 Door | A Wi-Fi **door or window (contact) sensor**. |
| 🔥 Gas | A **Wi-Fi gas detector**, plugged into the mains. |
| 🌡️ Temperature and humidity | A Wi-Fi **temperature and humidity sensor**. |

Tested with Wi-Fi devices, without a Zigbee gateway. The gas alert on the TV is an extra warning: it **does not replace** a
certified gas detector with its own alarm.

Also:

- Tuned TV's launcher installed ([the launcher](../../README.md#the-launcher)).
- On the computer, a separate Python environment with the Tuya libraries. It lives outside the repo, because it keeps
  your session:
  ```bash
  python -m venv ~/Documents/casa-tuya/venv
  ~/Documents/casa-tuya/venv/bin/pip install tuya-device-sharing-sdk tinytuya qrcode   # Windows: venv\Scripts\pip
  ```
  `CASA_DIR` changes the folder; the default is `~/Documents/casa-tuya`. In the steps below, `casa` means
  `~/Documents/casa-tuya/venv/bin/python tools/casa_probe.py`.

## Set it up

1. **Sign in with your Smart Life account.** In the app, *Me → Settings → Account and Security → User Code*. Then:
   ```bash
   casa login <code>          # leaves qr.png in the Casa folder: scan it with the Smart Life app
   casa devices               # lists your devices
   casa scan                  # finds them on the home network (local IP and protocol version)
   ```
2. **Say which device is which** in `roles.json`, inside the Casa folder, with their names in the app. Drop the lines
   for what you don't have. The keys are Casa's roles and stay as they are (`luz` light, `calefactor` heater, `puerta`
   door, `gas`, `clima` climate):
   ```json
   {"luz": "Living room light", "calefactor": "Heater", "puerta": "Front door", "gas": "Gas sensor", "clima": "Thermometer"}
   ```
3. **Send it to the TV**, with debugging on and `TV_SERIAL` set:
   ```bash
   casa push                  # sends the devices to Casa and lets it show alerts over everything
   casa tv-login <code>       # new QR: a cloud session for the TV only (door and climate); the PC doesn't keep it
   ```
4. **Show it on the home screen.** In your profile's `launcher/config.json`:
   ```json
   "casa_row": "io.github.ignaciopd3.casa",
   "app_keys": ["KEYCODE_PROG_YELLOW:io.github.ignaciopd3.casa/.LuzActivity"]
   ```
   `app_keys` is optional: here the yellow button switches the light. For the heater, `.CalefactorActivity`. Then
   `uv run run.py launcher --profile <profile>`.
5. **Try the alerts** without opening the real door:
   ```bash
   adb shell am start -n io.github.ignaciopd3.casa/.ImportActivity --es simulate puerta   # or sigue, cerrada
   ```
   `simulate gas` sounds the alarm at full volume (`gas-normal` clears it). Warn the household before you try it.

## Privacy

- **Your session and the devices' keys** stay in the Casa folder and on the TV. The tool refuses to save them inside
  the repo and never prints them.
- **The light, the heater and the gas sensor** go over the home network with Tuya's local protocol. They keep working
  if the internet goes down.
- **The door and climate sensors** come from Tuya's cloud: they run on batteries and only talk to it. Access uses the
  same official device-sharing system as Home Assistant's Tuya integration (a QR code you approve in the app).

## Limits

- Smart Life / Tuya only for now. **Home Assistant support is on the way.**
- Alerts need the TV to be on.
- Casa speaks English and Spanish and follows the TV's language; on a TV in another language it shows English.
  Translations are welcome (see [CONTRIBUTING.md](../../CONTRIBUTING.md#translations)).
- Tested on a TCL with Google TV and a Fire TV Stick 4K Max.
