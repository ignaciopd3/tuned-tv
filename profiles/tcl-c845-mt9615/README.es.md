# TCL C845 (1.ª revisión) · G05 · MediaTek MT9615 · EU

[English](README.md)

| | |
|---|---|
| Identificador (`MATCH_PROP`) | `persist.tcl.client_type = TCL-EU-MT9615-S1` |
| Producto / placa | `G05_4K_GB` / `G05` (`ro.product.model` solo dice «Smart TV Pro») |
| Chip | MT9615 (`ro.board.platform = mt5889`) |
| Sistema | Google TV, Android 11 (SDK 30), build `AR2101/AR23` |
| ABI | `armeabi-v7a` (32 bits: cualquier APK que instales debe tener build ARMv7) |
| Conexión | ADB por wifi, puerto 5555 ([guía de Android TV](../../docs/guides/android-tv.es.md)) |
| Probado | Noviembre de 2026 |

La **C845X2** (2.ª revisión) es otra placa (`G08`, `tcl9618`, Android 14) con otros paquetes: este perfil no le sirve.

## Qué hace este perfil

**Deshabilita unos 35 paquetes** (`packages.remove`, más `packages.caution` con `--include-caution`). Todo se
deshabilita y se puede deshacer, salvo `com.tcl.guard` (ver abajo). La lista sale de los ejemplos G05 de cleanyourtv
(65C735, 55C728, 65C935, 65C745, 55C735), cruzados con esta tele. Solo entra lo que se deshabilitó sin problemas en
varias G05 y no toca imagen, sonido, mando, HDMI, DRM ni actualizaciones.

- **Telemetría:** el subidor de registros de TCL, TGuard (rastreo, «health info» y limpiador de apps), «Enviar
  comentarios» de Google y la atribución de partners.
- **Anuncios y promos:** las recomendaciones de TCL, los mensajes push, los avisos de la cuenta TCL, el panel «TCL
  Home», TCL Live (canales FAST con anuncios), las pegatinas del modo tienda y el instalador automático de apps de
  partners.
- **Preinstalados sin uso:** navegador y WebView de TCL (el sistema usa el de Google), reproductor y galería USB,
  manual electrónico, notas, Alexa, Play Juegos, Play Películas, TalkBack, sincronización del calendario y la cola de
  impresión.
- **El salvapantallas Ambient de Google** (unos 110 MB), sustituido por el reloj del launcher.
- **Opcionales, mejor leerlos antes:**
  - **Asistente de Google:** es también el reconocimiento de voz del sistema, así que se pierden la búsqueda por voz y
    el dictado. Gastaba unos 120 MB y entre un 5 y un 20 % de un núcleo.
  - **AirPlay:** unos 110 MB y un 6 % de CPU; Chromecast se queda.
  - **Gboard:** esta tele usa el teclado de TCL.
- **`packages.caution`:**
  - `com.tcl.ttvs`, la analítica de TCL y el ACR de Samba TV, que lleva dentro también el actualizador del firmware
    (sin OTA hasta reactivarlo);
  - el actualizador del mando y la barra de sonido;
  - el panel del botón TCL (`partnercustomizer`);
  - el asistente del primer arranque (`setupwraith`, necesario antes de cambiar el inicio);
  - Miracast, T-Cast, Rakuten TV y YouTube Music.
  - Las líneas con `# KEEP` se quedan: Chromecast, modo juego, adaptación auditiva y «escuchar solo» por Bluetooth.

**Por qué `com.tcl.guard` se desinstala para el usuario (`pm uninstall -k --user 0`) en vez de deshabilitarse:** es una
app de sistema persistente, y el ActivityManager la arranca al encender aunque esté deshabilitada. Vuelve con
`cmd package install-existing com.tcl.guard`.

**Ajustes** (`settings.conf`):

| Ajuste | Antes | Después |
|---|---|---|
| `window_animation_scale` / `transition_animation_scale` / `animator_duration_scale` | 1.0 | 0.25 |
| `wifi_scan_always_enabled` | 1 | 0 |
| `private_dns_mode` / `private_dns_specifier` | sin definir | `hostname` / `p2.freedns.controld.com` (DNS sobre TLS con bloqueo de anuncios y rastreadores) |

**Registro del sistema más callado** (`props.conf`): el servicio de TV de TCL (`sita.*`) y el chip MediaTek (`MI3`)
escribían unas 1.300 líneas por segundo. A `W` solo quedan avisos y errores: 35 líneas por segundo (−97 %). Dos
etiquetas que repiten «handle is null» sin ninguna entrada HDMI abierta van a `E` y `F`. Los ajustes siguen tras un
reinicio.

**Trabajo en segundo plano** (`appops.conf`): la tarea cada 30 minutos de una app gastaba un 2,5 % de un núcleo con la
app cerrada. Se queda en memoria, así que sigue abriendo en 0,13 s.

## Resultados

Medido en reposo con `run.py medir`, de la primera medida a la última:

| | Antes | Después |
|---|---|---|
| CPU ocupada en reposo | ~12–13 % | 4,5 % |
| Memoria disponible | 1.271 MB | 1.345 MB |
| Intercambio en uso | 288 MB | 269 MB |
| Paquetes activos | 118 | 114 |

Una carga media de unos 55 no es un problema. Sale de 55 hilos de drivers de MediaTek (HDMI, sintonizador, vídeo) que
esperan sin usar CPU.

## Botones del mando

- **Los botones propios de TCL (40xx) nunca llegan a los servicios de accesibilidad.** No los ve Button Mapper ni el
  `HomeKeyService` del launcher; solo la pantalla que está delante. Con el inicio limpio (y `launcherx` de Google
  deshabilitado) funcionan **desde el inicio** con los `app_keys` del launcher:

  | Botón (código) | Desde el inicio |
  |---|---|
  | Netflix (4062) / YouTube (4065) / Prime Video (4099) | su app |
  | TCL Home (4137) | HDMI 1 |
  | Web (4159) | HDMI 2 |
  | TCL (4020) | libre: añade `"4020:<paquete.de.la.app>"` a `app_keys` |

- **No se puede remapear de forma nativa en este firmware.** `TclPhoneWindowManager.handleCustomKey` solo lee
  `settings global CustomKey_<código>` para una lista fija de botones de apps (4096, 4100, 4101, 4142, 4144 y 4163). El
  mando IR de este modelo no tiene ninguno. La 4020 va directa a `startTKey`; `CustomKey_4020`, `CustomKey_4137` y
  `CustomKey_4159` se ignoran. `remap.conf` guarda una plantilla probada para los botones que sí están en la lista.
- Una app lanzada desde un botón necesita el **componente explícito** cuando su actividad no declara
  `CATEGORY_DEFAULT`.

## Inicio limpio

El launcher sustituye por completo al inicio de Google TV (`launcherx`). Desaparecen las sugerencias de Google («Para
ti», tendencias, más vendidas) y se libera la memoria del launcher. Los ajustes van en el `launcher/config.json` del
perfil:

- **Primero la TDT:** la primera ficha del dock es la antena (`app_labels` «TDT»). **Inicio → OK** abre la tele aunque
  la última fuente fuera un HDMI. Usa `launch_actions` `view:content://android.media.tv/channel?input=<sintonizador>`;
  abrir la app sin más vuelve a la última fuente.
- **Volumen de dos en dos, resuelto** (`consume_volume_keys`). Este firmware aplica la tecla de volumen antes del
  filtro de teclas de accesibilidad y otra vez cuando el servicio la devuelve. Que el servicio se quede las teclas de
  volumen lo arregla.
- **El tiempo y el aviso de ADB** en la cabecera, un reloj a pantalla completa tras 3 minutos quieto, fondos de
  Wikimedia Commons y los complementos en la cuadrícula de arriba. Ver `launcher/CREDITS.md`.
- **Entradas** (`dumpsys tv_input`): HDMI 1 `HW1413744128`, HDMI 2 `HW1413744384`, HDMI 3 `HW1413744640`, HDMI 4
  `HW1413745664`, AV `HW1413743104`.

**Volver al inicio de Google:**

```bash
adb shell pm enable com.google.android.apps.tv.launcherx
adb shell cmd package set-home-activity --user 0 com.google.android.apps.tv.launcherx/.home.HomeActivity
```

Después, `--action rollback` del run que deshabilitó `setupwraith`.

## Conviene saber

- **El arranque en frío** tarda unos 38 s, directo al inicio limpio, y se mantiene todo (paquetes, ajustes, canales,
  servicio de teclas, CEC, DNS privado). Apagar con el mando es un reposo rápido, no un reinicio.
- **Deriva:** mientras `com.tcl.ttvs` siga activo, el firmware vuelve a activar `usercenter`, `smartalexa` y
  `notereminder` en cada arranque. Vuelve a lanzar `--action debloat`; no repite lo ya hecho.
- **Actualizaciones del firmware:** búscala en Ajustes → Sistema → Información → Actualización del sistema antes de
  deshabilitar `com.tcl.ttvs`.
- **Wifi:** esta tele usa el dominio de España y Europa. En 5 GHz, mejor un canal fijo entre 36, 40, 44 y 48 a 80 MHz.
  En los canales DFS (52–144) el router cambia de canal cuando detecta un radar, y la tele pierde la red.
- **Orden de los canales:** `tools/tcl_channels.py` ordena la TDT a partir de un `channels.txt`, un nombre por línea
  (`!` oculta uno). Las listas dependen de la región, así que este perfil no trae ninguna. Esta tele admite los canales
  UHD (DVB-T2 con HEVC). Ver la [guía de canales](../../docs/guides/channels.es.md).

## Uso

```bash
export TV_SERIAL=<ip-de-la-tele>:5555
uv run run.py medir --perfil tcl-c845-mt9615
uv run run.py motor --profile tcl-c845-mt9615 --action all --dry-run
uv run run.py motor --profile tcl-c845-mt9615 --action all
uv run run.py launcher --perfil tcl-c845-mt9615        # opcional: el inicio limpio
uv run run.py motor --profile tcl-c845-mt9615 --action rollback --all   # vuelve a como venía
```

## Créditos

La lista de paquetes parte de los ejemplos G05 de [cleanyourtv](https://github.com/Gathin23/cleanyourtv) (MIT), igual
que el launcher. Ver el [CREDITS.md](../../CREDITS.md) de la raíz.
