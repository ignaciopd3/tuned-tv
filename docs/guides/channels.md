# Terrestrial TV channels: tune and sort

[Español](channels.es.md) · [Back to the README](../../README.md)

After an automatic scan, channels end up numbered the way the broadcast says: SD, HD and UHD duplicates, test and
shopping channels, and the ones you watch most end up far away. This guide covers the three steps: **tune**, check
whether **your TV supports UHD channels**, and **sort them your way**. You choose the order. Tuned TV suggests putting
each channel's best version on its number, the UHD one if your TV supports it, but nothing forces you to.

## 1. Tune

1. Plug the aerial cable firmly into the TV's **ANT / RF** input.
2. Find the channel scan in the settings. The name changes by brand: *Channels → Channel scan*, *Auto tuning*,
   *Channel installation*… On Google TV it is usually under *Settings → Channels & Inputs → Channels*, or in the TV
   app's menu.
3. Pick **Antenna** (DVB-T/T2, not cable or satellite) and your country, and let it finish.

- **A new automatic scan wipes your order.** Keep your list (step 3) so you can apply it again.
- **Scan again** when channels disappear or have no signal: broadcasts move frequency now and then.
- **If the channel editor will not let you move channels**, turn off *LCN* or *automatic numbering* (on some TVs) and
  scan again.

## 2. Does your TV support UHD channels?

UHD (4K) terrestrial channels are broadcast in **DVB-T2** with **HEVC (H.265)** video, some in HDR (HLG). Many recent
4K TVs support them, but not all, and HD TVs almost never do.

- **Check your model's spec sheet:** it must list *DVB-T2* and *HEVC* or *H.265*.
- **Or try it:** tune in a UHD channel after the scan. If it plays, your TV supports them. If it stays black, says
  "format not supported" or "service not available", or never shows up after the scan, it does not.

Then decide:

| Your TV | Best choice |
|---|---|
| Supports UHD | Each channel on its number with its UHD version; HD and SD hidden or at the end. |
| No UHD | The HD version on its number; UHD channels hidden so they don't show up black. |
| Not sure | HD first; UHD channels at the end, to try them without getting in the way. |

## 3. Sort

Write your order in a text file, `channels.txt`: one channel per line, named **exactly as the TV's list shows it**.

```text
# My order. One channel per line; "!" in front hides it; lines with # are notes.
Channel 1 UHD
Channel 2 UHD
Channel 3 HD
Channel 4 HD
# Lower-quality versions: hidden
!Channel 1 HD
!Channel 1
!Channel 2 HD
!Shopping
```

- Channels you leave out stay behind, in their previous order.
- Radio stations are not touched.
- It's your list and depends on where you live: there's no need to share it.

### Applying it

| Your TV | How |
|---|---|
| **TCL with Google TV** (TV app `com.tcl.tv`) | Automatic, with `tools/tcl_channels.py` (below). |
| **Other Android TV and Google TV** | By hand, in the TV's channel editor: TV app → menu → *Channels* → *Edit* or *Organise*. |
| **LG webOS and Samsung Tizen** | By hand, in their channel editor (*Channel manager*, *Edit channels*). |
| **Fire TV Stick** | No tuner. Fire TV Edition TVs: with their guide's editor. |

**On a TCL**, with debugging enabled (the [Android TV guide](android-tv.md)) and nobody using the TV:

```bash
export TV_SERIAL=<tv-ip>:5555
uv run python tools/tcl_channels.py channels.txt --dry-run   # reads the list and shows the changes; touches nothing
uv run python tools/tcl_channels.py channels.txt             # makes them
```

The tool opens the TV's channel editor and moves and hides each channel as you would with the remote. It checks the
screen every few moves and, at the end, reads the whole list again and fixes what is left. Don't touch the remote
while it works.

### Why isn't it automatic on every TV?

Android doesn't let ADB write the channel list: the permission it needs (`WRITE_EPG_DATA`) is reserved for the
manufacturer's apps. So the only way to automate it is to drive the TV's own editor, screen by screen, as the TCL tool
does. If you build one for your brand, share it: see [CONTRIBUTING.md](../../CONTRIBUTING.md).
