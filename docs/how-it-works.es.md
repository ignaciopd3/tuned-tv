# Cómo funciona Tuned TV

[English](how-it-works.md) · [Volver al README](../README.es.md)

```
profiles/<tele>/  ──►  motor (run.py motor)  ──►  la tele, por ADB
                         foto → auditoría → plan → aplicar en un lote → comprobar
                         └─► profiles/<tele>/backups/<run>/  (fotos, plan, rollback.sh; nunca van a git)
launcher/         ──►  run.py launcher: cleanyourtv + parches → compilar (con caché) → instalar → tema
run.py medir      ──►  profiles/<tele>/backups/medidas/<hora>.json y .md, comparado con la anterior
```

## Perfiles

Una carpeta por modelo de tele, en `profiles/`. Cada línea de las listas lleva su motivo detrás de `#`, y si falta un
archivo es que no hay nada de ese tipo.

| Archivo | Qué lleva | Formato |
|---|---|---|
| `profile.env` | Nombre y la propiedad que identifica el modelo; el motor rechaza cualquier tele que no coincida | `PROFILE_NAME=…`, `MATCH_PROP=ro.…`, `MATCH_VALUE=…` |
| `packages.remove` | Paquetes que se deshabilitan | `paquete [disable\|uninstall]   # motivo` |
| `packages.caution` | Paquetes opcionales, solo con `--include-caution`; `# KEEP paquete` documenta lo que se queda a propósito | igual |
| `settings.conf` | Ajustes de Android | `system\|secure\|global  clave  valor   # motivo` |
| `appops.conf` | Permisos de apps, como el trabajo en segundo plano | `paquete OPERACIÓN modo   # motivo` (`allow`, `ignore`, `deny`, `default`, `foreground`) |
| `props.conf` | Niveles de registro (solo `log.tag.*` y `persist.log.tag.*`; sin root no se puede más) | `propiedad nivel   # motivo` |
| `remap.conf` | Botones del mando, donde el firmware los lee de los ajustes | igual que `settings.conf` |
| `launcher/config.json` | Tema y comportamiento del inicio limpio | claves de tema de cleanyourtv más las de Tuned TV |
| `README.md` | Qué hace el perfil en ese modelo, por qué, sus rarezas y sus medidas | Markdown (y `README.es.md`) |

`lib/protected.list` es la lista de paquetes que ningún perfil puede tocar: inicios, teclados, wifi, HDMI, DRM, la app
de la tele y Prime Video en Fire OS. El motor protege además el teclado activo de cada tele.

## El motor

`uv run run.py motor --profile <tele> --action <acción> [--dry-run] [--include-caution]`

1. **Conecta y comprueba** que la tele es el modelo del perfil (`MATCH_PROP` = `MATCH_VALUE`). Si no, no hace nada
   (salida 3).
2. **Foto:** paquetes (todos, de sistema, de terceros y deshabilitados), los ajustes de los tres espacios, los permisos
   de apps y las propiedades de registro, en una sola ida y vuelta.
3. **Auditoría y plan:** compara el perfil con la foto. Al plan solo van las diferencias, así que lanzar un perfil dos
   veces no cambia nada la segunda. Los paquetes que no existen en esa tele se saltan con un aviso.
4. **Aplicar** (sin `--dry-run`): `rollback.sh` se escribe *antes* de cambiar nada, y después el plan entero va en un
   solo lote a la tele.
5. **Comprobar:** una segunda foto (`after/`) verifica cada cambio. Salida 4 si algo no se aplicó.

Cada ejecución deja una carpeta en `profiles/<tele>/backups/<fecha-hora>/`: `before/`, `after/`, `plan.txt`,
`apply.out`, `rollback.sh` y `run.log`. Las copias llevan datos del aparato (el identificador de Android, por ejemplo),
así que git las ignora.

| Acción | Hace |
|---|---|
| `audit` | Solo lectura: qué tiene la tele y qué cambiaría el perfil |
| `debloat` | `packages.remove` (y `packages.caution` con `--include-caution`) |
| `optimize` | `settings.conf`, `appops.conf` y `props.conf` |
| `remap` | `remap.conf` |
| `all` | Todo lo anterior |
| `rollback` | Deshace la última ejecución, una concreta (`--from <run>`) o todas las pendientes (`--all`), de la más reciente a la más antigua |

## Medir

`uv run run.py medir --perfil <tele>` no cambia nada. Anota, en un solo lote:

- la CPU ocupada durante un rato, y los procesos que más gastan;
- la memoria disponible y el intercambio;
- los procesos que más memoria usan;
- el número de paquetes activos.

El informe se guarda en JSON y en Markdown y se compara con la medida anterior. Mide con la tele quieta en su inicio:
con un vídeo puesto las cifras no se pueden comparar.

## El launcher

`uv run run.py launcher --perfil <tele> [--solo-compilar] [--forzar]`

1. **Código:** cleanyourtv en el commit de `launcher/patches/BASE`, más `launcher/patches/*.patch` en orden, más los
   complementos de `launcher/patches/ADDONS`. Se preparan en el clon de cleanyourtv, en una rama
   `tv-opt-<perfil>`.
2. **Compilar** con Gradle, con las pruebas unitarias del launcher. Los APK se guardan en `~/.tv-opt/cache` con una
   huella de los parches, los complementos y la clave de firma, así que un launcher sin cambios no se vuelve a
   compilar.
3. **Instalar solo lo que cambia** (comparando la huella con lo que tiene la tele), primero los complementos y al final
   el launcher. Espera a que el inicio de la tele esté delante, porque instalar reinicia el inicio y no debe cortar lo
   que se está viendo.
4. **Tema:** `config.json`, los fondos y sus créditos se envían por el proveedor de contenido del launcher, solo si
   cambiaron. Después se reinicia el inicio y se vuelven a conectar sus ayudantes del mando.
5. **Extras de Fire OS:** Fire OS reserva el inicio a su launcher, así que el perfil pone `stock_home_redirect` y el
   servicio de accesibilidad del launcher devuelve a su sitio el inicio de Amazon. Con `restore_key_services`,
   `run.py launcher` da además los permisos que reponen la accesibilidad tras un cierre forzado (GuardRevival).

Cada parche es un commit con un mensaje que explica qué hace y por qué; leer
[`launcher/patches/`](../launcher/patches/) en orden cuenta la historia del launcher.

## Pruebas

- **Pruebas unitarias:** cubren la lectura de archivos, los planes, las medidas, las piezas del launcher y el detector
  de datos privados, y no necesitan tele.
- **Escenarios del motor** (`tests/test_engine_scenarios.py`): acciones completas contra una tele simulada
  (`tests/fake_adb.sh`, `tests/fake_device.sh`), con aplicar, deshacer, paquetes protegidos y errores de conexión.
- **CI:** ruff, ruff format, pyright, pytest y `python -m tvopt.core.privacy` en cada push y cada pull request.
