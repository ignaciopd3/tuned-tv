# Canales de la TDT: sintonizar y ordenar

[English](channels.md) · [Volver al README](../../README.es.md)

Tras una búsqueda automática los canales quedan como los numera la emisión: hay duplicados en SD, HD y UHD, canales de
prueba y de teletienda, y los que más ves acaban lejos. Esta guía te lleva por los tres pasos: **sintonizar**, ver si
**tu tele admite los canales UHD** y **ordenarlos a tu gusto**. El orden lo eliges tú. Tuned TV propone poner la mejor
versión de cada canal en su número, la UHD si tu tele la admite, pero nada obliga a ello.

## 1. Sintoniza

1. Conecta bien el cable de la antena a la entrada **ANT / RF** de la tele.
2. Busca en los ajustes la búsqueda de canales. El nombre cambia según la marca: *Canales → Búsqueda de canales*,
   *Sintonización automática*, *Instalación de canales*… En Google TV suele estar en *Ajustes → Canales y entradas →
   Canales*, o en el menú de la app de la tele.
3. Elige **Antena** (DVB-T/T2, no cable ni satélite) y tu país, y deja que termine.

- **Una búsqueda automática nueva borra el orden** que hayas hecho. Guarda tu lista (paso 3) para volver a aplicarla.
- **Vuelve a buscar** cuando desaparezcan canales o salgan sin señal: las emisiones cambian de frecuencia de vez en
  cuando.
- **Si el editor de canales no te deja moverlos**, desactiva *LCN* o *numeración automática* (en algunas teles) y
  vuelve a buscar.

## 2. ¿Tu tele admite los canales UHD?

Los canales UHD (4K) de la TDT se emiten en **DVB-T2** con vídeo **HEVC (H.265)**, y algunos en HDR (HLG). Muchas
teles 4K recientes los admiten, pero no todas, y las teles HD casi nunca.

- **Mira la ficha de tu modelo:** tiene que poner *DVB-T2* y *HEVC* o *H.265*.
- **O pruébalo:** pon un canal UHD tras sintonizar. Si se ve, tu tele los admite. Si sale en negro, con «formato no
  admitido» o «servicio no disponible», o no aparece tras la búsqueda, no los admite.

Con eso decides:

| Tu tele | Qué conviene |
|---|---|
| Admite UHD | Cada canal en su número con su versión UHD; la HD y la SD, ocultas o al final. |
| No admite UHD | La versión HD en su número; las UHD, ocultas para que no salgan en negro. |
| No lo tienes claro | Primero la HD; las UHD al final, para probarlas sin que estorben. |

## 3. Ordena

Escribe tu orden en un archivo de texto, `channels.txt`: un canal por línea, con el nombre **tal como sale en la lista
de la tele**.

```text
# Mi orden. Un canal por línea; «!» delante lo oculta; las líneas con # son notas.
Canal 1 UHD
Canal 2 UHD
Canal 3 HD
Canal 4 HD
# Versiones peores: ocultas
!Canal 1 HD
!Canal 1
!Canal 2 HD
!Teletienda
```

- Los canales que no pongas quedan detrás, en su orden de antes.
- Las radios no se tocan.
- Es tu lista y depende de tu zona: no hace falta compartirla.

### Aplicarlo

| Tu tele | Cómo |
|---|---|
| **TCL con Google TV** (app de la tele `com.tcl.tv`) | Automático con `tools/tcl_channels.py` (abajo). |
| **Otras Android TV y Google TV** | A mano, en el editor de canales de la tele: app de la tele → menú → *Canales* → *Editar* u *Organizar*. |
| **LG webOS y Samsung Tizen** | A mano, en su editor de canales (*Gestor de canales*, *Editar canales*). |
| **Fire TV Stick** | No tiene sintonizador. Las teles Fire TV Edition, con el editor de su guía. |

**En una TCL**, con la depuración activada (la [guía de Android TV](android-tv.es.md)) y nadie usando la tele:

```bash
export TV_SERIAL=<ip-de-la-tele>:5555
uv run python tools/tcl_channels.py channels.txt --dry-run   # lee la lista y enseña los cambios; no toca nada
uv run python tools/tcl_channels.py channels.txt             # los hace
```

La herramienta abre el editor de canales de la tele y mueve y oculta cada canal como lo harías con el mando. Comprueba
la pantalla cada pocos movimientos y, al final, relee la lista completa y corrige lo que falte. No toques el mando
mientras trabaja.

### ¿Por qué no es automático en todas las teles?

Android no deja que ADB escriba la lista de canales: el permiso que hace falta (`WRITE_EPG_DATA`) solo lo tienen las
apps del fabricante. Así que la única forma de automatizarlo es manejar el editor de la propia tele, pantalla a
pantalla, como hace la herramienta de TCL. Si haces una para tu marca, compártela: ver
[CONTRIBUTING.es.md](../../CONTRIBUTING.es.md).
