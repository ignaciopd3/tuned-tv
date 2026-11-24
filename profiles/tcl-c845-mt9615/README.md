# TCL C845 (1st revision) · G05 · MediaTek MT9615 · EU

[Español](README.es.md)

| | |
|---|---|
| Identifier (`MATCH_PROP`) | `persist.tcl.client_type = TCL-EU-MT9615-S1` |
| Product / board | `G05_4K_GB` / `G05` (`ro.product.model` only says "Smart TV Pro") |
| Chip | MT9615 (`ro.board.platform = mt5889`) |
| System | Google TV, Android 11 (SDK 30), build `AR2101/AR23` |
| ABI | `armeabi-v7a` (32-bit: any APK you install needs an ARMv7 build) |
| Connection | ADB over Wi-Fi, port 5555 ([Android TV guide](../../docs/guides/android-tv.md)) |
| Tested | November 2026 |

The **C845X2** (2nd revision) is a different board (`G08`, `tcl9618`, Android 14) with other packages: this profile
does not fit it.

## What this profile does

**Disables about 35 packages** (`packages.remove`, plus `packages.caution` with `--include-caution`). Everything is
disabled and reversible, except `com.tcl.guard` (see below). The list comes from cleanyourtv's G05 examples
(65C735, 55C728, 65C935, 65C745, 55C735), cross-checked on this TV. It only includes packages disabled without
trouble on several G05 sets and unrelated to picture, sound, remote, HDMI, DRM and updates.

- **Telemetry:** TCL's log uploader, TGuard (tracking, "health info" and app cleaner), Google feedback and partner
  attribution.
- **Ads and promos:** TCL content recommendations, push messages, TCL account nags, the "TCL Home" panel, TCL Live
  (FAST channels with ads), store demo stickers and the partner app auto-installer.
- **Unused preinstalls:** TCL browser and WebView (the system uses Google's), USB media player and gallery, e-manual,
  notes, Alexa, Play Games, Play Movies, TalkBack, calendar sync and print spooler.
- **Google's Ambient screensaver** (about 110 MB), replaced by the launcher's clock.
- **Optional, and worth reading first:**
  - **Google Assistant:** it is also the system's voice recognition, so you lose voice search and dictation. It used
    about 120 MB and 5–20 % of a core.
  - **AirPlay:** about 110 MB and 6 % CPU; Chromecast stays.
  - **Gboard:** this TV uses TCL's keyboard.
- **`packages.caution`:**
  - `com.tcl.ttvs`, TCL's analytics and Samba TV ACR, which also holds the firmware updater (no OTA until re-enabled);
  - the remote and soundbar updater;
  - the TCL key panel (`partnercustomizer`);
  - the first-boot wizard (`setupwraith`, needed before replacing the home app);
  - Miracast, T-Cast, Rakuten TV and YouTube Music.
  - Lines marked `# KEEP` stay on: Chromecast, game mode, hearing adaptation and Bluetooth "listen alone".

**Why `com.tcl.guard` is uninstalled for the user (`pm uninstall -k --user 0`) instead of disabled:** it is a
persistent system app, and the ActivityManager starts it at boot even when disabled. It comes back with
`cmd package install-existing com.tcl.guard`.

**Settings** (`settings.conf`):

| Setting | Before | After |
|---|---|---|
| `window_animation_scale` / `transition_animation_scale` / `animator_duration_scale` | 1.0 | 0.25 |
| `wifi_scan_always_enabled` | 1 | 0 |
| `private_dns_mode` / `private_dns_specifier` | unset | `hostname` / `p2.freedns.controld.com` (DNS-over-TLS with ad and tracker blocking) |

**A quieter system log** (`props.conf`): TCL's TV service (`sita.*`) and the MediaTek chip (`MI3`) wrote about 1,300
log lines per second. At `W`, only warnings and errors remain: 35 lines per second (−97 %). Two tags that repeat
"handle is null" with no HDMI input open go to `E` and `F`. The settings survive a reboot.

**Background work** (`appops.conf`): one app's background job every 30 minutes used 2.5 % of a core while closed. It is
kept in memory, so it still opens in 0.13 s.

## Results

Measured at idle with `run.py medir`, from the first measurement to the last:

| | Before | After |
|---|---|---|
| Busy CPU at idle | ~12–13 % | 4.5 % |
| Available memory | 1,271 MB | 1,345 MB |
| Swap in use | 288 MB | 269 MB |
| Enabled packages | 118 | 114 |

A load average of about 55 is not a problem. It comes from 55 MediaTek driver threads (HDMI, tuner, video) that wait
without using CPU.

## Remote buttons

- **TCL's own buttons (40xx) never reach accessibility services.** Neither Button Mapper nor the launcher's
  `HomeKeyService` sees them; only the screen in front does. With the clean home (and Google's `launcherx` disabled),
  they work **from Home** through the launcher's `app_keys`:

  | Button (code) | From Home |
  |---|---|
  | Netflix (4062) / YouTube (4065) / Prime Video (4099) | that app |
  | TCL Home (4137) | HDMI 1 |
  | Web (4159) | HDMI 2 |
  | TCL (4020) | free: add `"4020:<app.package>"` to `app_keys` |

- **No native remap on this firmware.** `TclPhoneWindowManager.handleCustomKey` only reads
  `settings global CustomKey_<code>` for a fixed list of app buttons (4096, 4100, 4101, 4142, 4144 and 4163). The IR
  remote of this model has none of them. 4020 goes straight to `startTKey`; `CustomKey_4020`, `CustomKey_4137` and
  `CustomKey_4159` are ignored. `remap.conf` keeps a tested template for the buttons that are on the list.
- An app launched from a button needs the **explicit component** when its activity declares no `CATEGORY_DEFAULT`.

## Clean home

The launcher replaces Google TV's home (`launcherx`) entirely. Google's suggestions disappear ("For you", trending,
best sellers) and the launcher's memory is freed. The settings are in this profile's `launcher/config.json`:

- **DTT first:** the first dock tile is the antenna (`app_labels` "TDT"). **Home → OK** opens live TV even when the
  last source was an HDMI input. It uses `launch_actions` `view:content://android.media.tv/channel?input=<tuner>`;
  opening the app plainly returns to the last source.
- **Volume stepping two at a time, fixed** (`consume_volume_keys`). This firmware applies the volume key before the
  accessibility key filter and again when the service returns it. Letting the service keep the volume keys fixes it.
- **Weather and the ADB warning** in the header, a full-screen clock after 3 minutes idle, wallpapers from Wikimedia
  Commons, and add-ons in the top-bar grid. See `launcher/CREDITS.md`.
- **Inputs** (`dumpsys tv_input`): HDMI 1 `HW1413744128`, HDMI 2 `HW1413744384`, HDMI 3 `HW1413744640`, HDMI 4
  `HW1413745664`, AV `HW1413743104`.

**Back to Google's home:**

```bash
adb shell pm enable com.google.android.apps.tv.launcherx
adb shell cmd package set-home-activity --user 0 com.google.android.apps.tv.launcherx/.home.HomeActivity
```

Then run `--action rollback` for the run that disabled `setupwraith`.

## Good to know

- **Cold boot** takes about 38 s, straight into the clean home, and everything stays (packages, settings, channels,
  key service, CEC, private DNS). Turning off with the remote is a fast standby, not a reboot.
- **Drift:** while `com.tcl.ttvs` is active, the firmware re-enables `usercenter`, `smartalexa` and `notereminder` at
  every boot. Run `--action debloat` again; it is idempotent.
- **Firmware updates:** look for one in Settings → System → About → System update before disabling `com.tcl.ttvs`.
- **Wi-Fi:** this TV uses the Spanish/European domain. In 5 GHz, prefer a fixed channel among 36, 40, 44 and 48 at
  80 MHz. DFS channels (52–144) force the router to jump channels when it detects radar, and the TV drops the network.
- **Channel order:** `tools/tcl_channels.py` sorts DTT channels from a `channels.txt` in the profile, one name per
  line (`!` hides one). Lists depend on the region, so this profile ships none.

## Use

```bash
export TV_SERIAL=<tv-ip>:5555
uv run run.py medir --perfil tcl-c845-mt9615
uv run run.py motor --profile tcl-c845-mt9615 --action all --dry-run
uv run run.py motor --profile tcl-c845-mt9615 --action all
uv run run.py launcher --perfil tcl-c845-mt9615        # optional: the clean home
uv run run.py motor --profile tcl-c845-mt9615 --action rollback --all   # back to how it came
```

## Credits

The package list starts from [cleanyourtv](https://github.com/Gathin23/cleanyourtv)'s G05 examples (MIT), as does the
launcher. See the root [CREDITS.md](../../CREDITS.md).
