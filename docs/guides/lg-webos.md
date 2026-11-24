# LG webOS

[Español](lg-webos.es.md) · [Back to the README](../../README.md)

**Applies to** LG TVs with webOS 3 or newer.

**Status:** 📘 guide ready; Tuned TV does not automate webOS yet. Until it does, this guide covers what you can do
today, mostly with [free-my-tv](https://github.com/simbasjungles/free-my-tv) (MIT). Support in Tuned TV will build on a
pinned version of it.

## What is possible without root

- **Turn off tracking** in the TV's own settings. This is the biggest privacy win, and it needs nothing else.
- **Install a clean home app** through LG's Developer Mode (free-my-tv), so you start on your apps instead of LG's
  shelves of suggestions.
- **Not possible:** removing or disabling LG's preinstalled apps. webOS does not allow it without root, and rooting is
  out of scope here.

## 1. Turn off tracking

Names and places change from year to year; look for these:

- **Live Plus** (ACR, the service that recognises what is on screen): Settings → All settings → General → System →
  Additional settings → Live Plus → Off.
- **User agreements:** Settings → All settings → Support → Privacy & Terms → User Agreements. Untick *Viewing
  Information*, *Voice Information* and *Interest-Based Advertising*.
- **Ad tracking:** under the same privacy menus, *Limit Ad Tracking* → On.
- **Home promotion and auto-play:** in the home settings, turn off *Home Promotion*, *Content Recommendation* and
  auto-play where they appear.

## 2. Turn on Developer Mode

1. Create a free LG developer account at [webostv.developer.lge.com](https://webostv.developer.lge.com).
2. On the TV, open the LG Content Store, install **Developer Mode** and sign in with that account.
3. Turn on **Dev Mode Status**; the TV restarts.
4. Open Developer Mode again and turn on **Key Server**.
5. Note the TV's IP address and the passphrase the app shows.

**Developer Mode expires after about 40 days.** Renew it with the **EXTEND** button in the app or with free-my-tv's
`renew.py`, which needs the TV on and reachable and the key `install.py` saved. Renewing weekly is enough, and
`renew.py` prints a cron line (macOS and Linux) or a Task Scheduler line (Windows).

## 3. Install a clean home with free-my-tv

You need Python 3 and the TV on the same Wi-Fi as the computer. From a clone of free-my-tv:

```bash
python3 webos/apps.py <tv-ip>       # reads the installed apps (needed on webOS 3)
python3 webos/build.py              # packs the app and config.properties into an .ipk, no LG tools needed
python3 webos/install.py <tv-ip>    # installs it through Developer Mode; asks for the passphrase the first time
python3 webos/renew.py <tv-ip>      # extends Developer Mode
python3 webos/install.py <tv-ip> --uninstall
```

Good to know:

- On **webOS 6 and newer**, the app cannot list installed apps until you allow access once; until then it shows
  well-known apps.
- On non-4K TVs it installs at 1280 × 720.
- Holding a number key on the remote while the app is open lets you open it from anywhere.

## Planned in Tuned TV

- A `tvopt/webos` adapter over a pinned free-my-tv: connection steps, inventory (system info and apps), the launcher
  install and Developer Mode renewal, with the same profile and dry-run flow as the other systems.
- A model profile for each LG model someone tests: [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Credits

Developer Mode steps, renewal and tooling from [free-my-tv](https://github.com/simbasjungles/free-my-tv) (MIT).
