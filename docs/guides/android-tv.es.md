# Android TV y Google TV

[English](android-tv.md) · [Volver al README](../../README.es.md)

**Sirve para** teles y aparatos con Android TV o Google TV: TCL, Sony Bravia, Xiaomi (Mi TV y Mi Box), Philips
(modelos Android), Hisense (modelos Android, no VIDAA), Sharp, Toshiba, Nokia, Chromecast con Google TV, Google TV
Streamer, NVIDIA Shield, onn y muchas más. Android 8 o posterior.

**Estado:** ✅ funciona y está probado (TCL C845 con Google TV 11).

## 1. Activa las opciones para desarrolladores

Los nombres de los menús cambian según la marca y la versión. Lo que buscas es el **número de compilación** en la
pantalla «Información»: pulsar OK siete veces sobre él desbloquea las opciones para desarrolladores.

| Tu tele tiene | Ruta |
|---|---|
| **Google TV** (casi todas las teles desde 2021, Chromecast con Google TV, Google TV Streamer) | Ajustes → Sistema → Información → **Compilación del SO de Android TV** → OK 7 veces. Las opciones para desarrolladores salen en Ajustes → Sistema. |
| **Android TV** (menús clásicos: Sony, Philips, Xiaomi, Shield…) | Ajustes → Preferencias del dispositivo → Información → **Compilación** → OK 7 veces. Las opciones salen en Preferencias del dispositivo. |

Si pide el PIN, escríbelo. Un mensaje como «Ya eres desarrollador» lo confirma.

## 2. Activa la depuración

En **Opciones para desarrolladores**:

- Activa **Depuración por USB**. En casi todas las teles abre también el ADB por red en el puerto 5555, que es el que
  usa Tuned TV.
- Si ves **Depuración por red** o **Depuración ADB** (NVIDIA Shield, algunas Sony y Philips), actívala también.
- **Depuración inalámbrica con código de vinculación** (Chromecast con Google TV, Google TV Streamer y aparatos en los
  que el 5555 sigue cerrado): entra en *Depuración inalámbrica → Vincular dispositivo con código*. En el ordenador:
  ```bash
  adb pair <ip-de-la-tele>:<puerto-de-vinculación>   # escribe el código que sale en la tele
  adb connect <ip-de-la-tele>:<puerto>               # el puerto de la pantalla de depuración inalámbrica
  adb tcpip 5555                                     # opcional: abre el 5555 hasta el siguiente reinicio
  ```

## 3. Busca la IP y conéctate

- La IP está en Ajustes → Red e Internet → tu red, o en Información → Estado.
- Conéctate y acepta **«¿Permitir depuración USB?»** en la tele. Marca «Permitir siempre desde este ordenador» para que
  no pregunte cada vez.
  ```bash
  adb connect <ip-de-la-tele>:5555
  adb devices                          # debe salir <ip-de-la-tele>:5555   device
  export TV_SERIAL=<ip-de-la-tele>:5555
  ```
- Dale a la tele una IP fija en el router (reserva DHCP), y así `TV_SERIAL` no cambia nunca.

## 4. Identifica el modelo exacto

Un perfil reconoce la tele por una propiedad del sistema, para no aplicarse nunca en otro modelo:

```bash
adb shell getprop ro.product.manufacturer
adb shell getprop ro.product.model
adb shell getprop ro.board.platform        # el chip
adb shell getprop ro.build.version.release # versión de Android
adb shell getprop | grep -i -E "client_type|product.name|device"
```

Algunas marcas ponen un nombre vago en `ro.product.model` (la TCL C845 solo dice «Smart TV Pro»). Entonces elige una
propiedad más precisa, como `persist.tcl.client_type` en TCL.

## Qué hace Tuned TV en Android TV

- **El motor** (`run.py motor`): deshabilita paquetes, aplica ajustes, permisos de apps (`appops`) y niveles de
  registro, y cambia botones donde el firmware lo deja. Saca una foto antes y deja deshacer cada ejecución.
- **Medir** (`run.py medir`): CPU, memoria, intercambio y los procesos que más gastan, en reposo.
- **El launcher** (`run.py launcher`): sustituye el inicio, también el de Google TV, y sus sugerencias. Añade reloj,
  tiempo y acciones para los botones del mando, e instala complementos.

**¿Tu modelo no está?** [cleanyourtv](https://github.com/Gathin23/cleanyourtv) tiene listas probadas para unos 400
modelos (busca en [cleanyour.tv/tvs](https://cleanyour.tv/tvs)). Son el mejor punto de partida para un perfil nuevo:
ver [CONTRIBUTING.es.md](../../CONTRIBUTING.es.md).

## Problemas típicos

| Síntoma | Qué hacer |
|---|---|
| `connection refused` en el puerto 5555 | La depuración está apagada, la tele se reinició (la depuración inalámbrica vuelve a cerrar el 5555) o cambió la IP. |
| `unauthorized` | Acepta el aviso en la tele. Si no sale, apaga y enciende la depuración USB, revoca las autorizaciones en las opciones para desarrolladores y vuelve a conectar. |
| Play Protect bloquea un APK (Android 14) | «Más detalles» → «Instalar de todos modos». |
| Un complemento no arranca en TCL | TCL bloquea el arranque en segundo plano de las apps instaladas; `run.py launcher` lo permite (`APP_AUTO_START allow`). |
| Una actualización del firmware devolvió paquetes | Vuelve a lanzar el perfil con `--dry-run` y aplícalo. |

## Apaga la depuración al terminar

Opciones para desarrolladores → apaga **Depuración por USB**, **Depuración por red** y **Depuración inalámbrica**, las
que tenga tu tele, y revoca las autorizaciones. El ADB por red va sin cifrar, y en algunos firmwares cualquiera de tu
red tiene una terminal en la tele. Todo lo que cambiaste sigue funcionando.

## Créditos

Pasos y listas de modelos de [cleanyourtv](https://github.com/Gathin23/cleanyourtv) (MIT) y
[free-my-tv](https://github.com/simbasjungles/free-my-tv) (MIT).
