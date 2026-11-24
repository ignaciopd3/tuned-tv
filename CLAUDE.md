# Tuned TV

Remove ads, bloat and tracking from smart TVs and streaming sticks over the network, measure the result, and undo it
whenever you want. Android TV and Google TV and Fire OS are supported and tested; LG webOS and Samsung Tizen have
guides and are on the way. Start with [README.md](README.md) and [docs/how-it-works.md](docs/how-it-works.md).

## Map

```
run.py                 single entry point: engine (motor), measure (medir), launcher
tvopt/core/            shared: profiles and manifests, logging, privacy scan
tvopt/adb/             ADB client (one connection per TV, batched commands)
tvopt/android_tv/      Android TV, Google TV and Fire OS: engine (snapshot, plan, apply, rollback, verify),
                       performance measurement, launcher build and theme
profiles/<tv>/         one folder per TV model: profile.env, packages.remove, packages.caution, settings.conf,
                       appops.conf, props.conf, remap.conf, launcher/config.json, README.md
profiles/_template/    start here for a new model
lib/protected.list     packages no profile may touch (the engine refuses them)
launcher/              patches on top of cleanyourtv (version in launcher/patches/BASE), shared add-ons and wallpapers
tests/                 pytest: unit tests and full scenarios against a simulated TV (tests/fake_*.sh)
docs/guides/           how to enable developer mode or debugging on each system
```

The code comments are in Spanish; documentation is in English and Spanish (`*.es.md`). Contributions are welcome in
either language. Reply to people in their own language.

Everything a person sees is translated. Python messages are written in Spanish inside `tr()` (`tvopt/core/i18n.py`)
with their English text in `tvopt/core/i18n_en.py`; the language is the system's, or `TVOPT_LANG` (`en`, `es`). On the
TV, texts live in each app's `values/strings.xml` (English) and `values-es/` (Spanish). `tests/test_i18n.py` fails
if a message has no translation or bypasses `tr()`.

## Rules

- **Never change a TV without a plan first.** Every change goes through
  `uv run run.py engine --profile <tv> --action <...> --dry-run`, is shown, and is applied only when the person agrees.
  The engine takes a snapshot first and every run can be undone with `--action rollback`.
- **Disable, never uninstall** system packages. The exception is a persistent package that restarts while disabled;
  then `uninstall` (`pm uninstall -k --user 0`, reversible with `install-existing`), with the reason in the line.
- **Respect `lib/protected.list`**: launchers, keyboards, Wi-Fi, HDMI, DRM, the TV app, updaters the person relies on.
  Adding to it is fine; removing needs a strong reason in the PR.
- **Measure before and after** (`uv run run.py measure --profile <tv>`) with the TV idle at Home; a playing video makes
  the numbers meaningless.
- **Install the launcher only with the TV's home screen in front** (`run.py launcher` waits for it), never over an
  HDMI input or an app.
- **No private data in the repo**: no IP addresses, e-mails, serials, account names, keys, tokens or `backups/`.
  `uv run python -m tvopt.core.privacy` must stay clean; CI runs it on every pull request.
- **Every line in a manifest says why** (`package   # reason`).

## Checks (all must pass before a commit)

```bash
uv run ruff check
uv run ruff format --check
uv run pyright
uv run pytest
uv run python -m tvopt.core.privacy
```

No change reaches a real TV before it passes the engine scenarios (`tests/test_engine_scenarios.py`).

## Adding a TV model

Follow [CONTRIBUTING.md](CONTRIBUTING.md): find the exact model (`getprop`), copy `profiles/_template` to
`profiles/<brand>-<model>-<chip>/`, fill `profile.env`, build the lists from the system guide and the references, dry
run, apply, measure, write `results.md` with `run.py results --profile <tv>`, and write the model's README.md.
