# LG webOS

[English](lg-webos.md) · [Volver al README](../../README.es.md)

**Sirve para** teles LG con webOS 3 o posterior.

**Estado:** 📘 guía lista; Tuned TV aún no automatiza webOS. Mientras tanto, esta guía cuenta lo que se puede hacer
hoy, sobre todo con [free-my-tv](https://github.com/simbasjungles/free-my-tv) (MIT). El soporte en Tuned TV se
apoyará en una versión fija de esa herramienta.

## Qué se puede hacer sin root

- **Apagar el rastreo** en los ajustes de la propia tele. Es lo que más mejora la privacidad, y no necesita nada más.
- **Instalar un inicio limpio** con el modo desarrollador de LG (free-my-tv), para empezar en tus apps y no en las
  filas de sugerencias de LG.
- **No se puede:** quitar ni deshabilitar las apps de LG que vienen de serie. webOS no lo deja sin root, y el root
  queda fuera de este proyecto.

## 1. Apaga el rastreo

Los nombres y su sitio cambian de un año a otro; busca estos:

- **Live Plus** (ACR, el servicio que reconoce lo que sale en pantalla): Ajustes → Todos los ajustes → General →
  Sistema → Ajustes adicionales → Live Plus → Desactivado.
- **Acuerdos de usuario:** Ajustes → Todos los ajustes → Soporte → Privacidad y condiciones → Acuerdos de usuario.
  Desmarca *Información de visualización*, *Información de voz* y *Publicidad basada en intereses*.
- **Seguimiento publicitario:** en esos mismos menús de privacidad, *Limitar el seguimiento de anuncios* → Activado.
- **Promoción en el inicio y reproducción automática:** en los ajustes del inicio, apaga *Promoción en el inicio*,
  *Recomendación de contenido* y la reproducción automática donde salgan.

## 2. Activa el modo desarrollador

1. Crea una cuenta gratuita de desarrollador de LG en [webostv.developer.lge.com](https://webostv.developer.lge.com).
2. En la tele, abre la LG Content Store, instala **Developer Mode** e inicia sesión con esa cuenta.
3. Activa **Dev Mode Status**; la tele se reinicia.
4. Vuelve a abrir Developer Mode y activa **Key Server**.
5. Apunta la IP de la tele y la frase de paso que enseña la app.

**El modo desarrollador caduca a los 40 días, más o menos.** Se renueva con el botón **EXTEND** de la app o con
`renew.py` de free-my-tv, que necesita la tele encendida y accesible y la clave que guardó `install.py`. Basta con
renovarlo cada semana, y `renew.py` escribe la línea para cron (macOS y Linux) o para el Programador de tareas
(Windows).

## 3. Instala un inicio limpio con free-my-tv

Necesitas Python 3 y la tele en la misma wifi que el ordenador. Desde un clon de free-my-tv:

```bash
python3 webos/apps.py <ip-de-la-tele>       # lee las apps instaladas (hace falta en webOS 3)
python3 webos/build.py                      # empaqueta la app y config.properties en un .ipk, sin herramientas de LG
python3 webos/install.py <ip-de-la-tele>    # la instala por el modo desarrollador; la primera vez pide la frase de paso
python3 webos/renew.py <ip-de-la-tele>      # alarga el modo desarrollador
python3 webos/install.py <ip-de-la-tele> --uninstall
```

Conviene saber:

- En **webOS 6 y posteriores**, la app no puede ver las apps instaladas hasta que le das permiso una vez; mientras
  tanto, enseña las más conocidas.
- En las teles que no son 4K se instala a 1280 × 720.
- Mantener pulsada una tecla de número con la app abierta permite abrirla desde cualquier sitio.

## Lo que vendrá en Tuned TV

- Un adaptador `tvopt/webos` sobre una versión fija de free-my-tv: pasos de conexión, inventario (información del
  sistema y apps), instalación del inicio y renovación del modo desarrollador, con el mismo flujo de perfil y
  simulación que en los demás sistemas.
- Un perfil por cada modelo de LG que alguien pruebe: [CONTRIBUTING.es.md](../../CONTRIBUTING.es.md).

## Créditos

Los pasos del modo desarrollador, la renovación y las herramientas vienen de
[free-my-tv](https://github.com/simbasjungles/free-my-tv) (MIT).
