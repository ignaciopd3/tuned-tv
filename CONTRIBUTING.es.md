# Colaborar con Tuned TV

[English](CONTRIBUTING.md)

¡Gracias por ayudar! Lo que más aporta es un **perfil para un modelo de tele** que todavía no esté: el siguiente con
esa tele empieza desde algo probado en vez de desde cero. Los avisos de fallos, las guías, las traducciones y el código
son igual de bienvenidos.

Con amabilidad y paciencia; seguimos el [Código de conducta](CODE_OF_CONDUCT.md). Las issues y las pull requests pueden
ir en inglés o en español.

## Añadir un modelo de tele

### 1. Comprueba que no está ya

Mira en [`profiles/`](profiles/) y en las [issues](https://github.com/ignaciopd3/tuned-tv/issues). Si alguien ya está
con él, únete. Si no, abre una issue **New TV model**: reúne los datos en un sitio y avisa a los demás de que estás en
ello.

### 2. Conéctate e identifica el modelo

Sigue la [guía de tu sistema](README.es.md#sistemas) y después:

```bash
adb shell getprop ro.product.manufacturer
adb shell getprop ro.product.model
adb shell getprop ro.board.platform          # chip
adb shell getprop ro.build.version.release   # versión de Android
adb shell getprop | grep -i -E "product|board|hardware|client_type|fingerprint"
```

Elige **una propiedad cuyo valor solo tengan este modelo y su familia de firmware**. `ro.product.model` suele ser
demasiado genérico, así que mira `ro.product.name`, una propiedad de la marca (`persist.tcl.client_type` en TCL) o,
como último recurso, `ro.build.fingerprint`.

### 3. Crea la carpeta del perfil

```bash
cp -r profiles/_template profiles/<marca>-<modelo>-<chip>     # en minúsculas, p. ej. tcl-c845-mt9615
```

Rellena `profile.env`:

```
PROFILE_NAME="Marca Modelo · chip · región"
MATCH_PROP=<la propiedad del paso 2>
MATCH_VALUE=<su valor>
ABI=<adb shell getprop ro.product.cpu.abilist, el primero>
```

El motor se niega a tocar ninguna tele mientras `MATCH_VALUE` sea `CAMBIAR`.

### 4. Arma las listas

- **Parte de listas probadas:** los [ejemplos de cleanyourtv](https://cleanyour.tv/tvs) para Android TV y Google TV
  (unos 400 modelos) y el [catálogo de dumbtv](https://github.com/humblemuzzu/dumbtv) para Fire OS. Cítalos en el README
  del perfil; el catálogo de dumbtv es CC BY-SA 4.0, así que las listas que salen de él siguen con esa licencia.
- **Mira lo que tiene tu tele:** `adb shell pm list packages -s` (de sistema) y `adb shell pm list packages -3`
  (instalados).
- **Un paquete por línea, con su motivo:** `com.vendor.ads   # servicio de anuncios de la marca, recomendaciones en el
  inicio`.
- **Lo que tenga un coste** va a `packages.caution`, no a `packages.remove`: actualizadores, envío desde el móvil, voz,
  funciones de imagen y sonido, apps de serie que alguien podría usar. Lo que se queda a propósito va como
  `# KEEP paquete   # por qué`.
- **Nunca** pongas inicios, teclados, wifi, HDMI, DRM, la app de la tele o del sintonizador ni nada de
  `lib/protected.list`; el motor los rechaza de todas formas.
- `settings.conf`, `appops.conf`, `props.conf` y `remap.conf` son opcionales. Los perfiles del
  [Fire TV](profiles/fire-tv-4k-max-aftka/) y de la [TCL](profiles/tcl-c845-mt9615/) usan todos.

### 5. Simula, aplica y prueba

```bash
export TV_SERIAL=<ip-de-la-tele>:5555
uv run run.py motor --profile <tu-perfil> --action audit
uv run run.py medir --perfil <tu-perfil>                      # antes, quieta en el inicio
uv run run.py motor --profile <tu-perfil> --action all --dry-run
uv run run.py motor --profile <tu-perfil> --action all
```

Después prueba, una a una, las cosas que usa la gente:

- wifi y cable;
- cada entrada HDMI;
- la TDT;
- el sonido, también una barra de sonido o eARC;
- el mando, también los botones de apps;
- las apps;
- el envío desde el móvil;
- la tele tras un reinicio.

Vuelve a medir (`run.py medir`), quieta en el inicio. Si algo se rompió, `--action rollback` y pasa ese paquete a
`packages.caution` con una nota.

### 6. Escribe el README del modelo

`profiles/<tu-perfil>/README.md` en inglés, y también `README.es.md` si puedes. Sigue los que ya hay:

- una tabla con el modelo, el sistema, el chip, cómo conectarse y cuándo lo probaste;
- qué se deshabilita y por qué, por grupos, y lo que cuesta (voz, envío desde el móvil…);
- resultados antes y después;
- las rarezas del modelo;
- cómo usarlo y cómo deshacerlo.

### 7. Sin datos privados, comprueba y envía

- **Nada privado:** escribe `<tv-ip>` en vez de direcciones, y no pongas correos, números de serie, cuentas ni nombres
  de wifi. Las carpetas `backups/` las ignora git; no las fuerces nunca.
- Lanza las comprobaciones de abajo. Después abre una pull request: la plantilla trae la lista de comprobación.

## Aportar código

```bash
uv sync
uv run ruff check
uv run ruff format --check
uv run pyright
uv run pytest
uv run python -m tvopt.core.privacy
```

- **Python 3.12**, con tipos. `pyright` va en modo estricto en `tvopt/`.
- **Prueba sin tele:** los escenarios del motor van contra una tele simulada (`tests/fake_adb.sh`,
  `tests/fake_device.sh`). Añade un escenario si cambias el comportamiento del motor.
- **Cambios pequeños y centrados**, una idea por pull request.
- **Mensajes de commit:** un asunto en imperativo (`Add profile for Sony KD-55X85J`, `Engine: skip packages missing on
  the TV`), y en el cuerpo, el porqué.
- **Los comentarios del código están en español** por historia; en código nuevo vale el inglés. La documentación es
  bilingüe: actualiza los dos idiomas si puedes, o di en la PR que falta la traducción.
- **Los cambios del launcher** son parches sobre cleanyourtv: haz commit en un clon de cleanyourtv y expórtalos con
  `git format-patch` a `launcher/patches/`, manteniendo la numeración. Lo que no sea propio de Tuned TV, mándalo también
  a cleanyourtv.

## Traducciones

Todo lo que sale en la tele sigue el idioma de la tele. El inglés es el idioma por defecto y el español está
completo; cualquier otro idioma sale en inglés hasta que alguien lo traduzca.

- **Los textos de Tuned TV en el launcher** están en su `strings.xml` (`values/` en inglés, `values-es/` en español),
  que añaden los parches de `launcher/patches/`.
- **El complemento Casa** tiene sus textos en `addons/casa/app/src/main/res/values*/strings.xml`.
- **Para añadir un idioma**, crea `values-<código>/strings.xml` (por ejemplo `values-fr/`) con los mismos nombres, haz
  commit en un clon de cleanyourtv y exporta el parche. Las pruebas de Casa comprueban que cada idioma tiene todos
  los textos con los mismos huecos.
- Las traducciones no cuestan nada al usar la tele: Android elige el idioma una vez, al abrir la app.
- **La herramienta del ordenador** escribe sus mensajes en español dentro de `tr()` y guarda el inglés en
  `tvopt/core/i18n_en.py`. Un mensaje nuevo necesita su línea en inglés; `tests/test_i18n.py` falla si falta, y también
  si un mensaje se enseña sin `tr()`. Habla el idioma del sistema, o el de `TVOPT_LANG` (`en`, `es`).

## Revisión

Un mantenedor revisa cada pull request. El CI tiene que pasar (estilo, tipos, pruebas y el detector de datos privados).
En los perfiles, el plan de la simulación y las medidas de antes y después en la PR hacen la revisión rápida.

## Licencia

Al colaborar aceptas que tu aportación se publique con la [licencia MIT](LICENSE). Lo que salga de fuentes CC BY-SA
mantiene esa licencia; márcalo en el perfil y en [CREDITS.md](CREDITS.md).
