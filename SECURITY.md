# Security / Seguridad

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Report them privately through
[GitHub's private vulnerability reporting](https://github.com/ignaciopd3/tuned-tv/security/advisories/new). Include
what you found, how to reproduce it and what it could affect. You will get an answer as soon as possible, and credit
in the fix if you want it.

**En español:** no abras una issue pública para problemas de seguridad; avisa en privado con el enlace de arriba.

## In scope

- The tool (`run.py`, `tvopt/`, `tools/`): anything that could change a TV beyond the plan shown, leak data from the
  computer or the TV, or run commands nobody asked for.
- The launcher patches and add-ons built from this repo.
- Profiles that disable something that breaks the TV in a way `--action rollback` cannot undo.

## Out of scope

- Vulnerabilities in TV firmware itself. Report those to the manufacturer.
- The upstream projects (cleanyourtv, dumbtv, free-my-tv). Report to them; we will pick up their fixes.

## Using Tuned TV safely

- **Turn debugging off when you are done.** Network ADB is unencrypted, and on some firmware any device on your
  network gets a shell on the TV.
- **Read the plan** (`--dry-run`) before applying, and read the model's README for what each change costs.
- **Keep your signing key safe** if you build the launcher: whoever has it can sign updates that your TV accepts.
- **Never share your `backups/` folders.** They contain device identifiers.
- Changes are reversible (`--action rollback`) and a factory reset always restores the TV, but warranty terms depend on
  your brand and country.
