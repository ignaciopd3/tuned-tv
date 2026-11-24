<div align="center">

# Tuned TV

**Every TV, tuned.**

Remove ads, bloat and tracking from your smart TV or streaming stick over your home network.
Measure the difference, and undo everything whenever you want. No root, nothing uninstalled.

[![tests](https://github.com/ignaciopd3/tuned-tv/actions/workflows/tests.yml/badge.svg)](https://github.com/ignaciopd3/tuned-tv/actions/workflows/tests.yml)
[![licence: MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](LICENSE)
![python 3.12+](https://img.shields.io/badge/python-3.12%2B-informational)
![Android TV · Google TV · Fire TV](https://img.shields.io/badge/Android%20TV%20%C2%B7%20Google%20TV%20%C2%B7%20Fire%20TV-supported-success)
![webOS · Tizen](https://img.shields.io/badge/webOS%20%C2%B7%20Tizen-guides-lightgrey)

**English** · [Español](README.es.md)

</div>

---

## Why

Smart TVs ship with apps nobody asked for. Many also report what you watch, including what comes in over HDMI (ACR),
and show ads on the home screen you paid for. All of that costs memory and CPU on a chip that was slow to begin with.
Tuned TV switches it off with the TV's own developer tools, one reviewed step at a time.

## What it does

- **Debloat without uninstalling.** Packages are disabled, never deleted, after a snapshot of the TV. Every run can be
  rolled back. Packages a TV needs (launchers, keyboards, Wi-Fi, HDMI, DRM, the TV app) are protected and the engine
  refuses to touch them.
- **Privacy settings.** Ad tracking limited, usage reports off, ACR off where it can be. Optionally, a private DNS that
  blocks ads and trackers for the whole TV.
- **Faster, measured.** `medir` (measure) records CPU, memory, swap and the busiest processes at idle, before and
  after, so you see what each change bought.
- **A clean home screen** (optional), built from [cleanyourtv](https://github.com/Gathin23/cleanyourtv)'s launcher
  with Tuned TV's patches: no suggestions or ads, your apps in your order, a clock, weather and remote buttons that
  do what you want. On Fire TV it even takes over the Home button, which Fire OS normally keeps to itself.
- **Per-model profiles.** Each TV model gets a folder with its lists, settings and notes, so the next person with that
  model starts from a tested setup. [Add yours](CONTRIBUTING.md).

## Supported systems

| System | Status | Guide |
|---|---|---|
| **Android TV / Google TV** (TCL, Sony, Xiaomi, Philips, Hisense Android, Chromecast, Shield…) | ✅ Supported, tested | [android-tv](docs/guides/android-tv.md) |
| **Fire OS** (Fire TV Stick, Cube, Fire TV Edition TVs) | ✅ Supported, tested | [fire-tv](docs/guides/fire-tv.md) |
| **LG webOS** | 📘 Guide ready; support on the way | [lg-webos](docs/guides/lg-webos.md) |
| **Samsung Tizen** | 📘 Guide ready; support on the way | [samsung-tizen](docs/guides/samsung-tizen.md) |

Roku, Hisense VIDAA and anything that needs root are out of scope.

### Tested models

| Model | System | Profile |
|---|---|---|
| TCL C845 (G05, MediaTek MT9615, EU) | Google TV 11 | [`profiles/tcl-c845-mt9615`](profiles/tcl-c845-mt9615/README.md) |
| Amazon Fire TV Stick 4K Max (1st gen, AFTKA) | Fire OS 7.7 | [`profiles/fire-tv-4k-max-aftka`](profiles/fire-tv-4k-max-aftka/README.md) |

Your model is not here? It can still work: start from the closest profile or from `profiles/_template`, and send it
back when it runs well.

## Quick start

**You need:** [uv](https://docs.astral.sh/uv/) (it brings its own Python), Android's
[`adb`](https://developer.android.com/tools/releases/platform-tools) on your PATH (or set `ADB` to its full path), and
the TV on the same network as your computer.

```bash
git clone https://github.com/ignaciopd3/tuned-tv.git
cd tuned-tv
uv sync
```

1. **Turn on debugging on the TV:** follow the [guide for your system](#supported-systems). Accept the "Allow
   debugging?" prompt the first time your computer connects.
2. **Point the tool at the TV:**
   ```bash
   export TV_SERIAL=<tv-ip>:5555          # Windows PowerShell: $env:TV_SERIAL = "<tv-ip>:5555"
   ```
3. **Measure first**, with the TV idle at its home screen:
   ```bash
   uv run run.py medir --perfil <profile>
   ```
4. **See the plan.** Nothing changes yet:
   ```bash
   uv run run.py motor --profile <profile> --action all --dry-run
   ```
5. **Apply it** when you agree with the plan, then measure again:
   ```bash
   uv run run.py motor --profile <profile> --action all
   uv run run.py medir --perfil <profile>
   ```
6. **Undo** at any time:
   ```bash
   uv run run.py motor --profile <profile> --action rollback --all
   ```

Actions: `audit` (read only), `debloat`, `optimize` (settings, app permissions, log levels), `remap` (remote
buttons), `all`, `rollback`. Add `--include-caution` for the optional packages in `packages.caution`.

**When you are done, turn debugging off again** (Developer options → USB/Network/ADB debugging off). Network ADB is
plain text, and on some firmware anyone on your network gets a shell. The changes and the clean home keep working
without it.

## The launcher

`uv run run.py launcher --perfil <profile>` builds the clean home screen and installs it, with its add-ons and the
profile's theme (`profiles/<profile>/launcher/config.json`). It is cached, so it only rebuilds when the patches change,
and it waits until the TV's home screen is in front before installing.

To build it you also need:

- **JDK 17** (set `JAVA_HOME`) and the **Android SDK** with platform 34 (set `ANDROID_HOME`);
- **a clone of cleanyourtv** next to this repo (`../cleanyourtv`, or set `CYT_DIR`), with its tools environment:
  `python3 -m venv tools/venv && tools/venv/bin/pip install -r tools/requirements.txt` inside that clone;
- **a stable signing key** (`~/.android/debug.keystore` by default). Android only updates an app signed with the same
  key, so keep a copy.

The patches live in [`launcher/patches/`](launcher/patches/), on top of the cleanyourtv version in
[`launcher/patches/BASE`](launcher/patches/BASE). [How it works](docs/how-it-works.md#the-launcher) explains each piece.

## Safety

- **No root and nothing written to `/system`.** A factory reset always brings the TV back to stock.
- **Disable, don't uninstall.** The rare exception, a persistent package that restarts while disabled, is removed for
  your user only (`pm uninstall -k --user 0`) and comes back with `cmd package install-existing`.
- **A snapshot before every change, verification after it, and a rollback for every run.**
- **Protected packages** ([`lib/protected.list`](lib/protected.list)) cannot be touched by any profile.
- **Dry run first.** The plan is printed and saved before anything happens.

Disabling packages can still break features you rely on (voice search goes with the assistant, for example). Every
profile explains what each line costs. Read it before applying, and keep debugging switched off when you are not
using it.

## FAQ

<details>
<summary><b>An update brought everything back.</b></summary>

Updating a system app re-enables it. Run the same profile again with `--dry-run`: if the plan is not empty, apply it.
On Fire TV, Amazon's updater does this every few weeks.
</details>

<details>
<summary><b>Will this void my warranty?</b></summary>

It only uses the developer settings the TV itself offers, and a factory reset removes every change. Warranty terms
differ by brand and country, so check yours if it matters.
</details>

<details>
<summary><b>Can I just remove everything?</b></summary>

No. Some packages look useless but carry the TV's input switching, DRM or remote handling. Profiles only list packages
that were disabled on that model without side effects, and the riskier ones wait in `packages.caution`.
</details>

<details>
<summary><b>Why does the tool say "medir" and "motor"?</b></summary>

The project started in Spanish: `medir` means measure and `motor` means engine. The code and its comments are still in
Spanish; the documentation is in both languages.
</details>

## Contributing

The most valuable contribution is a **profile for a TV model** that is not here yet. [CONTRIBUTING.md](CONTRIBUTING.md)
walks you through it: identify the model, start from the template, dry run, apply, measure and write its notes. Bugs
and ideas go in [issues](https://github.com/ignaciopd3/tuned-tv/issues/new/choose).

## Credits

Tuned TV builds on the work of
[cleanyourtv](https://github.com/Gathin23/cleanyourtv) (Android TV debloat lists and the launcher),
[dumbtv](https://github.com/humblemuzzu/dumbtv) (Fire OS lists and the Home button takeover) and
[free-my-tv](https://github.com/simbasjungles/free-my-tv) (LG webOS and Samsung Tizen).
Details and licences are in [CREDITS.md](CREDITS.md).

## Licence

[MIT](LICENSE). Some data and images are under their own licences (CC BY-SA 4.0 for dumbtv's device catalogue,
CC BY and CC BY-SA for the wallpapers): see [CREDITS.md](CREDITS.md).
