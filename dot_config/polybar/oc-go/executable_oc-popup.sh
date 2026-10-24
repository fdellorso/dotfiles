#!/bin/sh
# oc-popup.sh --popup : toggle popup OpenCode Go (stessa posizione calendario).
BAR_HEIGHT=38
GAP=10
POPUP_WIDTH=420
POPUP_HEIGHT=340

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
POPUP_SCRIPT="${SCRIPT_DIR}/oc_popup.py"

case "$1" in
--popup)
    if pgrep -f "[o]c_popup.py" > /dev/null; then
        pkill -f "[o]c_popup.py"
        exit 0
    fi
    # Refresh on-demand: aggiorna la cache prima di aprire.
    # La barra la rilegge da sola ogni 10s (interval modulo).
    python3 "${SCRIPT_DIR}/oc_go_sync.py" > /dev/null 2>&1
    SCREEN_INFO=$(xrandr --query 2>/dev/null | grep ' connected' | head -1)
    WIDTH=$(echo "$SCREEN_INFO" | grep -oP '\d+x\d+' | head -1 | cut -dx -f1)
    WIDTH=${WIDTH:-1920}
    pos_x=$((WIDTH - POPUP_WIDTH - GAP - GAP))
    pos_y=$((BAR_HEIGHT + GAP + GAP + GAP))
    python3 "$POPUP_SCRIPT" --posx="$pos_x" --posy="$pos_y" --width="$POPUP_WIDTH" --height="$POPUP_HEIGHT" &
    ;;
*)
    echo "uso: $0 --popup"
    ;;
esac
