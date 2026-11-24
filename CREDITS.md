# Credits / Créditos

Tuned TV stands on the shoulders of these projects. Thank you!
Tuned TV se apoya en estos proyectos. ¡Gracias!

## cleanyourtv · MIT · © 2026 Gathin

<https://github.com/Gathin23/cleanyourtv>

- **The launcher.** Tuned TV builds cleanyourtv's launcher at the commit in
  [`launcher/patches/BASE`](launcher/patches/BASE), with the patches in [`launcher/patches/`](launcher/patches/) on top.
- **The add-ons** listed in [`launcher/patches/ADDONS`](launcher/patches/ADDONS) live in cleanyourtv's `addons/` and
  keep their authors: weather by @Sumyabazar1, remote-access by @maxhayim. The Casa add-on comes from Tuned TV's
  patches.
- **Android TV debloat lists:** the TCL C845 profile starts from cleanyourtv's G05 examples (65C735, 55C728, 65C935,
  65C745 and 55C735). Its model catalogue at [cleanyour.tv/tvs](https://cleanyour.tv/tvs) is the recommended starting
  point for new Android TV profiles.

## dumbtv · code MIT, device catalogue CC BY-SA 4.0 · © 2026 dumbtv contributors

<https://github.com/humblemuzzu/dumbtv>

- **Fire OS package lists**: [`profiles/fire-tv-4k-max-aftka/packages.remove`](profiles/fire-tv-4k-max-aftka/packages.remove)
  is adapted from dumbtv's catalogue entry `fireos-amazon-aftka-ps7713`, tested on three sticks by harupong, Elv1sh and
  rotenaple. That file is therefore under **CC BY-SA 4.0**, and so are lists derived from it.
- **Fire OS privacy settings and protected packages** (in `lib/protected.list`).
- **Techniques** behind launcher patches 0018 and 0019, re-implemented without copying code:
  - the Home button takeover through an accessibility service;
  - the launch through an exact alarm under a cover, with `min_futurity=0`;
  - reading the app in front from UsageStats;
  - turning accessibility off and on so Fire OS binds the service.

## free-my-tv · MIT

<https://github.com/simbasjungles/free-my-tv>

- **The LG webOS and Samsung Tizen guides:** Developer Mode, renewal, installation, known issues by model year.
- **Android TV notes**, such as wireless debugging pairing on Chromecast with Google TV and Play Protect on Android 14.
- Planned webOS and Tizen support will build on a pinned version of free-my-tv.

## Wallpapers · CC BY and CC BY-SA

Landscape photos from [Wikimedia Commons](https://commons.wikimedia.org), each under its own licence, with author,
licence, link and the changes made listed in [`launcher/CREDITS.md`](launcher/CREDITS.md). Adaptations of CC BY-SA
pictures stay under CC BY-SA, and so do the README screenshots in [`docs/images/`](docs/images/), which show `004.jpg`
("Lake Mystery, Canterbury, New Zealand 05" by Michal Klajban, CC BY-SA 4.0).

## Libraries used at run time (not bundled)

- [tuya-device-sharing-sdk](https://github.com/tuya/tuya-device-sharing-sdk) and
  [tinytuya](https://github.com/jasonacox/tinytuya) (both MIT) are used by the optional Casa tools in `tools/`, which
  you install yourself. `tools/casa_probe.py` signs in through Tuya's device sharing with
  [Home Assistant](https://github.com/home-assistant/core)'s public client registration (Apache 2.0), the same QR
  flow as Home Assistant's Tuya integration.
- [Control D](https://controld.com)'s free public resolver `p2.freedns.controld.com` is the private DNS the example
  profiles set; any DNS-over-TLS resolver works.

## Trademarks

Android TV, Google TV and Chromecast are trademarks of Google LLC. Fire TV, Fire OS, Alexa and Prime Video are
trademarks of Amazon.com, Inc. LG and webOS are trademarks of LG Electronics. Samsung and Tizen are trademarks of
Samsung Electronics. TCL is a trademark of TCL Corporation. Tuned TV is not affiliated with any of them.
