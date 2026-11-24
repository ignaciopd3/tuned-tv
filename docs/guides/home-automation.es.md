# Domótica: tu casa en la tele

[English](home-automation.md) · [Volver al README](../../README.es.md)

El complemento **Casa** conecta la tele con aparatos de **Smart Life / Tuya**. Te avisa en pantalla, encima de lo que
estés viendo, y te deja encender la luz o el calefactor desde el inicio o con un botón del mando. Se instala con el
launcher (`run.py launcher`) en Android TV, Google TV y Fire TV.

| | Qué hace | Cómo llega |
|---|---|---|
| 🚪 **Puerta** | Avisa al abrirse, te lo recuerda cada 5 minutos mientras siga abierta y avisa al cerrarse con el tiempo que estuvo abierta. | Nube de Tuya, al momento |
| 🔥 **Gas** | Oscurece la pantalla, pone una alarma roja grande y pita cada 3 segundos hasta que pulses OK. | Red de casa, al momento |
| 💡 **Luz** · ♨️ **Calefactor** | Botones en el inicio, junto a la barra de arriba, y si quieres en un botón del mando. | Red de casa, sin internet |
| 🌡️ **Temperatura y humedad** | Las de casa, en el inicio y en el reloj de reposo, al lado del tiempo de fuera. | Nube de Tuya |

Los avisos salen encima de cualquier canal, app o entrada HDMI, con la tele encendida.

## Qué necesitas

**Aparatos inteligentes en casa.** La tele no detecta nada por sí sola: cada función necesita su aparato, dado de alta
en la app **Smart Life** (o Tuya Smart). Busca «Smart Life» o «Tuya» en la caja. Pon solo los que quieras; lo que no
tengas se queda fuera.

| Para | Necesitas |
|---|---|
| 💡 Luz | Un **enchufe inteligente wifi**, con la lámpara enchufada y encendida en su interruptor. |
| ♨️ Calefactor | Otro **enchufe inteligente wifi** que aguante su potencia (mira los vatios del calefactor; muchos enchufes aguantan 16 A, unos 3.600 W), con el calefactor encendido en su propio interruptor. |
| 🚪 Puerta | Un **sensor de puerta o ventana** (de contacto) wifi. |
| 🔥 Gas | Un **detector de gas wifi**, enchufado a la corriente. |
| 🌡️ Temperatura y humedad | Un **sensor de temperatura y humedad** wifi. |

Probado con aparatos wifi, sin pasarela Zigbee. El aviso de gas en la tele es un aviso más: **no sustituye** a un
detector homologado con su propia alarma.

Además:

- El launcher de Tuned TV instalado ([el launcher](../../README.es.md#el-launcher)).
- En el ordenador, un entorno de Python aparte con las librerías de Tuya. Va fuera del repo, porque guarda tu sesión:
  ```bash
  python -m venv ~/Documents/casa-tuya/venv
  ~/Documents/casa-tuya/venv/bin/pip install tuya-device-sharing-sdk tinytuya qrcode   # Windows: venv\Scripts\pip
  ```
  `CASA_DIR` cambia la carpeta; por defecto es `~/Documents/casa-tuya`. En los pasos de abajo, `casa` significa
  `~/Documents/casa-tuya/venv/bin/python tools/casa_probe.py`.

## Configurarlo

1. **Entra con tu cuenta de Smart Life.** En la app, *Yo → Ajustes → Cuenta y seguridad → Código de usuario*. Después:
   ```bash
   casa login <código>        # deja qr.png en la carpeta de Casa: escanéalo con la app Smart Life
   casa devices               # lista tus aparatos
   casa scan                  # los busca en la red de casa (IP local y versión del protocolo)
   ```
2. **Di qué aparato es cada cosa** en `roles.json`, dentro de la carpeta de Casa, con el nombre que tienen en la app.
   Quita las líneas de lo que no tengas:
   ```json
   {"luz": "Luz salón", "calefactor": "Calefactor", "puerta": "Puerta", "gas": "Sensor de gas", "clima": "Termómetro"}
   ```
3. **Pásaselo a la tele**, con la depuración activada y `TV_SERIAL` puesto:
   ```bash
   casa push                  # manda los aparatos a Casa y le deja mostrar avisos encima de todo
   casa tv-login <código>     # QR nuevo: una sesión de la nube solo para la tele (puerta y clima); el PC no la guarda
   ```
4. **Enséñalo en el inicio.** En el `launcher/config.json` de tu perfil:
   ```json
   "casa_row": "io.github.ignaciopd3.casa",
   "app_keys": ["KEYCODE_PROG_YELLOW:io.github.ignaciopd3.casa/.LuzActivity"]
   ```
   `app_keys` es opcional: aquí el botón amarillo enciende y apaga la luz. Para el calefactor, `.CalefactorActivity`.
   Después, `uv run run.py launcher --perfil <perfil>`.
5. **Prueba los avisos** sin abrir la puerta de verdad:
   ```bash
   adb shell am start -n io.github.ignaciopd3.casa/.ImportActivity --es simulate puerta   # o sigue, cerrada
   ```
   `simulate gas` hace sonar la alarma a todo volumen (`gas-normal` la quita). Avisa en casa antes de probarla.

## Privacidad

- **Tu sesión y las claves de los aparatos** se quedan en la carpeta de Casa y en la tele. La herramienta se niega a
  guardarlas dentro del repo y nunca las enseña en pantalla.
- **La luz, el calefactor y el gas** van por la red de casa con el protocolo local de Tuya. Funcionan aunque se caiga
  internet.
- **La puerta y el clima** llegan de la nube de Tuya: esos sensores van a pilas y solo hablan con ella. El acceso usa el
  mismo sistema oficial de compartir aparatos que la integración de Tuya de Home Assistant (un QR que apruebas en la
  app).

## Límites

- Solo Smart Life / Tuya por ahora. **Home Assistant está en camino.**
- Los avisos necesitan la tele encendida.
- Probado en una TCL con Google TV y en un Fire TV Stick 4K Max.
