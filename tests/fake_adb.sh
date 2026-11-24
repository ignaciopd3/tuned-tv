#!/usr/bin/env bash
# adb simulado para tests. El estado del «dispositivo» vive en $FAKE_TV (ver fake_device.sh).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
if [[ ${1:-} == -s ]]; then shift 2; fi
cmd=${1:-}
shift || true
case $cmd in
  connect) echo "connected to ${1:-}" ;;
  get-state)
    st=$(cat "$FAKE_TV/state" 2>/dev/null || echo device)
    if [[ $st == device ]]; then echo device; else echo "error: device $st" >&2; exit 1; fi ;;
  push) mkdir -p "$FAKE_TV/files"; cp "$1" "$FAKE_TV/files/${2##*/}" ;;
  shell) exec bash -c "source '$HERE/fake_device.sh'; $*" ;;
  *) echo "fake adb: no soportado: $cmd" >&2; exit 1 ;;
esac
