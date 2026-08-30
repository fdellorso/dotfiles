#!/usr/bin/env bash
# AI Agent Launcher — Rofi module for i3
# Shows OpenCode usage stats, project list, and prompt input for pi.dev

DB="$HOME/.local/share/opencode/opencode.db"
ROFI_THEME="$HOME/.config/rofi/ai-launcher/theme.rasi"

# --- Query OpenCode DB ---
if [ -f "$DB" ]; then
    STATS=$(sqlite3 "$DB" \
        "SELECT count(*), printf('%.2f',sum(cost)), sum(tokens_input), sum(tokens_output) FROM session;" 2>/dev/null)
    SESSIONS=$(echo "$STATS" | cut -d'|' -f1)
    COST=$(echo "$STATS" | cut -d'|' -f2)
    TOKENS_IN=$(echo "$STATS" | cut -d'|' -f3)
    TOKENS_OUT=$(echo "$STATS" | cut -d'|' -f4)

    # Format token counts
    TOKENS_IN_FMT=$(echo "$TOKENS_IN" | awk '{
        if ($1 >= 1000000) printf "%.1fM", $1/1000000
        else if ($1 >= 1000) printf "%.1fK", $1/1000
        else print $1
    }')
    TOKENS_OUT_FMT=$(echo "$TOKENS_OUT" | awk '{
        if ($1 >= 1000000) printf "%.1fM", $1/1000000
        else if ($1 >= 1000) printf "%.1fK", $1/1000
        else print $1
    }')

    # Last model used
    LAST_MODEL=$(sqlite3 "$DB" \
        "SELECT model FROM session ORDER BY time_created DESC LIMIT 1;" 2>/dev/null)
    LAST_MODEL_NAME=$(echo "$LAST_MODEL" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
    [ -z "$LAST_MODEL_NAME" ] && LAST_MODEL_NAME="—"

    # Get projects
    PROJECTS=$(sqlite3 "$DB" \
        "SELECT DISTINCT worktree FROM project ORDER BY worktree;" 2>/dev/null)
else
    SESSIONS="—"
    COST="—"
    TOKENS_IN_FMT="—"
    TOKENS_OUT_FMT="—"
    LAST_MODEL_NAME="—"
    PROJECTS=""
fi

# --- Build message (static, non-selectable) ---
# Colors from shared/colors.rasi: background=#1E1F29, foreground=#FFFFFF, selected=#BD93F9, active=#50FA7B, urgent=#FF5555
NF_CHART=$'\uf201'
NF_PROMPT=$'\uf12c'
NF_FOLDER=$'\uf07b'
NF_LINK=$'\uf0c1'
NL=$'\n'
MSG="<span foreground='#BD93F9'>${NF_CHART} OpenCode Go</span>${NL}"
MSG+="<span foreground='#FFFFFF'>Sessioni:</span> <span foreground='#BD93F9'>${SESSIONS}</span>  "
MSG+="<span foreground='#FFFFFF'>Costo:</span> <span foreground='#50FA7B'>\$${COST}</span>${NL}"
MSG+="<span foreground='#FFFFFF'>Modello:</span> <span foreground='#FF5555'>${LAST_MODEL_NAME}</span>${NL}"
MSG+="<span foreground='#FFFFFF'>Token:</span> <span foreground='#BD93F9'>${TOKENS_IN_FMT} in / ${TOKENS_OUT_FMT} out</span>"

# --- Build selectable entries ---
ENTRIES="${NF_PROMPT}  Prompt → pi.dev"

if [ -n "$PROJECTS" ]; then
    while IFS= read -r proj; do
        [ -z "$proj" ] && continue
        # Skip root project
        [ "$proj" = "/" ] && continue
        PROJ_NAME=$(basename "$proj")
        ENTRIES+="${NL}${NF_FOLDER}  ${PROJ_NAME}  →  ${proj}"
    done <<< "$PROJECTS"
fi

ENTRIES+="${NL}${NF_LINK}  OpenCode Go — sito ufficiale"

# --- Launch Rofi ---
SELECTED=$(echo -e "$ENTRIES" | rofi -dmenu \
    -p "${NF_CHART} AI" \
    -mesg "$MSG" \
    -theme "$ROFI_THEME" \
    -width 60 \
    -no-custom \
    2>/dev/null)

[ -z "$SELECTED" ] && exit 0

# --- Handle selection ---
case "$SELECTED" in
    *"Prompt → pi.dev"*)
        PROMPT=$(rofi -dmenu -p "${NF_PROMPT} Prompt" -theme "$ROFI_THEME" 2>/dev/null)
        cd "$HOME"
        if [ -n "$PROMPT" ]; then
            alacritty -e pi "$PROMPT"
        else
            alacritty -e pi
        fi
        ;;

    *"${NF_FOLDER}"*)
        PROJ_PATH=$(echo "$SELECTED" | sed 's/.*→  //')
        if [ -d "$PROJ_PATH" ]; then
            cd "$PROJ_PATH" && alacritty -e opencode
        fi
        ;;
    *"${NF_LINK}"*)
        xdg-open "https://opencode.ai" 2>/dev/null &
        ;;
esac
