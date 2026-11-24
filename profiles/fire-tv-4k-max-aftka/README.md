# Fire TV Stick 4K Max (1st gen, 2021) · AFTKA

[Español](README.es.md)

| | |
|---|---|
| Model | AFTKA "kara" (`ro.product.model`) |
| System | Fire OS 7.7.1.3 (PS7713/5443), based on Android 9 (SDK 28) |
| Chip | MediaTek MT8696, 4 cores, 32-bit (`armeabi-v7a`) |
| Memory | 1.7 GB |
| Keyboard | `com.amazon.tv.ime` (the engine always protects the active keyboard) |
| Connection | ADB over Wi-Fi, port 5555 ([Fire TV guide](../../docs/guides/fire-tv.md)) |
| Tested | November 2026, on one stick; the package list comes from dumbtv, tested on three sticks with this firmware |

## What this profile does

**Disables 58 packages** (`packages.remove`). Nothing is uninstalled: this firmware has no `install-existing`, so
everything is disabled and comes back with `--action rollback`.

- **Ads and the advertising ID**, telemetry and metrics.
- **ACR**: the service that recognises what you watch, including what comes in over HDMI.
- **Promos**, the in-TV store banners and notices.
- **Forced Fire OS updates**: the stick no longer updates by itself. Amazon updates bring new ads, but you also stop
  getting fixes; see [Updates](#updates-re-enable-what-you-disabled).
- **Alexa**: the microphone button on the remote does nothing afterwards.
- **Amazon apps** for Music, Photos, Games, Luna, Silk, Kids, Help, printing and miniTV.
- **Amazon's screensaver** and TV-provider sign-in.

**Kept on purpose:** Prime Video (`com.amazon.firebat`, in `lib/protected.list`), the Appstore (`com.amazon.venezia`),
Amazon's home (it also holds the Fire TV settings), notifications, WebView and everything in `lib/protected.list`.

**Packages Amazon protects** cannot be disabled without root: metrics, crash reports, remote management, ad links,
remote support and the OTA updater. `appops.conf` takes away their background work instead (`RUN_IN_BACKGROUND
ignore`).

**Settings** (`settings.conf`):

- Ad tracking limited, no personalised ads, no usage-data upload.
- No heads-up notifications, no featured video that plays by itself.
- Animations at 0.25.
- Private DNS with ad and tracker blocking (`p2.freedns.controld.com`).
- **No system screensaver.** On Fire OS, leaving a screensaver force-stops the package that provides it; see
  [quirks](#fire-os-quirks-worth-knowing). The launcher shows its own clock after 3 minutes idle on Home instead, and
  the screen still sleeps after 20 minutes (`screen_off_timeout` = `sleep_timeout`).

## Results

In [`results.md`](results.md), made by `run.py results` from the measurements at idle, before the first change and after
the last one, already with the clean home: busy CPU goes from 11.0% to 5.9% (−5.1 points), swap in use drops by 128 MB
and 58 fewer packages are enabled. Available memory stays the same: the clean home and its add-ons use what is freed.
What uses most CPU now is the firmware's audio service, about 20% of one core with nothing playing, which cannot be
touched without root.

## Clean home (optional)

Fire OS does not let you change or disable the home app. The launcher (see [the launcher](../../README.md#the-launcher))
works around it with its accessibility service. The settings live in this profile's `launcher/config.json` and the
code is shared in `launcher/patches/`:

- **Home button.** The service sees Amazon's home appear and opens the clean one (`stock_home_redirect`). With
  `min_futurity=0` (`remap.conf`) it takes 0.4 s, hidden under a cover in the background colour, instead of the 5 s
  with ads that Fire OS would impose.
- **Back after a force stop.** A force stop takes an app off the accessibility list and nothing turns it back on.
  With `restore_key_services`, `run.py launcher` grants the launcher permission to write settings and read usage
  history, and enables GuardRevival. Android reconnects GuardRevival right after a force stop; it restores accessibility
  in about a second and, if Amazon's home is in front, jumps to the clean one.
- **Appstore tile → the store.** The Appstore's normal entry is the "Your apps & games" grid.
  `launch_actions` `com.amazon.venezia=activity:.ade.ADEHomeActivity` opens the store front.
- **No key filter** (`"key_filter": false`). On Fire OS the Home key never reaches the service, so filtering every key
  only added latency.

If accessibility ever shows empty (`adb shell settings get secure enabled_accessibility_services`), turn it off and on
again. Writing the value alone does not make Fire OS bind the service, as dumbtv also notes:

```bash
adb shell 'settings put secure accessibility_enabled 0; settings put secure enabled_accessibility_services "\"\""; sleep 1
  settings put secure enabled_accessibility_services com.gathin.tvhome/.HomeKeyService; settings put secure accessibility_enabled 1'
```

## Fire OS quirks worth knowing

- **Screensavers get force-stopped.** When a screensaver ends, Fire OS force-stops the package that provides it
  (`AmazonDreamControllerCallback.forceStopDream` in `fosservices`). Only Amazon's own screensaver and packages with
  "android" in their name are spared. A launcher that is also the screensaver dies on every wake, and Amazon's home
  (with ads) shows until it comes back. That is why this profile turns the system screensaver off.
- **The TV button (LIVE_TV, key code 297) reaches no app.** The system opens Amazon's Live TV directly
  (`com.amazon.tv.livetv/.GuideWrapperActivity`), which with no channels lands on "Add channels". To send it to an app
  of your choice, add `"redirect_apps": ["com.amazon.tv.livetv:<your.app.package>"]` to the launcher config. The
  launcher sees the Live TV window and opens your app with Home underneath, so Back returns Home. Side effect: Amazon's
  Live TV settings also go to that app.
- **The phone remote needs WhisperLink.** The Fire TV phone app talks to `com.amazon.whisperlink.core.android`. This
  profile leaves it allowed (`appops.conf`) so the phone works as a spare remote, at the cost of about 10 % of a core.
  Travelling without the remote? The stick only knows your home Wi-Fi. A phone hotspot with the same name and password
  gets it online by itself, and the phone app finds it.

## Updates re-enable what you disabled

Updating a system app turns it back on, and Amazon's updater (protected) does so now and then. Check every few weeks:

```bash
uv run run.py engine --profile fire-tv-4k-max-aftka --action all --dry-run
```

If the plan is not empty, run it again without `--dry-run`.

## Use

```bash
export TV_SERIAL=<tv-ip>:5555
uv run run.py measure --profile fire-tv-4k-max-aftka
uv run run.py engine --profile fire-tv-4k-max-aftka --action all --dry-run
uv run run.py engine --profile fire-tv-4k-max-aftka --action all
uv run run.py launcher --profile fire-tv-4k-max-aftka        # optional: the clean home
uv run run.py engine --profile fire-tv-4k-max-aftka --action rollback --all   # back to how it came
```

## Credits

The package lists, the accessibility approach to the Home button and the off/on trick come from
[dumbtv](https://github.com/humblemuzzu/dumbtv) (MIT; its device catalogue is CC BY-SA 4.0). See [CREDITS.md](CREDITS.md).
