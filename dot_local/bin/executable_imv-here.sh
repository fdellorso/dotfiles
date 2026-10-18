#!/bin/sh
# imv-here.sh — apri imv sull'intera cartella partendo dal file dato.
# Uso: imv-here.sh FILE (da .desktop: imv-here.sh %F)
# imv da solo caricherebbe solo il file passato; passando la directory
# e -n, le frecce DX/SX scorrono tutti i fratelli della stessa cartella.
[ -z "$1" ] && exit 1
if [ -d "$1" ]; then
    exec imv "$1"
fi
dir=$(dirname -- "$1")
exec imv -n "$1" -- "$dir"
