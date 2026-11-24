# shellcheck shell=bash
# Imita getprop/pm/cmd/settings/sh/rm de Android sobre ficheros en $FAKE_TV:
#   props          «[clave]: [valor]»
#   pkgs           «paquete estado tipo» (estado: enabled|disabled|uninstalled · tipo: s|3)
#   settings.<ns>  «clave=valor», ordenado con LC_ALL=C
#   files/         destino de adb push
#   die_after      N: tras N mutaciones se corta la «conexión» (kill del shell remoto)
export LC_ALL=C
# mksh (el sh de Android) trae alias de serie que tapan funciones, p. ej. r='\builtin fc -e -'.
shopt -s expand_aliases
alias r='fc -e -'

_mut() {
  local n=0
  if [[ -f $FAKE_TV/mut_count ]]; then n=$(<"$FAKE_TV/mut_count"); fi
  n=$((n + 1))
  echo "$n" >"$FAKE_TV/mut_count"
  if [[ -f $FAKE_TV/die_after ]] && ((n > $(<"$FAKE_TV/die_after"))); then
    command rm -f "$FAKE_TV/die_after"
    kill -9 $$ # mata el shell remoto (simula caída de ADB)…
    exit 255   # …y el subshell actual, sin aplicar esta mutación
  fi
}

_pkg_change() { # <paquete> <nuevo estado>
  _mut
  grep -q "^$1 " "$FAKE_TV/pkgs" || { echo "Unknown package: $1" >&2; return 1; }
  awk -v p="$1" -v s="$2" '$1 == p { $2 = s } { print }' "$FAKE_TV/pkgs" >"$FAKE_TV/pkgs.tmp"
  mv "$FAKE_TV/pkgs.tmp" "$FAKE_TV/pkgs"
}

_pm_list() {
  awk -v fl=" $* " '
    { u = ($2 == "uninstalled") }
    index(fl, " -f ") { if (index(fl, " -u ") || !u) print "package:/fake/" $1 ".apk=" $1; next }
    index(fl, " -u ") { print "package:" $1; next }
    u { next }
    index(fl, " -e ") { if ($2 == "enabled") print "package:" $1; next }
    index(fl, " -d ") { if ($2 == "disabled") print "package:" $1; next }
    index(fl, " -s ") { if ($3 == "s") print "package:" $1; next }
    index(fl, " -3 ") { if ($3 == "3") print "package:" $1; next }
    { print "package:" $1 }' "$FAKE_TV/pkgs"
}

getprop() {
  if (($#)); then sed -n "s/^\[$1\]: \[\(.*\)\]\$/\1/p" "$FAKE_TV/props"; else cat "$FAKE_TV/props"; fi
}

setprop() { # <clave> <valor>: reescribe la línea de props; con valor vacío la quita
  _mut
  { grep -vF "[$1]: " "$FAKE_TV/props" || true; [[ -z ${2-} ]] || printf '[%s]: [%s]
' "$1" "$2"; } >"$FAKE_TV/props.tmp"
  command mv "$FAKE_TV/props.tmp" "$FAKE_TV/props"
}

pm() {
  local sub=$1
  shift
  case $sub in
    list) _pm_list "$@" ;;
    disable-user) _pkg_change "${@: -1}" disabled ;;
    enable) _pkg_change "${@: -1}" enabled ;;
    uninstall) _pkg_change "${@: -1}" uninstalled ;;
    *) echo "fake pm: no soportado: $sub" >&2; return 1 ;;
  esac
}

cmd() {
  case "$1 ${2:-}" in
    "package install-existing") _pkg_change "${@: -1}" enabled ;;
    "wifi "*) echo "fake cmd $*" ;;
    "appops get")
      grep -q "^$3 " "$FAKE_TV/pkgs" || { echo "Error: No UID for $3 in user 0" >&2; return 255; }
      local m; m=$(awk -v p="$3" -v o="$4" '$1 == p && $2 == o { print $3 }' "$FAKE_TV/appops" 2>/dev/null)
      if [[ -n $m ]]; then echo "$4: $m; time=+1s ago"; else printf 'No operations.
Default mode: allow
'; fi ;;
    "appops set")
      _mut
      grep -q "^$3 " "$FAKE_TV/pkgs" || { echo "Error: No UID for $3 in user 0" >&2; return 255; }
      { awk -v p="$3" -v o="$4" '!($1 == p && $2 == o)' "$FAKE_TV/appops" 2>/dev/null
        [[ $5 == default ]] || echo "$3 $4 $5"; } | sort >"$FAKE_TV/appops.tmp"
      command mv "$FAKE_TV/appops.tmp" "$FAKE_TV/appops" ;;
    *) echo "fake cmd: no soportado: $*" >&2; return 1 ;;
  esac
}

settings() {
  local op=$1 f=$FAKE_TV/settings.$2 key=${3-}
  case $op in
    list) cat "$f" ;;
    put) _mut; { grep -v "^$key=" "$f" || true; printf '%s=%s\n' "$key" "$4"; } | sort >"$f.tmp"; mv "$f.tmp" "$f" ;;
    delete) _mut; { grep -v "^$key=" "$f" || true; } >"$f.tmp"; mv "$f.tmp" "$f" ;;
    get) local v; v=$(sed -n "s/^$key=//p" "$f"); echo "${v:-null}" ;;
    *) echo "fake settings: no soportado: $op" >&2; return 1 ;;
  esac
}

dumpsys() {
  if [[ "$*" == "meminfo -c" ]]; then command cat "$FAKE_TV/perf/meminfo-c.txt"; else echo "fake dumpsys $*"; fi
}

# Rutas de la TV → files/ (solo importa el nombre del fichero)
sh() { source "$FAKE_TV/files/${1##*/}"; }
rm() {
  local a
  for a in "$@"; do
    if [[ $a != -* ]]; then command rm -f "$FAKE_TV/files/${a##*/}"; fi
  done
}

# Medición de rendimiento (run.py medir): /proc y las órdenes lentas salen de $FAKE_TV/perf/, capturado de una
# tele real (tests/fixtures/android_perf). sleep pasa a la segunda lectura de /proc/stat, como el tiempo real.
_proc_args() { # cada argumento /proc/… pasa a $FAKE_TV/perf/…; el resto, tal cual (uno por línea)
  local a
  for a in "$@"; do
    if [[ $a == /proc/* ]]; then printf '%s\n' "$FAKE_TV/perf${a#/proc}"; else printf '%s\n' "$a"; fi
  done
}
cat() { local -a a=(); mapfile -t a < <(_proc_args "$@"); command cat "${a[@]}"; }
head() { local -a a=(); mapfile -t a < <(_proc_args "$@"); command head "${a[@]}"; }
grep() { local -a a=(); mapfile -t a < <(_proc_args "$@"); command grep "${a[@]}"; }
sleep() {
  if [[ -f $FAKE_TV/perf/stat.after ]]; then command cp "$FAKE_TV/perf/stat.after" "$FAKE_TV/perf/stat"; fi
}
top() { command cat "$FAKE_TV/perf/top.txt"; }
df() { command cat "$FAKE_TV/perf/df.txt"; }
