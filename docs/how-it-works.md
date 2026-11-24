# How Tuned TV works

[Español](how-it-works.es.md) · [Back to the README](../README.md)

```
profiles/<tv>/  ──►  engine (run.py motor)  ──►  the TV, over ADB
                       snapshot → audit → plan → apply in one batch → verify
                       └─► profiles/<tv>/backups/<run>/  (snapshots, plan, rollback.sh; never committed)
launcher/       ──►  run.py launcher: cleanyourtv + patches → build (cached) → install → theme
run.py medir    ──►  profiles/<tv>/backups/medidas/<time>.json and .md, compared with the previous one
```

## Profiles

One folder per TV model, under `profiles/`. Every list line carries its reason after `#`, and a missing file simply
means "nothing of that kind".

| File | What it holds | Format |
|---|---|---|
| `profile.env` | Name and the property that identifies the model; the engine refuses any TV that does not match | `PROFILE_NAME=…`, `MATCH_PROP=ro.…`, `MATCH_VALUE=…` |
| `packages.remove` | Packages to disable | `package [disable\|uninstall]   # reason` |
| `packages.caution` | Optional packages, only with `--include-caution`; `# KEEP package` documents what stays on purpose | same |
| `settings.conf` | Android settings | `system\|secure\|global  key  value   # reason` |
| `appops.conf` | App permissions, such as background work | `package OPERATION mode   # reason` (`allow`, `ignore`, `deny`, `default`, `foreground`) |
| `props.conf` | Log levels (`log.tag.*` and `persist.log.tag.*` only; nothing else is possible without root) | `property level   # reason` |
| `remap.conf` | Remote buttons, where the firmware reads them from settings | same as `settings.conf` |
| `launcher/config.json` | The clean home's theme and behaviour | cleanyourtv's theme keys plus Tuned TV's |
| `README.md` | What the profile does on that model, why, its quirks and measurements | Markdown (and `README.es.md`) |

`lib/protected.list` lists packages that no profile can touch: launchers, keyboards, Wi-Fi, HDMI, DRM, the TV app and
Prime Video on Fire OS. The engine also protects whichever keyboard is active on each TV.

## The engine

`uv run run.py motor --profile <tv> --action <action> [--dry-run] [--include-caution]`

1. **Connect and verify** that the TV is the profile's model (`MATCH_PROP` = `MATCH_VALUE`). If not, nothing happens
   (exit code 3).
2. **Snapshot:** packages (all, system, third-party, disabled), settings in the three namespaces, app permissions and
   log properties, read in one round trip.
3. **Audit and plan:** compare the profile with the snapshot. Only the differences go into the plan, so running a
   profile twice changes nothing the second time. Packages that do not exist on that TV are skipped with a warning.
4. **Apply** (without `--dry-run`): `rollback.sh` is written *before* anything changes, then the whole plan runs as
   one batch on the TV.
5. **Verify:** a second snapshot (`after/`) checks every change. Exit code 4 if something did not take.

Each run leaves a folder in `profiles/<tv>/backups/<date-time>/`: `before/`, `after/`, `plan.txt`, `apply.out`,
`rollback.sh` and `run.log`. Backups hold device data (the Android ID, for one), so git ignores them.

| Action | Does |
|---|---|
| `audit` | Read only: what the TV has and what the profile would change |
| `debloat` | `packages.remove` (and `packages.caution` with `--include-caution`) |
| `optimize` | `settings.conf`, `appops.conf` and `props.conf` |
| `remap` | `remap.conf` |
| `all` | All of the above |
| `rollback` | Undo the latest run, a given one (`--from <run>`) or all pending runs (`--all`), newest first |

## Measuring

`uv run run.py medir --perfil <tv>` changes nothing. It records, in a single batch:

- busy CPU over a sampling window, plus the busiest processes;
- available memory and swap;
- the processes using the most memory;
- the number of enabled packages.

The report is saved as JSON and Markdown and compared with the previous measurement. Measure with the TV idle at its
home screen: a playing video makes numbers incomparable.

## The launcher

`uv run run.py launcher --perfil <tv> [--solo-compilar] [--forzar]`

1. **Source:** cleanyourtv at the commit in `launcher/patches/BASE`, plus `launcher/patches/*.patch` in order, plus
   the add-ons listed in `launcher/patches/ADDONS`. They are checked out in the cleanyourtv clone on a
   `tv-opt-<profile>` branch.
2. **Build** with Gradle, with the launcher's unit tests. APKs are cached under `~/.tv-opt/cache`, keyed by a
   fingerprint of the patches, the add-ons and the signing key, so an unchanged launcher is never rebuilt.
3. **Install only what changed** (compared by hash with what the TV has), add-ons first and the launcher last. It
   waits until the TV's home screen is in front, because installing restarts the home screen and must not interrupt
   what is being watched.
4. **Theme:** `config.json`, the wallpapers and their captions are pushed through the launcher's content provider,
   only if they changed. The home screen then restarts and its key helpers are bound again.
5. **Fire OS extras:** Fire OS keeps Home to its own launcher, so the profile sets `stock_home_redirect`, and the
   launcher's accessibility service sends Amazon's home back to it. With `restore_key_services`, `run.py launcher`
   also grants the permissions that bring accessibility back after a force stop (GuardRevival).

Each patch is one commit, with a message that explains what and why; reading
[`launcher/patches/`](../launcher/patches/) in order tells the launcher's story.

## Tests

- **Unit tests** cover parsing, plans, measurements, the launcher pieces and the privacy scan, and need no TV.
- **Engine scenarios** (`tests/test_engine_scenarios.py`) run full actions against a simulated TV
  (`tests/fake_adb.sh`, `tests/fake_device.sh`): apply, rollback, protected packages and connection errors.
- **CI** runs ruff, ruff format, pyright, pytest and `python -m tvopt.core.privacy` on every push and pull request.
