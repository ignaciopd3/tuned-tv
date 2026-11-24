# Samsung Tizen

[English](samsung-tizen.md) · [Volver al README](../../README.es.md)

**Sirve para** teles Samsung con Tizen, desde 2015. Los modelos Orsay (smart TV antiguas de Samsung) no pueden
ejecutar apps de terceros.

**Estado:** 📘 guía lista; Tuned TV aún no automatiza Tizen. Mientras tanto, esta guía cuenta lo que se puede hacer
hoy, sobre todo con [free-my-tv](https://github.com/simbasjungles/free-my-tv) (MIT). El soporte en Tuned TV se apoyará
en una versión fija de esa herramienta.

## Qué se puede hacer sin root

- **Apagar el rastreo** en los ajustes de la propia tele. Es lo que más mejora la privacidad, y no necesita nada más.
- **Instalar un inicio limpio** en modo desarrollador (free-my-tv).
- **No se puede:** quitar ni deshabilitar las apps de Samsung que vienen de serie.

## 1. Apaga el rastreo

Los nombres y su sitio cambian de un año a otro. En los modelos recientes están en Ajustes → Todos los ajustes →
General y privacidad → Condiciones y privacidad (en los antiguos, Ajustes → Soporte → Condiciones y política):

- **Servicios de información de visualización** (ACR) → Desactivado.
- **Publicidad basada en intereses** → Desactivado; restablece el identificador publicitario si te lo ofrece.
- **Servicios de reconocimiento de voz** → Desactivado si no usas la voz.
- En los ajustes de Smart Hub, apaga el arranque automático de Smart Hub y la reproducción automática de contenido
  promocionado donde salgan.

## 2. Activa el modo desarrollador

1. Abre **Apps** en la tele y teclea **1 2 3 4 5** con el mando.
2. Activa el **Modo desarrollador**.
3. En **IP del PC anfitrión**, escribe la IP de tu ordenador.
4. Reinicia la tele (desenchúfala o mantén pulsado el botón de encendido hasta que se reinicie).

## 3. Instala un inicio limpio con free-my-tv

**Opción A: TizenBrew.** Usa TizenBrew Installer (de @reisxd), conéctate a la tele y añade el módulo
`simbasjungles/free-my-tv`. En las teles de 2023 en adelante hay que iniciar sesión una vez con una cuenta de Samsung.
Las de 2015 y 2016 no pueden con TizenBrew; usa la opción B.

**Opción B: compílalo e instálalo tú** (solo Python, sin Tizen Studio):

```bash
python3 tizen/build.py                               # genera FreeMyTV-tizen.wgt
python3 tizen/install.py <ip-de-la-tele>             # lo instala (y explica por qué falló, si falla)
python3 tizen/install.py <ip-de-la-tele> --uninstall
```

En las teles de 2023 en adelante, el certificado de firma se obtiene iniciando sesión con la cuenta de Samsung en el
navegador.

**Problemas conocidos** (de los informes de free-my-tv):

| Mensaje o modelo | Qué significa |
|---|---|
| `download failed[116]` | La tele no tiene espacio libre para apps. |
| `failed[118]` (p. ej. algunos modelos de 2016) | Ver `tizen/install-118.md` de free-my-tv. |
| Teles de 2017–2018 (Tizen 3 y 4) | Abrir los Ajustes de la tele desde el launcher puede bloquearla. |
| Teles de 2019–2020 | «Abrir la última app» no vuelve a abrir el launcher al encender. |

## Lo que vendrá en Tuned TV

- Un adaptador `tvopt/tizen` sobre una versión fija de free-my-tv: pasos de conexión, inventario (la ficha que la
  tele publica en el puerto 8001, y las apps) e instalación del inicio, con el mismo flujo de perfil y simulación que en
  los demás sistemas.
- Un perfil por cada modelo de Samsung que alguien pruebe: [CONTRIBUTING.es.md](../../CONTRIBUTING.es.md).

## Créditos

Los pasos del modo desarrollador, las herramientas y los problemas conocidos vienen de
[free-my-tv](https://github.com/simbasjungles/free-my-tv) (MIT) y sus colaboradores; TizenBrew es de @reisxd.
