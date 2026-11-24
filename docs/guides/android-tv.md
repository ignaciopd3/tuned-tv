# Android TV and Google TV

[Español](android-tv.es.md) · [Back to the README](../../README.md)

**Applies to** TVs and boxes running Android TV or Google TV: TCL, Sony Bravia, Xiaomi (Mi TV and Mi Box), Philips
(Android models), Hisense (Android models, not VIDAA), Sharp, Toshiba, Nokia, Chromecast with Google TV, Google TV
Streamer, NVIDIA Shield, onn and many more. Android 8 or newer.

**Status:** ✅ supported and tested (TCL C845 on Google TV 11).

## 1. Turn on developer options

Menu names change between brands and firmware versions. What you are looking for is the **build number** in the
"About" screen; pressing OK on it seven times unlocks developer options.

| Your TV runs | Path |
|---|---|
| **Google TV** (most TVs from 2021, Chromecast with Google TV, Google TV Streamer) | Settings → System → About → **Android TV OS build** → press OK 7 times. Developer options appear under Settings → System. |
| **Android TV** (classic menus: Sony, Philips, Xiaomi, Shield…) | Settings → Device Preferences → About → **Build** → press OK 7 times. Developer options appear under Device Preferences. |

If the TV asks for your PIN, enter it. A message such as "You are now a developer" confirms it.

## 2. Turn on debugging

In **Developer options**:

- Turn on **USB debugging**. On most TVs this also opens network ADB on port 5555, which is what Tuned TV uses.
- If you see **Network debugging** or **ADB debugging** (NVIDIA Shield, some Sony and Philips sets), turn it on too.
- **Wireless debugging with a pairing code** (Chromecast with Google TV, Google TV Streamer, and boxes where port 5555
  stays closed): open *Wireless debugging → Pair device with pairing code*. On the computer:
  ```bash
  adb pair <tv-ip>:<pairing-port>      # type the code the TV shows
  adb connect <tv-ip>:<port>           # the port on the Wireless debugging screen
  adb tcpip 5555                       # optional: opens 5555 until the next reboot
  ```

## 3. Find the IP address and connect

- The IP address is in Settings → Network & Internet → your network, or in About → Status.
- Connect, then accept **"Allow USB debugging?"** on the TV. Tick "Always allow from this computer" so it does not
  ask every time.
  ```bash
  adb connect <tv-ip>:5555
  adb devices                          # should list <tv-ip>:5555   device
  export TV_SERIAL=<tv-ip>:5555
  ```
- Give the TV a fixed address in your router (DHCP reservation), so `TV_SERIAL` never changes.

## 4. Identify the exact model

A profile matches a TV by one system property, so it never runs on the wrong model:

```bash
adb shell getprop ro.product.manufacturer
adb shell getprop ro.product.model
adb shell getprop ro.board.platform        # the chip
adb shell getprop ro.build.version.release # Android version
adb shell getprop | grep -i -E "client_type|product.name|device"
```

Some brands put a vague name in `ro.product.model` (the TCL C845 only says "Smart TV Pro"). Then pick a more precise
property, such as `persist.tcl.client_type` on TCL.

## What Tuned TV does on Android TV

- **The engine** (`run.py engine`): it disables packages, applies settings, app permissions (`appops`) and log levels,
  and remaps buttons where the firmware allows it. It takes a snapshot first and lets you roll back every run.
- **Measuring** (`run.py measure`): CPU, memory, swap and the busiest processes, at idle.
- **The launcher** (`run.py launcher`): replaces the home screen, including Google TV's, and its suggestions. It adds a
  clock, weather and remote-button actions, and installs add-ons.

**Not listed yet?** [cleanyourtv](https://github.com/Gathin23/cleanyourtv) keeps tested debloat lists for about 400
models (search [cleanyour.tv/tvs](https://cleanyour.tv/tvs)). They are the best starting point for a new profile:
see [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Common problems

| Symptom | What to do |
|---|---|
| `connection refused` on port 5555 | Debugging is off, the TV rebooted (wireless debugging closes 5555 again) or the IP changed. |
| `unauthorized` | Accept the prompt on the TV. If it never shows, turn USB debugging off and on, revoke the authorisations in Developer options and connect again. |
| Play Protect blocks an APK (Android 14) | "More details" → "Install anyway". |
| An add-on does not start on TCL | TCL blocks background start for installed apps; `run.py launcher` allows it (`APP_AUTO_START allow`). |
| A firmware update brought packages back | Run the profile again with `--dry-run`, then apply it. |

## Turn debugging off when you are done

Developer options → turn **USB debugging**, **Network debugging** and **Wireless debugging** off, whichever your TV
has, and revoke the debugging authorisations. Network ADB is plain text, and on some firmware anyone on your network
gets a shell. Everything you changed keeps working.

## Credits

Steps and model lists from [cleanyourtv](https://github.com/Gathin23/cleanyourtv) (MIT) and
[free-my-tv](https://github.com/simbasjungles/free-my-tv) (MIT).
