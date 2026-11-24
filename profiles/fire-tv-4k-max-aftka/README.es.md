# Fire TV Stick 4K Max (1.ª generación, 2021) · AFTKA

[English](README.md)

| | |
|---|---|
| Modelo | AFTKA «kara» (`ro.product.model`) |
| Sistema | Fire OS 7.7.1.3 (PS7713/5443), basado en Android 9 (SDK 28) |
| Chip | MediaTek MT8696, 4 núcleos, 32 bits (`armeabi-v7a`) |
| Memoria | 1,7 GB |
| Teclado | `com.amazon.tv.ime` (el motor protege siempre el teclado activo) |
| Conexión | ADB por wifi, puerto 5555 ([guía de Fire TV](../../docs/guides/fire-tv.es.md)) |
| Probado | Noviembre de 2026, en un stick; la lista de paquetes viene de dumbtv, probada en tres sticks con este firmware |

## Qué hace este perfil

**Deshabilita 58 paquetes** (`packages.remove`). No se desinstala nada: este firmware no tiene `install-existing`, así
que todo se deshabilita y vuelve con `--action rollback`.

- **Anuncios e identificador publicitario**, telemetría y métricas.
- **ACR**: el servicio que reconoce lo que ves, también lo que entra por HDMI.
- **Promos**, los banners de la tienda en la tele y los avisos.
- **Actualizaciones forzadas de Fire OS**: el stick ya no se actualiza solo. Las actualizaciones de Amazon traen
  anuncios nuevos, pero también dejas de recibir arreglos; ver
  [Actualizaciones](#las-actualizaciones-reactivan-lo-deshabilitado).
- **Alexa**: el botón del micro del mando deja de hacer nada.
- **Apps de Amazon** de música, fotos, juegos, Luna, Silk, Kids, ayuda, impresión y miniTV.
- **El salvapantallas de Amazon** y el inicio de sesión con proveedor de TV.

**Se mantienen a propósito:** Prime Video (`com.amazon.firebat`, en `lib/protected.list`), la Appstore
(`com.amazon.venezia`), el inicio de Amazon (lleva dentro los Ajustes del Fire TV), las notificaciones, el WebView y
todo lo de `lib/protected.list`.

**Paquetes que Amazon protege:** no se pueden deshabilitar sin root (métricas, informes de fallos, gestión remota,
enlaces de anuncios, soporte remoto y el actualizador OTA). `appops.conf` les quita el trabajo en segundo plano
(`RUN_IN_BACKGROUND ignore`).

**Ajustes** (`settings.conf`):

- Seguimiento publicitario limitado, sin anuncios personalizados ni subida de datos de uso.
- Sin avisos emergentes ni vídeo destacado que se reproduce solo.
- Animaciones a 0,25.
- DNS privado con bloqueo de anuncios y rastreadores (`p2.freedns.controld.com`).
- **Sin salvapantallas del sistema.** En Fire OS, al salir de un salvapantallas se cierra a la fuerza el paquete que lo
  da; ver [rarezas](#rarezas-de-fire-os-que-conviene-saber). En su lugar, el launcher pone su reloj tras 3 minutos
  quieto en el inicio, y la pantalla sigue apagándose a los 20 minutos (`screen_off_timeout` = `sleep_timeout`).

## Resultados

Medido en reposo con `run.py medir`:

| | Antes | Después |
|---|---|---|
| Memoria disponible | 915 MB | 965 MB |
| Intercambio en uso | 154 MB | 137 MB |
| Paquetes activos | 249 | 191 |

Con el inicio limpio (abajo), en reposo: unos 836 MB disponibles, 40 MB de intercambio y un 3,6 % de CPU total. Lo que
queda es el servicio de audio del firmware, que gasta un 20 % de un núcleo sin sonar nada y no se puede tocar sin root.

## Inicio limpio (opcional)

Fire OS no deja cambiar ni desactivar el inicio. El launcher (ver [el launcher](../../README.es.md#el-launcher)) lo
sortea con su servicio de accesibilidad. Los ajustes van en el `launcher/config.json` del perfil y el código, compartido,
en `launcher/patches/`:

- **Botón de inicio.** El servicio ve aparecer el inicio de Amazon y abre el limpio (`stock_home_redirect`). Con
  `min_futurity=0` (`remap.conf`) tarda 0,4 s, tapado por una capa del color del fondo, en vez de los 5 s con publicidad
  que impondría Fire OS.
- **Vuelve tras un cierre forzado.** Un cierre forzado saca a una app de la lista de accesibilidad y nada la vuelve a
  poner. Con `restore_key_services`, `run.py launcher` da al launcher permiso para escribir ajustes y leer el historial
  de uso, y activa GuardRevival. Android vuelve a conectar GuardRevival nada más cerrarse; este repone la accesibilidad
  en un segundo y, si el inicio de Amazon está delante, salta al limpio.
- **Icono de Appstore → la tienda.** La entrada normal de la Appstore es la cuadrícula «Mis apps y juegos».
  `launch_actions` `com.amazon.venezia=activity:.ade.ADEHomeActivity` abre la tienda.
- **Sin filtro de teclas** (`"key_filter": false`). En Fire OS la tecla de inicio nunca llega al servicio, así que
  filtrar todas las teclas solo añadía retraso.

Si la accesibilidad sale vacía alguna vez (`adb shell settings get secure enabled_accessibility_services`), hay que
apagarla y encenderla. Escribir solo el valor no hace que Fire OS conecte el servicio, lo dice también dumbtv:

```bash
adb shell 'settings put secure accessibility_enabled 0; settings put secure enabled_accessibility_services "\"\""; sleep 1
  settings put secure enabled_accessibility_services com.gathin.tvhome/.HomeKeyService; settings put secure accessibility_enabled 1'
```

## Rarezas de Fire OS que conviene saber

- **Los salvapantallas se cierran a la fuerza.** Al terminar un salvapantallas, Fire OS cierra a la fuerza el paquete
  que lo da (`AmazonDreamControllerCallback.forceStopDream` en `fosservices`). Solo se libran el de Amazon y los
  paquetes con «android» en el nombre. Un launcher que también es el salvapantallas muere en cada despertar, y se ve el
  inicio de Amazon (con anuncios) hasta que vuelve. Por eso este perfil quita el salvapantallas del sistema.
- **El botón de la tele (LIVE_TV, código 297) no llega a ninguna app.** El sistema abre directamente la TV en directo
  de Amazon (`com.amazon.tv.livetv/.GuideWrapperActivity`), que sin canales cae en «Añadir canales». Para mandarlo a la
  app que quieras, añade `"redirect_apps": ["com.amazon.tv.livetv:<paquete.de.tu.app>"]` a la configuración del
  launcher. El launcher ve la ventana de la TV en directo y abre tu app con el inicio debajo, así que Atrás vuelve al
  inicio. Efecto secundario: los ajustes de TV en directo de Amazon también llevan a esa app.
- **El mando del móvil necesita WhisperLink.** La app Fire TV del móvil habla con `com.amazon.whisperlink.core.android`.
  Este perfil lo deja permitido (`appops.conf`) para que el móvil sirva de mando de recambio, a cambio de un 10 % de un
  núcleo. ¿De viaje sin el mando? El stick solo conoce la wifi de casa. Con un punto de acceso en el móvil con el mismo
  nombre y contraseña se conecta solo, y la app del móvil lo encuentra.

## Las actualizaciones reactivan lo deshabilitado

Actualizar una app del sistema la vuelve a activar, y el actualizador de Amazon (protegido) lo hace de vez en cuando.
Compruébalo cada pocas semanas:

```bash
uv run run.py motor --profile fire-tv-4k-max-aftka --action all --dry-run
```

Si el plan no sale vacío, vuelve a lanzarlo sin `--dry-run`.

## Uso

```bash
export TV_SERIAL=<ip-de-la-tele>:5555
uv run run.py medir --perfil fire-tv-4k-max-aftka
uv run run.py motor --profile fire-tv-4k-max-aftka --action all --dry-run
uv run run.py motor --profile fire-tv-4k-max-aftka --action all
uv run run.py launcher --perfil fire-tv-4k-max-aftka        # opcional: el inicio limpio
uv run run.py motor --profile fire-tv-4k-max-aftka --action rollback --all   # vuelve a como venía
```

## Créditos

Las listas de paquetes, la forma de tomar el botón de inicio por accesibilidad y el truco de apagar y encender vienen de
[dumbtv](https://github.com/humblemuzzu/dumbtv) (MIT; su catálogo de dispositivos es CC BY-SA 4.0). Ver
[CREDITS.md](CREDITS.md).
