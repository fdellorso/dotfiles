#!/usr/bin/env bash
# nc-sync.sh — stato sync Nextcloud per polybar (sola lettura).
# Grigio: client spento | Verde: ok | Rosso + N: errori | Arancio: stato ignoto.
C_OK="%{F#50FA7B}%{F-}"
C_ERR="%{F#FF5555}"
C_OFF="%{F#6272A4}%{F-}"
C_UNK="%{F#FFB86C} ?%{F-}"

pgrep -x nextcloud >/dev/null || { echo "$C_OFF"; exit 0; }

ERR=0
FOUND=0
for db in ~/Nextcloud/.sync_*.db; do
    [ -e "$db" ] || continue
    FOUND=1
    N=$(sqlite3 "file:${db}?immutable=1" \
        "SELECT (SELECT COUNT(*) FROM blacklist)+(SELECT COUNT(*) FROM conflicts);" 2>/dev/null)
    [ -n "$N" ] && ERR=$((ERR + N))
done

[ "$FOUND" -eq 0 ] && { echo "$C_UNK"; exit 0; }
[ "$ERR" -gt 0 ] 2>/dev/null && echo "${C_ERR} ${ERR}%{F-}" || echo "$C_OK"
