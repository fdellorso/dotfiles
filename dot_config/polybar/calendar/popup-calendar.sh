#!/bin/sh
#
# Polybar Calendar Module - Nextcloud Integration
# Basato su: polybar-scripts/popup-calendar
# Modificato per: popup Tkinter con eventi Nextcloud
#

BAR_HEIGHT=38   # polybar height (30pt) + border-top (8px)
GAP=10          # i3 gap size
POPUP_WIDTH=420 # larghezza popup Tkinter
POPUP_HEIGHT=480 # altezza popup Tkinter
DATE="$(date +"%a %d %H:%M")"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
POPUP_SCRIPT="${SCRIPT_DIR}/calendar_popup.py"

case "$1" in
--popup)
    # Toggle: se il popup è già aperto, chiudilo
    if pgrep -f calendar_popup.py > /dev/null; then
        pkill -f calendar_popup.py
        exit 0
    fi

    # Posizione: in alto a destra, sotto polybar, con gap i3
    # Ottieni dimensioni schermo con xrandr
    SCREEN_INFO=$(xrandr --query 2>/dev/null | grep ' connected' | head -1)
    WIDTH=$(echo "$SCREEN_INFO" | grep -oP '\d+x\d+' | head -1 | cut -dx -f1)
    
    # Fallback se xrandr non funziona
    WIDTH=${WIDTH:-1920}
    
    pos_x=$((WIDTH - POPUP_WIDTH - GAP))
    pos_y=$((BAR_HEIGHT + GAP + GAP))  # gap sotto polybar + gap finestra

    # Lancia il popup Python con le coordinate e dimensioni
    python3 "$POPUP_SCRIPT" --posx="$pos_x" --posy="$pos_y" --width="$POPUP_WIDTH" --height="$POPUP_HEIGHT" &
    ;;
*)
    # Output per la barra: icona nerd font + data
    echo "$(printf '\uf073') $(date +'%d %b %Y')"
    ;;
esac
