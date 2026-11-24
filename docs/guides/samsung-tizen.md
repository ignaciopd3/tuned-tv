# Samsung Tizen

[Español](samsung-tizen.es.md) · [Back to the README](../../README.md)

**Applies to** Samsung TVs with Tizen, from 2015. Orsay models (older Samsung smart TVs) cannot run third-party apps.

**Status:** 📘 guide ready; Tuned TV does not automate Tizen yet. Until it does, this guide covers what you can do
today, mostly with [free-my-tv](https://github.com/simbasjungles/free-my-tv) (MIT). Support in Tuned TV will build on a
pinned version of it.

## What is possible without root

- **Turn off tracking** in the TV's own settings. This is the biggest privacy win, and it needs nothing else.
- **Install a clean home app** in Developer Mode (free-my-tv).
- **Not possible:** removing or disabling Samsung's preinstalled apps.

## 1. Turn off tracking

Names and places change from year to year. On recent models they are under Settings → All settings → General &
Privacy → Terms & Privacy (older models: Settings → Support → Terms & Policy):

- **Viewing Information Services** (ACR) → Off.
- **Interest-Based Advertisement** → Off; reset the advertising ID if offered.
- **Voice recognition services** → Off if you do not use voice.
- In Smart Hub's settings, turn off auto-run of Smart Hub and auto-play of promoted content where they appear.

## 2. Turn on Developer Mode

1. Open **Apps** on the TV and type **1 2 3 4 5** on the remote.
2. Turn **Developer mode** on.
3. In **Host PC IP**, enter your computer's IP address.
4. Restart the TV (unplug it or hold the power button until it reboots).

## 3. Install a clean home with free-my-tv

**Option A: TizenBrew.** Use TizenBrew Installer (by @reisxd), connect to the TV and add the module
`simbasjungles/free-my-tv`. On 2023 and newer TVs you sign in to a Samsung account once. 2015 and 2016 TVs cannot run
TizenBrew; use option B.

**Option B: build and install it yourself** (Python only, no Tizen Studio):

```bash
python3 tizen/build.py                       # builds FreeMyTV-tizen.wgt
python3 tizen/install.py <tv-ip>             # installs it (also explains why an install failed)
python3 tizen/install.py <tv-ip> --uninstall
```

On 2023 and newer TVs, the signing certificate comes from signing in to your Samsung account in the browser.

**Known issues** (from free-my-tv's reports):

| Message or model | Meaning |
|---|---|
| `download failed[116]` | The TV is out of free storage for apps. |
| `failed[118]` (e.g. some 2016 models) | See free-my-tv's `tizen/install-118.md`. |
| 2017–2018 TVs (Tizen 3 and 4) | Opening TV Settings from the launcher can freeze. |
| 2019–2020 TVs | "Autorun last app" does not reopen the launcher after power-on. |

## Planned in Tuned TV

- A `tvopt/tizen` adapter over a pinned free-my-tv: connection steps, inventory (the device info the TV publishes on
  port 8001, and apps), launcher install, with the same profile and dry-run flow as the other systems.
- A model profile for each Samsung model someone tests: [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Credits

Developer Mode steps, tooling and the known issues come from [free-my-tv](https://github.com/simbasjungles/free-my-tv)
(MIT) and its contributors; TizenBrew is by @reisxd.
