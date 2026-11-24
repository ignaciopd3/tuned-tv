"""Los mensajes de tv-opt en inglés, por su texto en español (ver tvopt/core/i18n.py).

tests/test_i18n.py comprueba que estén todos los del código, que no sobre ninguno y que tengan los mismos huecos.
"""

from __future__ import annotations

EN: dict[str, str] = {
    # ---- ADB
    "Nombre de sección inválido: {name}": "Invalid section name: {name}",
    "Serial inválido: {serial}": "Invalid serial: {serial}",
    "La tele no respondió: {detail}": "The TV did not answer: {detail}",
    "La tele {serial} no respondió en {seconds:.0f} s": "The TV {serial} did not answer within {seconds:.0f} s",
    "No encuentro adb ({path})": "adb not found ({path})",
    "Acepta en la tele el aviso «¿Permitir la depuración USB?» (marca «Permitir siempre»)": (
        'Accept the "Allow USB debugging?" prompt on the TV (tick "Always allow")'
    ),
    "No se pudo conectar a {serial} (estado: {state})": "Could not connect to {serial} (state: {state})",
    "sin respuesta": "no answer",
    # ---- auditoría
    """# Auditoría · {profile} · run {run}

| Campo | Valor |
|---|---|
| Marca / modelo | {brand} / {model} |
| {match_prop} | {match_value} |
| Chip | {chip} (plataforma {platform}) |
| Producto / dispositivo | {product} / {device} |
| Android / SDK / parche | {android} |
| Build | {fingerprint} |
| ABI | {abi} |
| País (props) | {country} |
| Country code Wi-Fi (cmd wifi) | {cc} |

## Paquetes

| Instalados | Deshabilitados | Desinstalados (usuario 0) | Sistema | Terceros |
|---|---|---|---|---|
| {installed} | {disabled} | {uninstalled} | {system} | {third} |

Ficheros: `before/` (estado completo, solo lectura) · `audit/wifi.txt` · `audit/packages.paths` (APK de cada paquete)
""": """# Audit · {profile} · run {run}

| Field | Value |
|---|---|
| Brand / model | {brand} / {model} |
| {match_prop} | {match_value} |
| Chip | {chip} (platform {platform}) |
| Product / device | {product} / {device} |
| Android / SDK / patch | {android} |
| Build | {fingerprint} |
| ABI | {abi} |
| Country (props) | {country} |
| Wi-Fi country code (cmd wifi) | {cc} |

## Packages

| Installed | Disabled | Uninstalled (user 0) | System | Third-party |
|---|---|---|---|---|
| {installed} | {disabled} | {uninstalled} | {system} | {third} |

Files: `before/` (full state, read only) · `audit/wifi.txt` · `audit/packages.paths` (each package's APK)
""",
    "Auditoría: {path}": "Audit: {path}",
    "Diagnóstico Wi-Fi incompleto (audit/wifi.txt)": "Incomplete Wi-Fi diagnosis (audit/wifi.txt)",
    "No se pudieron leer las rutas de APK": "Could not read the APK paths",
    # ---- motor
    "Uso: run.py motor --profile <nombre> --action <audit|debloat|optimize|remap|all|rollback> [opciones]\n"
    "  --serial <ip:puerto>  TV destino (por defecto, variable TV_SERIAL)\n"
    "  --dry-run             calcula y guarda el plan sin tocar la TV\n"
    "  --include-caution     incluye packages.caution en debloat/all\n"
    "  --from <run>          rollback de un run concreto (nombre de su carpeta en backups/)\n"
    "  --all                 rollback de todos los runs pendientes, del más reciente al más antiguo\n"
    "Salida: 0 ok · 1 error · 2 uso/perfil inválido · 3 TV distinta al perfil · 4 verificación fallida": (
        "Usage: run.py engine --profile <name> --action <audit|debloat|optimize|remap|all|rollback> [options]\n"
        "  --serial <ip:port>    target TV (default: the TV_SERIAL variable)\n"
        "  --dry-run             works out and saves the plan without touching the TV\n"
        "  --include-caution     includes packages.caution in debloat/all\n"
        "  --from <run>          rolls back one run (its folder name in backups/)\n"
        "  --all                 rolls back every pending run, newest first\n"
        "Exit: 0 ok · 1 error · 2 usage/invalid profile · 3 TV differs from the profile · 4 check failed"
    ),
    "Run {run} · perfil {profile} · acción {action}{dry}": "Run {run} · profile {profile} · action {action}{dry}",
    "Hecho · {path}": "Done · {path}",
    "Conectado a {serial}": "Connected to {serial}",
    "TV verificada: {name}": "TV verified: {name}",
    "Rollback listo antes de tocar nada: {path}": "Rollback ready before touching anything: {path}",
    "Aplicando {count} cambios en un único lote…": "Applying {count} changes in a single batch…",
    "{count} cambios aplicados y verificados ({seconds:.1f} s)": (
        "{count} changes applied and verified ({seconds:.1f} s)"
    ),
    "Faltan --profile y --action": "--profile and --action are required",
    "Nombre de perfil inválido: {profile}": "Invalid profile name: {profile}",
    "Indica la TV con --serial <ip:puerto> o la variable TV_SERIAL": (
        "Name the TV with --serial <ip:port> or the TV_SERIAL variable"
    ),
    "No existe el perfil: {path}": "Profile not found: {path}",
    "Acción desconocida: {action}": "Unknown action: {action}",
    "Estado ORIGINAL de la TV guardado en {path}": "ORIGINAL state of the TV saved in {path}",
    "La TV no coincide con el perfil: {prop}='{got}' (esperado '{want}')": (
        "The TV does not match the profile: {prop}='{got}' (expected '{want}')"
    ),
    "{keyboard} es el teclado activo de esta TV: no se puede quitar": (
        "{keyboard} is this TV's active keyboard: it cannot be removed"
    ),
    "El lote se interrumpió; reconectando para comprobar el estado real": (
        "The batch was interrupted; reconnecting to check the real state"
    ),
    "{bad} cambios sin aplicar. Para deshacer: run.py motor --profile {profile} --action rollback": (
        "{bad} changes not applied. To undo: run.py engine --profile {profile} --action rollback"
    ),
    "Revirtiendo run {run}…": "Rolling back run {run}…",
    "Run {run} revertido y verificado": "Run {run} rolled back and verified",
    "Sin cambios: la TV ya cumple el perfil": "No changes: the TV already matches the profile",
    "Verificación: {key} = '{got}' (esperado '{want}')": "Check: {key} = '{got}' (expected '{want}')",
    "No hay rollback para el run '{run}' en {path}": "No rollback for run '{run}' in {path}",
    "No hay runs pendientes de revertir en {path}": "No runs left to roll back in {path}",
    "Rollback interrumpido; reconectando para comprobar el estado": (
        "Rollback interrupted; reconnecting to check the state"
    ),
    "Rollback de {run} incompleto ({bad} diferencias). Es idempotente: vuelve a lanzarlo": (
        "Rollback of {run} incomplete ({bad} differences). It is idempotent: run it again"
    ),
    "Falta el valor de {arg}": "Missing value for {arg}",
    "Dry-run: plan en {path}; la TV no se ha tocado": "Dry run: plan in {path}; the TV was not touched",
    "Opción desconocida: {arg}": "Unknown option: {arg}",
    # ---- launcher
    "El launcher vuelve solo tras un cierre forzado (GuardRevival, permisos de ajustes e historial de uso)": (
        "The launcher comes back by itself after a force stop (GuardRevival, settings and usage access)"
    ),
    "Esperando a que el inicio esté delante para no interrumpir lo que se está viendo…": (
        "Waiting for the home screen to be in front, so nothing being watched is interrupted…"
    ),
    "La tele ya tiene estos mismos APK: no se instala nada": "The TV already has these same APKs: nothing to install",
    "No se pudo dar al launcher los permisos de ajustes e historial de uso ni activar GuardRevival": (
        "Could not give the launcher settings and usage access, nor enable GuardRevival"
    ),
    " (¿firmado con otra clave?)": " (signed with another key?)",
    "Falló la instalación de {pkg}{hint}: {said}": "Installing {pkg} failed{hint}: {said}",
    "Instalado {pkg} con arranque automático permitido": "Installed {pkg} with auto start allowed",
    "Instalado {pkg}": "Installed {pkg}",
    "cleanyourtv en {commit} con {count} parches (rama tv-opt-{profile})": (
        "cleanyourtv at {commit} with {count} patches (branch tv-opt-{profile})"
    ),
    "Compilando {module}": "Building {module}",
    "Compilado y guardado en caché ({fingerprint})": "Built and cached ({fingerprint})",
    "No se pudo poner cleanyourtv en {commit}": "Could not check out cleanyourtv at {commit}",
    "Los parches no aplican sobre {commit}: {detail}": "The patches do not apply on {commit}: {detail}",
    "Falló la compilación de {module}": "Building {module} failed",
    "Falta launcher/patches/BASE ({path})": "launcher/patches/BASE is missing ({path})",
    "{path}: se espera «url commit»": '{path}: expected "url commit"',
    "No se pudo clonar {url}": "Could not clone {url}",
    "APK en caché ({fingerprint}): no hace falta compilar": "APKs cached ({fingerprint}): no build needed",
    "{where}: se espera «carpeta paquete»": '{where}: expected "folder package"',
    "Tema enviado: {sent} de {total} archivos (los demás ya estaban)": (
        "Theme sent: {sent} of {total} files (the rest were already there)"
    ),
    "Inicio reiniciado con el tema": "Home screen restarted with the theme",
    "No hay config.json en {path}": "No config.json in {path}",
    "{path} no es un objeto JSON de claves del tema: el launcher lo ignoraría": (
        "{path} is not a JSON object of theme keys: the launcher would ignore it"
    ),
    "El tema de la tele ya es este: no se envía nada": "The TV already has this theme: nothing sent",
    "La tele no aceptó {names}": "The TV did not accept {names}",
    "Falta el entorno de cleanyourtv ({path}): el tema sale al reiniciar el inicio": (
        "cleanyourtv's environment is missing ({path}): the theme shows when the home screen restarts"
    ),
    "El inicio no se reinició tras el tema: lo cogerá la próxima vez que arranque": (
        "The home screen did not restart after the theme: it picks it up the next time it starts"
    ),
    "{path} no es JSON válido": "{path} is not valid JSON",
    "No se pudo subir {name}": "Could not upload {name}",
    "Nombre de fondo no admitido: {name} (letras, cifras, «.», «_» y «-»)": (
        'Wallpaper name not allowed: {name} (letters, digits, ".", "_" and "-")'
    ),
    # ---- medir
    "nativo": "native",
    "sistema": "system",
    "persistente": "persistent",
    "servicio persistente": "persistent service",
    "en pantalla": "on screen",
    "visible": "visible",
    "perceptible": "perceptible",
    "servicio": "service",
    "anterior": "previous",
    "inicio": "home",
    "en caché": "cached",
    "# Rendimiento · {profile} · {taken}": "# Performance · {profile} · {taken}",
    "| Medida | Valor |": "| Measure | Value |",
    "| Memoria disponible | {available} de {total} ({pct} %) |": (
        "| Available memory | {available} of {total} ({pct}%) |"
    ),
    "| Memoria de intercambio en uso | {used} de {total} |": "| Swap in use | {used} of {total} |",
    "| CPU ocupada (1 s) | {pct} % de {cores} núcleos |": "| CPU busy (1 s) | {pct}% of {cores} cores |",
    "| Carga media (1, 5 y 15 min) | {a} · {b} · {c} |": "| Load average (1, 5 and 15 min) | {a} · {b} · {c} |",
    "| Procesos | {tasks} |": "| Processes | {tasks} |",
    "| Paquetes activos | {enabled} de {total} ({third} de terceros) |": (
        "| Enabled packages | {enabled} of {total} ({third} third-party) |"
    ),
    "| Almacenamiento usado | {pct} % |": "| Storage used | {pct}% |",
    "| Encendida desde hace | {hours} h |": "| Up for | {hours} h |",
    "## Lo que más CPU usa": "## Busiest CPU users",
    "| Proceso | CPU |": "| Process | CPU |",
    "## Lo que más memoria usa": "## Biggest memory users",
    "| Proceso | Estado | Memoria (PSS) |": "| Process | State | Memory (PSS) |",
    "| {name} | {pct} % |": "| {name} | {pct}% |",
    "Medido en {seconds} s, solo leyendo.": "Measured in {seconds} s, read only.",
    "Memoria disponible: {before} → {after} ({diff})": "Available memory: {before} → {after} ({diff})",
    "Intercambio en uso: {before} → {after} ({diff})": "Swap in use: {before} → {after} ({diff})",
    "CPU ocupada: {before} % → {after} %": "CPU busy: {before}% → {after}%",
    "Procesos: {before} → {after} ({diff})": "Processes: {before} → {after} ({diff})",
    "Paquetes activos: {before} → {after} ({diff})": "Enabled packages: {before} → {after} ({diff})",
    "Comparado con la medida anterior ({stamp}):": "Compared with the previous measurement ({stamp}):",
    "Guardado en {path}": "Saved in {path}",
    # ---- plan y foto
    "Plan: {count} cambios": "Plan: {count} changes",
    "{pkg} no está en esta TV; se omite": "{pkg} is not on this TV; skipped",
    "{pkg} no está en esta TV; se omite {op}": "{pkg} is not on this TV; {op} skipped",
    "(ahora: {state})": "(now: {state})",
    "(sin definir)": "(unset)",
    "propiedad": "property",
    "No se pudo crear un directorio de run en {path}": "Could not create a run folder in {path}",
    "Snapshot guardado: {path} ({seconds:.1f} s)": "Snapshot saved: {path} ({seconds:.1f} s)",
    "Snapshot incompleto en {path}: falta {missing}": "Incomplete snapshot in {path}: {missing} is missing",
    "No se pudo leer el estado de la TV (¿conexión caída?)": "Could not read the TV's state (connection lost?)",
    # ---- run.py
    "Indica la tele con --serial <ip:puerto> o la variable TV_SERIAL": (
        "Name the TV with --serial <ip:port> or the TV_SERIAL variable"
    ),
    "Launcher, complementos y tema del perfil {profile} al día": (
        "Launcher, add-ons and theme of profile {profile} up to date"
    ),
    "tv-opt: conectar, limpiar y optimizar teles": "tv-opt: connect, debloat and tune TVs",
    "orden": "command",
    "PERFIL": "PROFILE",
    "compara las medidas de antes y de después de los cambios y escribe results.md para compartir": (
        "compares the measurements before and after the changes and writes results.md to share"
    ),
    # ---- resultados
    "No hay cambios en vigor: aplica el perfil con el motor antes de sacar resultados": (
        "No changes in effect: apply the profile with the engine before getting results"
    ),
    "No hay medidas después del último cambio ({date}): mide con run.py medir, con la tele en reposo en el inicio": (
        "No measurements after the last change ({date}): measure with run.py measure, with the TV idle at home"
    ),
    "No hay ninguna medida de antes de los cambios: la próxima vez, mide antes de aplicar": (
        "There is no measurement from before the changes: next time, measure before applying"
    ),
    "Medida de antes de los cambios guardada: {path}": "Measurement from before the changes saved: {path}",
    "No se pudo tomar la medida de antes ({detail}); sigo sin ella": (
        "Could not take the measurement from before ({detail}); carrying on without it"
    ),
    "el motor: foto, auditoría, plan, aplicar y deshacer (motor --help)": (
        "the engine: snapshot, audit, plan, apply and undo (engine --help)"
    ),
    "mide el rendimiento de la tele sin tocar nada": "measures the TV's performance without touching anything",
    "perfil de la tele (carpeta de profiles/)": "the TV's profile (folder in profiles/)",
    "ip:puerto de la tele (por defecto, la variable TV_SERIAL)": "the TV's ip:port (default: the TV_SERIAL variable)",
    "compila (con caché) e instala el launcher, los complementos y el tema": (
        "builds (with a cache) and installs the launcher, the add-ons and the theme"
    ),
    "compila sin tocar la tele": "builds without touching the TV",
    "recompila y reinstala aunque no haya cambios": "rebuilds and reinstalls even without changes",
    "La tele no coincide con el perfil: {prop}='{got}' (esperado '{want}')": (
        "The TV does not match the profile: {prop}='{got}' (expected '{want}')"
    ),
    "Compilado (sin instalar)": "Built (not installed)",
    "Define TV_SERIAL (ip:puerto)": "Set TV_SERIAL (ip:port)",
    "No encuentro Git Bash: instala Git for Windows o indica su ruta en TVOPT_BASH": (
        "Git Bash not found: install Git for Windows or give its path in TVOPT_BASH"
    ),
    "No encuentro bash en el PATH": "bash not found in the PATH",
    # ---- perfiles
    "{where}: sobran campos: {extra}": "{where}: extra fields: {extra}",
    "{where}: nombre de paquete inválido: {pkg}": "{where}: invalid package name: {pkg}",
    "{where}: método inválido '{method}' (disable|uninstall)": "{where}: invalid method '{method}' (disable|uninstall)",
    "{where}: {pkg} está protegido (lib/protected.list)": "{where}: {pkg} is protected (lib/protected.list)",
    "{where}: {name} repetido": "{where}: {name} repeated",
    "{where}: se espera «namespace clave valor»": '{where}: expected "namespace key value"',
    "{where}: namespace inválido: {ns}": "{where}: invalid namespace: {ns}",
    "{where}: clave inválida: {key}": "{where}: invalid key: {key}",
    "{where}: valor con caracteres no permitidos: {value}": "{where}: value with characters not allowed: {value}",
    "{where}: se espera «paquete OPERACIÓN modo»": '{where}: expected "package OPERATION mode"',
    "{where}: operación inválida: {op}": "{where}: invalid operation: {op}",
    "{where}: modo inválido '{mode}' ({modes})": "{where}: invalid mode '{mode}' ({modes})",
    "{where}: se espera «propiedad valor»": '{where}: expected "property value"',
    "{where}: solo se admiten log.tag.<etiqueta> y persist.log.tag.<etiqueta>: {name}": (
        "{where}: only log.tag.<tag> and persist.log.tag.<tag> are allowed: {name}"
    ),
    "{where}: nivel inválido '{value}' (V, D, I, W, E, F o S)": (
        "{where}: invalid level '{value}' (V, D, I, W, E, F or S)"
    ),
    "Falta {path}": "{path} is missing",
    "{path}: MATCH_PROP inválido": "{path}: invalid MATCH_PROP",
    "{where}: se espera CLAVE=valor": "{where}: expected KEY=value",
    "{path}: falta {key}": "{path}: {key} is missing",
    # ---- datos privados
    "token de GitHub": "GitHub token",
    "clave de AWS": "AWS key",
    "clave privada": "private key",
    "Busca datos privados en los archivos del repo": "Looks for private data in the repo's files",
    "reglas propias, una expresión regular por línea": "your own rules, one regular expression per line",
    "Sin datos privados": "No private data",
    "{count} posibles datos privados": "{count} possible private data",
    "archivo que no se comparte": "file that is never shared",
    "correo": "e-mail",
    "IP privada": "private IP",
    # ---- tools/casa_probe.py
    "; olvidado: {roles}": "; forgotten: {roles}",
    "Enviado a Casa: {roles}{forgotten}; avisos encima de todo permitidos": (
        "Sent to Casa: {roles}{forgotten}; alerts over everything allowed"
    ),
    "QR listo: {path}": "QR ready: {path}",
    "No se escaneó el QR en 3 minutos.": "The QR code was not scanned within 3 minutes.",
    "Escuchando {seconds} s desde {time}": "Listening for {seconds} s from {time}",
    "Me niego a guardar datos de la cuenta dentro del repo: {path}": (
        "Refusing to save account data inside the repo: {path}"
    ),
    "Indica la tele con la variable TV_SERIAL (ip:puerto)": "Name the TV with the TV_SERIAL variable (ip:port)",
    "La tele no aceptó la orden: {detail}": "The TV did not accept the command: {detail}",
    "Tuya no dio el QR: {detail}": "Tuya did not give a QR code: {detail}",
    "No hay ningún aparato llamado «{name}»": 'No device called "{name}"',
    "Falta su clave local o su IP en casa: ejecuta devices y scan antes": (
        "Its local key or home IP is missing: run devices and scan first"
    ),
    "El aparato no respondió en local (¿versión de protocolo o clave?)": (
        "The device did not answer locally (protocol version or key?)"
    ),
    "Falta «{name}» con clave, IP y versión: ejecuta devices y scan antes": (
        '"{name}" with key, IP and version is missing: run devices and scan first'
    ),
    "Sesión guardada.": "Session saved.",
    "Sesión de la tele enviada a Casa.": "The TV's session was sent to Casa.",
    "encendido": "on",
    "apagado": "off",
    """Uso:
  casa_probe.py login <código>   código de usuario de Smart Life (Yo > Ajustes > Cuenta y seguridad); deja qr.png
                                 y espera hasta 3 min a que se escanee con la app
  casa_probe.py devices          lista los aparatos y los guarda en aparatos.json
  casa_probe.py scan             busca los aparatos en la red de casa: IP local y versión del protocolo LAN
  casa_probe.py listen [seg]     muestra lo que llega por MQTT (puerta, gas, enchufes) durante seg (120)
  casa_probe.py toggle <nombre>  enciende o apaga en local un enchufe, por su nombre en la app
  casa_probe.py push             pasa a la tele (complemento Casa, por ADB) los aparatos de roles.json y le da permiso
                                 para mostrar avisos encima de todo; entorno ADB y TV_SERIAL como run.py
  casa_probe.py tv-login <código> abre una sesión de la nube solo para la tele (QR nuevo) y se la pasa; el PC no la
                                 guarda

roles.json (en CASA_DIR, fuera del repo): papel en Casa → nombre en Smart Life, p. ej.
  {"luz": "Luz Salón", "calefactor": "Calefactor", "gas": "Gas sensor", "clima": "…", "puerta": "…"}
""": """Usage:
  casa_probe.py login <code>     Smart Life user code (Me > Settings > Account and Security); leaves qr.png
                                 and waits up to 3 min for the app to scan it
  casa_probe.py devices          lists the devices and saves them in aparatos.json
  casa_probe.py scan             finds the devices on the home network: local IP and LAN protocol version
  casa_probe.py listen [sec]     shows what arrives over MQTT (door, gas, plugs) for sec seconds (120)
  casa_probe.py toggle <name>    switches a plug on or off locally, by its name in the app
  casa_probe.py push             sends the devices in roles.json to the TV (Casa add-on, over ADB) and lets it
                                 show alerts over everything; ADB and TV_SERIAL environment as in run.py
  casa_probe.py tv-login <code>  opens a cloud session for the TV only (new QR code) and hands it over; the PC
                                 does not keep it

roles.json (in CASA_DIR, outside the repo): role in Casa → name in Smart Life, e.g.
  {"luz": "Living room light", "calefactor": "Heater", "gas": "Gas sensor", "clima": "…", "puerta": "…"}
""",
    # ---- tools/tcl_channels.py
    "No encuentro el cursor en el editor de canales": "Cannot find the cursor in the channel editor",
    "{channels} canales leídos · {swaps} intercambios pendientes": "{channels} channels read · {swaps} swaps pending",
    "«{name}» no está en la TV (o no quedan más copias) para el dial {dial}": (
        '"{name}" is not on the TV (or no copies are left) for dial {dial}'
    ),
    "Comprobación final: quedan {left}; replanifico": "Final check: {left} left; planning again",
    "ocultar {dial} {name}: {result}": "hide {dial} {name}: {result}",
    "{dial} {name} ya estaba oculto": "{dial} {name} was already hidden",
    "OK (comprobado)": "OK (checked)",
    "sin confirmar": "not confirmed",
    """Uso:  python tools/tcl_channels.py <mapa.txt> [--dry-run] [--check-every N]
  --check-every N: lee la pantalla solo cada N intercambios (10 por defecto); los demás van a ciegas
  con movimientos deterministas, y al final una lectura completa replanifica lo que falte.
  mapa.txt: un nombre por línea, en el orden deseado (los nombres repetidos se repiten); «!» delante
  oculta ese canal. Los canales que no aparezcan quedan detrás, en su orden actual. Las radios
  (diales ≥ 1000) no se tocan.
Entorno: ADB (ruta a adb), TV_SERIAL (ip:puerto).
""": """Usage:  python tools/tcl_channels.py <map.txt> [--dry-run] [--check-every N]
  --check-every N: reads the screen only every N swaps (10 by default); the rest go blind with
  deterministic moves, and a full read at the end plans whatever is left again.
  map.txt: one name per line, in the order you want (repeated names repeat); "!" in front hides that
  channel. Channels left out stay behind, in their current order. Radio stations (dials ≥ 1000) are
  not touched.
Environment: ADB (path to adb), TV_SERIAL (ip:port).
""",
}

# Los textos propios de argparse, en español (en inglés salen tal cual).
ARGPARSE_ES: dict[str, str] = {
    "usage: ": "uso: ",
    "positional arguments": "argumentos",
    "options": "opciones",
    "show this help message and exit": "muestra esta ayuda y sale",
    "show program's version number and exit": "muestra la versión y sale",
    "the following arguments are required: %s": "faltan estos argumentos: %s",
    "unrecognized arguments: %s": "argumentos desconocidos: %s",
    "invalid choice: %(value)r (choose from %(choices)s)": "opción no válida: %(value)r (elige entre %(choices)s)",
    "expected one argument": "falta su valor",
    "argument %(argument_name)s: %(message)s": "argumento %(argument_name)s: %(message)s",
}
