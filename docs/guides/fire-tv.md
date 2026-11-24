# Fire TV (Fire OS)

[Español](fire-tv.es.md) · [Back to the README](../../README.md)

**Applies to** Amazon Fire TV Stick (all generations, including 4K and 4K Max), Fire TV Cube and Fire TV Edition TVs.
dumbtv has tested Fire OS 6.2 to 8.1.

**Status:** ✅ supported and tested (Fire TV Stick 4K Max, Fire OS 7.7).

## 1. Turn on ADB debugging

1. Settings → **My Fire TV** → **About** → press OK on the **device name** 7 times, until it says you are a developer.
2. Back to My Fire TV → **Developer Options** → **ADB debugging** → On.
3. The IP address is in Settings → My Fire TV → About → **Network**. On Fire TV Edition TVs, use Settings → Network →
   the connected network.

## 2. Connect

```bash
adb connect <tv-ip>:5555
export TV_SERIAL=<tv-ip>:5555
```

Accept the **Allow USB debugging?** prompt on the TV (tick "Always allow from this computer"). To identify the model:
`adb shell getprop ro.product.model` (for example `AFTKA` is the Fire TV Stick 4K Max, 1st gen).

## What Tuned TV does on Fire OS

- **Disables Amazon's ads, telemetry, ACR, promos and forced updates**, plus the Amazon apps you do not use. Fire OS
  has no `install-existing`, so nothing is uninstalled and `--action rollback` brings everything back.
- **Packages Amazon protects** cannot be disabled without root: metrics, crash reports, remote management, ad links,
  remote support and the OTA updater. Tuned TV takes away their background work (`appops RUN_IN_BACKGROUND ignore`).
- **Privacy settings:** ad tracking limited, interest-based ads off, usage reporting off, home-screen autoplay off, and
  optionally a private DNS that blocks ads and trackers.
- **A clean home**, optional. Fire OS does not let you choose another home app, so the launcher's accessibility
  service watches for Amazon's home and replaces it in about 0.4 s, under a cover. It also comes back by itself after
  a force stop. Details and the model's quirks are in the
  [Fire TV Stick 4K Max profile](../../profiles/fire-tv-4k-max-aftka/README.md).

## Fire OS limits worth knowing

- **Updates re-enable what you disabled.** Updating a system app turns it back on, and Amazon's updater does it every
  few weeks. Check with `--dry-run` and apply again if the plan is not empty.
- **Leaving a screensaver force-stops the package that provides it.** Do not use the launcher as the system
  screensaver on Fire OS. The profile turns the system screensaver off and lets the launcher show its own clock.
- **The remote's TV button (LIVE_TV, code 297) reaches no app.** Fire OS opens its own Live TV screen. The launcher's
  `redirect_apps` can send that screen to any app.
- **YouTube ads cannot be blocked by DNS**: they come from the same servers as the videos. Alternative YouTube clients
  are the usual way out.
- **Fire OS cannot be replaced.** Amazon locks the boot chain, so changes live on top of Fire OS and a factory reset
  removes them.
- **The Fire TV phone app as a remote** needs `com.amazon.whisperlink.core.android` with background work allowed.
  Keep it if you travel without the remote.

## Alternatives and extras

[dumbtv](https://github.com/humblemuzzu/dumbtv) is a complete Fire OS toolkit with its own launcher. Its optional
**DNS filter** (personalDNSfilter, about 400 Amazon telemetry, ad and update hosts) also stops Fire OS updates while
it runs. It uses Android's only VPN slot, so it cannot run next to another VPN app. Its `contribute.sh` writes a device
report for untested models.

## Turn ADB off when you are done

Developer Options → ADB debugging → Off. The launcher and the changes keep working.

## Credits

The package lists, the privacy settings, the protected-package list and the accessibility approach to the Home button
come from [dumbtv](https://github.com/humblemuzzu/dumbtv) (code MIT, device catalogue CC BY-SA 4.0).
