#!/usr/bin/env bash
# Custom Power Menu — Dracula theme, Nerd Font glyphs

THEME="$HOME/.config/rofi/powermenu/custom/theme.rasi"

# --- Nerd Font glyphs ---
NF_SHUTDOWN=$'\uf011'
NF_REBOOT=$'\uf021'
NF_SUSPEND=$'\uf04c'
NF_LOCK=$'\uf023'
NF_LOGOUT=$'\uf08b'
NF_CHART=$'\uf201'

# --- System info ---
HOSTNAME=$(hostname)
UPTIME=$(uptime -p | sed 's/up //')

# RAM
RAM_TOTAL=$(free -h | awk '/Mem:/ {print $2}')
RAM_USED=$(free -h | awk '/Mem:/ {print $3}')
RAM_PCT=$(free | awk '/Mem:/ {printf "%.0f", $3/$2 * 100}')

# CPU
CPU_PCT=$(top -bn1 | awk '/^%Cpu/ {print 100 - $8}')

# Disk
DISK_USED=$(df -h / | awk 'NR==2 {print $3}')
DISK_TOTAL=$(df -h / | awk 'NR==2 {print $2}')
DISK_PCT=$(df / | awk 'NR==2 {gsub(/%/,""); print $5}')

# IP
IP_ADDR=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}')
[ -z "$IP_ADDR" ] && IP_ADDR="—"

# --- Build message ---
NL=$'\n'
MSG="<span foreground='#BD93F9'>${NF_CHART} ${HOSTNAME}</span>${NL}"
MSG+="<span foreground='#FFFFFF'>Uptime:</span> <span foreground='#50FA7B'>${UPTIME}</span>${NL}"
MSG+="<span foreground='#FFFFFF'>CPU:</span> <span foreground='#F1FA8C'>${CPU_PCT}%</span>  "
MSG+="<span foreground='#FFFFFF'>RAM:</span> <span foreground='#F1FA8C'>${RAM_USED}/${RAM_TOTAL} (${RAM_PCT}%)</span>${NL}"
MSG+="<span foreground='#FFFFFF'>Disk:</span> <span foreground='#F1FA8C'>${DISK_USED}/${DISK_TOTAL} (${DISK_PCT}%)</span>${NL}"
MSG+="<span foreground='#FFFFFF'>IP:</span> <span foreground='#8BE9FD'>${IP_ADDR}</span>"

# --- Menu entries ---
ENTRIES="${NF_LOCK}  Lock"
ENTRIES+="${NL}${NF_SUSPEND}  Suspend"
ENTRIES+="${NL}${NF_LOGOUT}  Logout"
ENTRIES+="${NL}${NF_REBOOT}  Reboot"
ENTRIES+="${NL}${NF_SHUTDOWN}  Shutdown"

# --- Launch Rofi ---
SELECTED=$(echo -e "$ENTRIES" | rofi -dmenu \
    -p "Power" \
    -mesg "$MSG" \
    -theme "$THEME" \
    -width 60 \
    -no-custom \
    2>/dev/null)

[ -z "$SELECTED" ] && exit 0

# --- Confirmation ---
confirm() {
    echo -e "  Yes\n  No" | rofi -dmenu \
        -p "Conferma" \
        -mesg "Sei sicuro?" \
        -theme "$THEME" \
        -width 30 \
        2>/dev/null
}

# --- Handle selection ---
case "$SELECTED" in
    *"${NF_SHUTDOWN}"*)
        confirm && systemctl poweroff
        ;;
    *"${NF_REBOOT}"*)
        confirm && systemctl reboot
        ;;
    *"${NF_SUSPEND}"*)
        confirm && systemctl suspend
        ;;
    *"${NF_LOCK}"*)
        i3lock-fancy --pixelate
        ;;
    *"${NF_LOGOUT}"*)
        confirm && i3-msg exit
        ;;
esac
