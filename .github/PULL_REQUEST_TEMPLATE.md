## What and why / Qué y por qué

<!-- One idea per pull request. Link the issue if there is one. · Una idea por pull request. Enlaza la issue si la hay. -->

## For a TV profile / Para un perfil de tele

- [ ] Model and system / Modelo y sistema:
- [ ] Dry-run plan reviewed (paste or attach it) / Plan de la simulación revisado (pégalo o adjúntalo)
- [ ] Applied and tested Wi-Fi, HDMI, tuner, sound, remote, apps, casting and a reboot / Aplicado y probado wifi, HDMI, TDT, sonido, mando, apps, envío desde el móvil y un reinicio
- [ ] Measured before and after, idle at Home (`run.py measure`) / Medido antes y después, quieta en el inicio
- [ ] `README.md` for the model (and `README.es.md` if possible) / del modelo
- [ ] Every list line has its reason / Cada línea de las listas lleva su motivo

## Always / Siempre

- [ ] `uv run ruff check`, `uv run ruff format --check`, `uv run pyright` and `uv run pytest` pass / pasan
- [ ] `uv run python -m tvopt.core.privacy` is clean: no IP addresses, e-mails, serials, accounts or `backups/` / está limpio
- [ ] Docs updated in both languages, or the missing translation is noted / Docs actualizadas en los dos idiomas, o se avisa de la traducción pendiente
