#!/usr/bin/env bash
# oc-go.sh — icona stato piano OpenCode Go (legge cache, mai rete/DB).
CACHE=~/.cache/polybar/oc-go/status.json
OFF="%{F#6272A4}%{F-}"
[ -f "$CACHE" ] || { echo "$OFF"; exit 0; }
PCT=$(python3 -c "import json;print(json.load(open('$CACHE'))['windows']['month']['pct'])" 2>/dev/null)
[ -z "$PCT" ] && { echo "$OFF"; exit 0; }
INT=${PCT%.*}
if [ "$INT" -ge 90 ]; then C="%{F#FF5555}"; elif [ "$INT" -ge 70 ]; then C="%{F#FFB86C}"; else C="%{F#50FA7B}"; fi
echo "${C} ${PCT}%{F-}"
