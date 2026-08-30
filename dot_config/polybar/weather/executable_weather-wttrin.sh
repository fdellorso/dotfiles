#!/bin/bash
# Weather plugin for Polybar — wttr.in (no API key)

CITY="Cadenazzo"
LANG="it"

COLOR_CLOUD="#606060"
COLOR_THUNDER="#d3b987"
COLOR_LIGHT_RAIN="#73cef4"
COLOR_HEAVY_RAIN="#b3deef"
COLOR_SNOW="#FFFFFF"
COLOR_FOG="#606060"
COLOR_SUN="#ffc24b"
COLOR_MOON="#FFFFFF"
COLOR_ERR="#f43753"
COLOR_WIND="#73cef4"
COLOR_COLD="#b3deef"
COLOR_HOT="#f43753"
COLOR_NORMAL_TEMP="#FFFFFF"
COLOR_TEXT=""

WEATHER_FONT_CODE=2
TEMP_FONT_CODE=1
DISPLAY_WIND="yes"
BEAUFORTICON="yes"
KNOTS="no"
DECIMALS=0
MIN_WIND=0
DISPLAY_FORCE="yes"
DISPLAY_WIND_UNIT="yes"
HOT_TEMP=25
COLD_TEMP=0
DISPLAY_LABEL="yes"

[ -n "$COLOR_TEXT" ] && CTB="%{F$COLOR_TEXT}" && CTE="%{F-}" || CTB="" && CTE=""

URL="wttr.in/${CITY}?format=j1&lang=${LANG}"
RESPONSE=$(curl -s --max-time 10 "$URL")
[ $? -ne 0 ] || [ -z "$RESPONSE" ] && echo " " && exit 0

WID=$(echo "$RESPONSE" | jq -r '.current_condition[0].weatherCode')
TEMP=$(echo "$RESPONSE" | jq -r '.current_condition[0].temp_C')

# Day/night
SUNRISE_24=$(echo "$RESPONSE" | jq -r '.weather[0].astronomy[0].sunrise' | sed 's/ AM//' | sed 's/ PM//' | awk -F: '{h=$1;m=$2;if(index($0,"PM")>0&&h!=12)h+=12;if(index($0,"AM")>0&&h==12)h=0;printf "%02d:%02d",h,m}')
SUNSET_24=$(echo "$RESPONSE" | jq -r '.weather[0].astronomy[0].sunset' | sed 's/ AM//' | sed 's/ PM//' | awk -F: '{h=$1;m=$2;if(index($0,"PM")>0&&h!=12)h+=12;if(index($0,"AM")>0&&h==12)h=0;printf "%02d:%02d",h,m}')
NOW=$(date +%H:%M)
[ "$NOW" \> "$SUNRISE_24" ] && [ "$NOW" \< "$SUNSET_24" ] && IS_DAY=1 || IS_DAY=0

# Weather Icons (from erikflowers/weather-icons)
IC_SUN=$'\uf00d'        # day-sunny
IC_MOON=$'\uf02e'       # night-clear
IC_PARTLY_DAY=$'\uf002' # day-cloudy
IC_PARTLY_NIGHT=$'\uf083' # night-partly-cloudy
IC_CLOUD=$'\uf013'      # cloudy
IC_FOG=$'\uf014'        # fog
IC_RAIN_DAY=$'\uf008'   # day-rain
IC_RAIN=$'\uf019'       # rain
IC_RAIN_NIGHT=$'\uf036' # night-rain
IC_DRIZZLE_DAY=$'\uf009' # day-showers
IC_DRIZZLE=$'\uf01a'    # showers
IC_DRIZZLE_NIGHT=$'\uf037' # night-showers
IC_SNOW=$'\uf01b'       # snow
IC_THUNDER=$'\uf010'    # day-thunderstorm
IC_THUNDER_N=$'\uf03b'  # night-thunderstorm
IC_SLEET=$'\uf0b2'      # day-sleet
IC_HAIL=$'\uf004'       # day-hail
IC_ERROR=$'\uf06a'      # (error icon from original script)

# Wind beaufort icons
W0=$'\uf0b7'; W1=$'\uf0b8'; W2=$'\uf0b9'; W3=$'\uf0ba'; W4=$'\uf0bb'
W5=$'\uf0bc'; W6=$'\uf0bd'; W7=$'\uf0be'; W8=$'\uf0bf'; W9=$'\uf0c0'
W10=$'\uf0c1'; W11=$'\uf0c2'; W12=$'\uf0c3'

# Icon selection based on weather code
if [ $WID -eq 113 ]; then
    [ "$IS_DAY" = "1" ] && { ICON="$IC_SUN"; ICON_COLOR=$COLOR_SUN; } || { ICON="$IC_MOON"; ICON_COLOR=$COLOR_MOON; }
elif [ $WID -eq 116 ]; then
    [ "$IS_DAY" = "1" ] && { ICON="$IC_PARTLY_DAY"; ICON_COLOR=$COLOR_SUN; } || { ICON="$IC_PARTLY_NIGHT"; ICON_COLOR=$COLOR_MOON; }
elif [ $WID -eq 119 ] || [ $WID -eq 122 ]; then
    ICON="$IC_CLOUD"; ICON_COLOR=$COLOR_CLOUD
elif [ $WID -eq 248 ] || [ $WID -eq 260 ] || [ $WID -eq 143 ]; then
    ICON="$IC_FOG"; ICON_COLOR=$COLOR_FOG
elif [ $WID -ge 176 ] && [ $WID -le 266 ]; then
    [ "$IS_DAY" = "1" ] && { ICON="$IC_DRIZZLE_DAY"; ICON_COLOR=$COLOR_LIGHT_RAIN; } || { ICON="$IC_DRIZZLE_NIGHT"; ICON_COLOR=$COLOR_LIGHT_RAIN; }
elif [ $WID -ge 293 ] && [ $WID -le 314 ]; then
    [ "$IS_DAY" = "1" ] && { ICON="$IC_RAIN_DAY"; ICON_COLOR=$COLOR_HEAVY_RAIN; } || { ICON="$IC_RAIN_NIGHT"; ICON_COLOR=$COLOR_HEAVY_RAIN; }
elif [ $WID -ge 317 ] && [ $WID -le 320 ]; then
    ICON="$IC_SLEET"; ICON_COLOR=$COLOR_HEAVY_RAIN
elif [ $WID -ge 323 ] && [ $WID -le 338 ] || [ $WID -eq 350 ]; then
    ICON="$IC_SNOW"; ICON_COLOR=$COLOR_SNOW
elif [ $WID -ge 353 ] && [ $WID -le 359 ]; then
    [ "$IS_DAY" = "1" ] && { ICON="$IC_RAIN_DAY"; ICON_COLOR=$COLOR_HEAVY_RAIN; } || { ICON="$IC_RAIN_NIGHT"; ICON_COLOR=$COLOR_HEAVY_RAIN; }
elif [ $WID -ge 362 ] && [ $WID -le 377 ]; then
    ICON="$IC_SNOW"; ICON_COLOR=$COLOR_SNOW
elif [ $WID -ge 386 ] && [ $WID -le 395 ] || [ $WID -eq 200 ]; then
    [ "$IS_DAY" = "1" ] && { ICON="$IC_THUNDER"; ICON_COLOR=$COLOR_THUNDER; } || { ICON="$IC_THUNDER_N"; ICON_COLOR=$COLOR_THUNDER; }
else
    ICON="$IC_ERROR"; ICON_COLOR=$COLOR_ERR
fi

# Wind
WINDFORCE=$(echo "$RESPONSE" | jq -r '.current_condition[0].windspeedKmph')
WIND_KMH=$WINDFORCE
[ "$KNOTS" = "yes" ] && WINDFORCE=$(awk "BEGIN {printf \"%.${DECIMALS}f\", $WINDFORCE * 0.539957}")

# Beaufort icon
[ "$WIND_KMH" -le 1 ] 2>/dev/null && WI=$W0
[ "$WIND_KMH" -gt 1 ] && [ "$WIND_KMH" -le 5 ] 2>/dev/null && WI=$W1
[ "$WIND_KMH" -gt 5 ] && [ "$WIND_KMH" -le 11 ] 2>/dev/null && WI=$W2
[ "$WIND_KMH" -gt 11 ] && [ "$WIND_KMH" -le 19 ] 2>/dev/null && WI=$W3
[ "$WIND_KMH" -gt 19 ] && [ "$WIND_KMH" -le 28 ] 2>/dev/null && WI=$W4
[ "$WIND_KMH" -gt 28 ] && [ "$WIND_KMH" -le 38 ] 2>/dev/null && WI=$W5
[ "$WIND_KMH" -gt 38 ] && [ "$WIND_KMH" -le 49 ] 2>/dev/null && WI=$W6
[ "$WIND_KMH" -gt 49 ] && [ "$WIND_KMH" -le 61 ] 2>/dev/null && WI=$W7
[ "$WIND_KMH" -gt 61 ] && [ "$WIND_KMH" -le 74 ] 2>/dev/null && WI=$W8
[ "$WIND_KMH" -gt 74 ] && [ "$WIND_KMH" -le 88 ] 2>/dev/null && WI=$W9
[ "$WIND_KMH" -gt 88 ] && [ "$WIND_KMH" -le 102 ] 2>/dev/null && WI=$W10
[ "$WIND_KMH" -gt 102 ] && [ "$WIND_KMH" -le 117 ] 2>/dev/null && WI=$W11
[ "$WIND_KMH" -gt 117 ] 2>/dev/null && WI=$W12

WIND=""
if [ "$DISPLAY_WIND" = "yes" ] && [ "$WIND_KMH" -ge "$MIN_WIND" ] 2>/dev/null; then
    WIND="%{T$WEATHER_FONT_CODE}%{F$COLOR_WIND}$WI%{F-}%{T-}"
    [ "$DISPLAY_FORCE" = "yes" ] && WIND="$WIND $CTB$WINDFORCE$CTE"
    [ "$DISPLAY_WIND_UNIT" = "yes" ] && WIND="$WIND ${CTB}km/h$CTE"
    WIND="$WIND |"
fi

# Temperature with celsius
TI=$'\uf2c8'
CELSIUS="°C"
TEMP_INT=${TEMP%%.*}
if [ "$TEMP_INT" -le "$COLD_TEMP" ] 2>/dev/null; then
    TEMP_OUT="%{F$COLOR_COLD}%{T1}$TI%{T-}%{F-} $CTB${TEMP_INT}${CELSIUS}$CTE"
elif [ "$TEMP_INT" -ge "$HOT_TEMP" ] 2>/dev/null; then
    TEMP_OUT="%{F$COLOR_HOT}%{T1}$TI%{T-}%{F-} $CTB${TEMP_INT}${CELSIUS}$CTE"
else
    TEMP_OUT="%{F$COLOR_NORMAL_TEMP}%{T1}$TI%{T-}%{F-} $CTB${TEMP_INT}${CELSIUS}$CTE"
fi

# Description
[ "$DISPLAY_LABEL" = "yes" ] && DESC=$(echo "$RESPONSE" | jq -r '.current_condition[0].lang_it[0].value' | sed 's/^ *//;s/ *$//' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)}1')" " || DESC=""

echo "$WIND %{T$WEATHER_FONT_CODE}%{F$ICON_COLOR}$ICON%{F-}%{T-} $CTB$DESC$CTE| $TEMP_OUT"
