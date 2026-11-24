# Contributing to Tuned TV

[Español](CONTRIBUTING.es.md)

Thanks for helping! The most valuable contribution is a **profile for a TV model** that is not here yet: the next
person with that TV starts from something tested instead of from zero. Bug reports, guides, translations and code are
just as welcome.

Be kind and patient; we follow the [Code of Conduct](CODE_OF_CONDUCT.md). Issues and pull requests can be in English
or Spanish.

## Adding a TV model

### 1. Check it is not there already

Look in [`profiles/`](profiles/) and the [issues](https://github.com/ignaciopd3/tuned-tv/issues). If someone is already
on it, join them. If not, open a **New TV model** issue: it gathers the details in one place and tells others you
are working on it.

### 2. Connect and identify the model

Follow the [guide for your system](README.md#supported-systems), then:

```bash
adb shell getprop ro.product.manufacturer
adb shell getprop ro.product.model
adb shell getprop ro.board.platform          # chip
adb shell getprop ro.build.version.release   # Android version
adb shell getprop | grep -i -E "product|board|hardware|client_type|fingerprint"
```

Pick **one property whose value only this model and firmware family has**. `ro.product.model` is often too generic,
so look at `ro.product.name`, a brand property (`persist.tcl.client_type` on TCL) or, as a last resort,
`ro.build.fingerprint`.

### 3. Create the profile folder

```bash
cp -r profiles/_template profiles/<brand>-<model>-<chip>     # lowercase, e.g. tcl-c845-mt9615
```

Fill in `profile.env`:

```
PROFILE_NAME="Brand Model · chip · region"
MATCH_PROP=<the property from step 2>
MATCH_VALUE=<its value>
ABI=<adb shell getprop ro.product.cpu.abilist, first value>
```

The engine refuses to touch any TV while `MATCH_VALUE` is `CAMBIAR`.

### 4. Build the lists

- **Start from tested lists:** [cleanyourtv's examples](https://cleanyour.tv/tvs) for Android TV and Google TV (about
  400 models), and [dumbtv's catalogue](https://github.com/humblemuzzu/dumbtv) for Fire OS. Cite them in the profile's
  README; dumbtv's catalogue is CC BY-SA 4.0, so lists derived from it stay under that licence.
- **See what your TV has:** `adb shell pm list packages -s` (system) and `adb shell pm list packages -3` (installed).
- **One package per line, with its reason:** `com.vendor.ads   # vendor ad service, recommendations on Home`.
- **Anything with a cost** goes to `packages.caution`, not `packages.remove`: updaters, casting, voice, picture and
  sound features, preinstalled apps someone might use. Lines kept on purpose stay as `# KEEP package   # why`.
- **Never** list launchers, keyboards, Wi-Fi, HDMI, DRM, the TV/tuner app or anything in `lib/protected.list`; the
  engine refuses them anyway.
- `settings.conf`, `appops.conf`, `props.conf` and `remap.conf` are optional. The [Fire TV](profiles/fire-tv-4k-max-aftka/)
  and [TCL](profiles/tcl-c845-mt9615/) profiles show each one in use.

### 5. Dry run, apply, test

```bash
export TV_SERIAL=<tv-ip>:5555
uv run run.py engine --profile <your-profile> --action audit
uv run run.py measure --profile <your-profile>                      # before, idle at Home (the engine also takes one)
uv run run.py engine --profile <your-profile> --action all --dry-run
uv run run.py engine --profile <your-profile> --action all
```

Then check, one by one, everything people use:

- Wi-Fi and Ethernet;
- every HDMI input;
- the TV tuner;
- sound, including any soundbar or eARC;
- the remote, including the app buttons;
- the apps;
- casting;
- the TV after a reboot.

Measure again (`run.py measure`), idle at Home; once or twice more over a while makes the figures steadier. If
something broke, `--action rollback` and move that package to `packages.caution` with a note.

Then write the results to share:

```bash
uv run run.py results --profile <your-profile>                      # writes profiles/<your-profile>/results.md
```

It compares the measurements from before the first change with those after the last one (the median of each group)
and keeps only figures: memory, swap, CPU at idle, processes and enabled packages. The engine measures by itself before
the first real change, in case you forget.

### 6. Write the model's README

`profiles/<your-profile>/README.md` in English, and `README.es.md` too if you can. Follow the existing ones:

- a table with the model, system, chip, how to connect and when you tested it;
- what is disabled and why, by group, and what it costs (voice, casting…);
- a link to `results.md`, with its headline figures;
- the model's quirks;
- how to use it and undo it.

### 7. Keep it private, check it, send it

- **No private data:** write `<tv-ip>` instead of addresses, and include no e-mails, serials, account or Wi-Fi
  names. `backups/` folders are git-ignored; never force-add them.
- Run the checks below. Then open a pull request: the template has the checklist.

## Contributing code

```bash
uv sync
uv run ruff check
uv run ruff format --check
uv run pyright
uv run pytest
uv run python -m tvopt.core.privacy
```

- **Python 3.12**, typed. `pyright` runs in strict mode on `tvopt/`.
- **Test without a TV:** the engine scenarios run against a simulated TV (`tests/fake_adb.sh`, `tests/fake_device.sh`).
  Add a scenario when you change engine behaviour.
- **Keep changes small and focused**, one idea per pull request.
- **Commit messages:** an imperative subject (`Add profile for Sony KD-55X85J`, `Engine: skip packages missing on the
  TV`), and a body that explains why.
- **Code comments are in Spanish** for historical reasons; English is fine in new code. Docs are bilingual: update both
  languages when you can, or say in the PR that a translation is pending.
- **Launcher changes** are patches on top of cleanyourtv: commit them in a cleanyourtv clone and export with
  `git format-patch` into `launcher/patches/`, keeping the numbering. Send fixes that are not specific to Tuned TV
  upstream to cleanyourtv too.

## Translations

Everything on the TV follows the TV's language. English is the default and Spanish is complete; any other language
falls back to English until someone translates it.

- **The launcher's Tuned TV texts** live in its `strings.xml` (`values/` in English, `values-es/` in Spanish), added
  by the patches in `launcher/patches/`.
- **The Casa add-on** has its texts in `addons/casa/app/src/main/res/values*/strings.xml`.
- **To add a language**, create `values-<code>/strings.xml` (for example `values-fr/`) with the same names, commit it
  in a cleanyourtv clone and export the patch. Casa's tests check that every language has every text with the same
  placeholders.
- Translations cost nothing at run time: Android picks the TV's language once, when the app starts.
- **The tool on the computer** writes its messages in Spanish inside `tr()` and keeps the English in
  `tvopt/core/i18n_en.py`. A new message needs its English line; `tests/test_i18n.py` fails otherwise, and also if a
  message is printed without `tr()`. It speaks the system's language, or the one in `TVOPT_LANG` (`en`, `es`).

## Reviews

A maintainer reviews every pull request. CI must pass (style, types, tests and the privacy scan). For profiles, a
dry-run plan and before/after measurements in the PR make reviews quick.

## Licence

By contributing you agree that your contribution is released under the [MIT licence](LICENSE). Material derived
from CC BY-SA sources keeps that licence; mark it in the profile and in [CREDITS.md](CREDITS.md).
