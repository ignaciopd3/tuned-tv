# Fire TV (Fire OS)

[English](fire-tv.md) · [Volver al README](../../README.es.md)

**Sirve para** los Fire TV Stick de Amazon (todas las generaciones, 4K y 4K Max incluidos), el Fire TV Cube y las
teles Fire TV Edition. dumbtv ha probado de Fire OS 6.2 a 8.1.

**Estado:** ✅ funciona y está probado (Fire TV Stick 4K Max, Fire OS 7.7).

## 1. Activa la depuración ADB

1. Configuración → **Mi Fire TV** → **Acerca de** → pulsa OK 7 veces sobre el **nombre del dispositivo**, hasta que
   diga que ya eres desarrollador.
2. Vuelve a Mi Fire TV → **Opciones para desarrolladores** → **Depuración ADB** → Activada.
3. La IP está en Configuración → Mi Fire TV → Acerca de → **Red**. En las teles Fire TV Edition, en Configuración → Red
   → la red conectada.

## 2. Conéctate

```bash
adb connect <ip-de-la-tele>:5555
export TV_SERIAL=<ip-de-la-tele>:5555
```

Acepta en la tele el aviso **¿Permitir depuración USB?** (marca «Permitir siempre desde este ordenador»). Para saber el
modelo: `adb shell getprop ro.product.model` (por ejemplo, `AFTKA` es el Fire TV Stick 4K Max de 1.ª generación).

## Qué hace Tuned TV en Fire OS

- **Deshabilita los anuncios, la telemetría, el ACR, las promos y las actualizaciones forzadas de Amazon**, más las apps
  de Amazon que no uses. Fire OS no tiene `install-existing`, así que no se desinstala nada y `--action rollback` lo
  devuelve todo.
- **Paquetes que Amazon protege:** no se pueden deshabilitar sin root (métricas, informes de fallos, gestión remota,
  enlaces de anuncios, soporte remoto y el actualizador OTA). Tuned TV les quita el trabajo en segundo plano
  (`appops RUN_IN_BACKGROUND ignore`).
- **Ajustes de privacidad:** seguimiento publicitario limitado, sin anuncios por intereses, sin informes de uso, sin
  vídeo que se reproduce solo en el inicio y, si quieres, un DNS privado que bloquea anuncios y rastreadores.
- **Un inicio limpio**, opcional. Fire OS no deja elegir otro inicio, así que el servicio de accesibilidad del launcher
  vigila el inicio de Amazon y lo sustituye en unos 0,4 s, tapado por una capa. También vuelve solo tras un cierre
  forzado. Los detalles y las rarezas del modelo están en el
  [perfil del Fire TV Stick 4K Max](../../profiles/fire-tv-4k-max-aftka/README.es.md).

## Límites de Fire OS que conviene saber

- **Las actualizaciones reactivan lo deshabilitado.** Actualizar una app del sistema la vuelve a activar, y el
  actualizador de Amazon lo hace cada pocas semanas. Compruébalo con `--dry-run` y vuelve a aplicar si el plan no sale
  vacío.
- **Al salir de un salvapantallas se cierra a la fuerza el paquete que lo da.** No uses el launcher como salvapantallas
  del sistema en Fire OS. El perfil quita el salvapantallas del sistema y deja que el launcher ponga su propio reloj.
- **El botón de la tele del mando (LIVE_TV, código 297) no llega a ninguna app.** Fire OS abre su propia pantalla de
  TV en directo. `redirect_apps` del launcher puede mandar esa pantalla a la app que quieras.
- **Los anuncios de YouTube no se pueden bloquear por DNS**: vienen de los mismos servidores que los vídeos. Lo normal
  es usar otro cliente de YouTube.
- **Fire OS no se puede sustituir.** Amazon bloquea el arranque, así que los cambios viven encima de Fire OS y un
  restablecimiento de fábrica los quita.
- **La app Fire TV del móvil como mando** necesita `com.amazon.whisperlink.core.android` con trabajo en segundo plano
  permitido. Déjalo así si viajas sin el mando.

## Alternativas y extras

[dumbtv](https://github.com/humblemuzzu/dumbtv) es un conjunto completo para Fire OS con su propio launcher. Su **filtro
DNS** opcional (personalDNSfilter, unos 400 servidores de telemetría, anuncios y actualizaciones de Amazon) también para
las actualizaciones de Fire OS mientras funciona. Ocupa la única VPN que admite Android, así que no puede ir junto a
otra app de VPN. Su `contribute.sh` escribe un informe para los modelos sin probar.

## Apaga el ADB al terminar

Opciones para desarrolladores → Depuración ADB → Desactivada. El launcher y los cambios siguen funcionando.

## Créditos

Las listas de paquetes, los ajustes de privacidad, la lista de paquetes protegidos y la forma de tomar el botón de
inicio por accesibilidad vienen de [dumbtv](https://github.com/humblemuzzu/dumbtv) (código MIT, catálogo de
dispositivos CC BY-SA 4.0).
