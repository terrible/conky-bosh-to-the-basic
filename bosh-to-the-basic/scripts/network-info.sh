#!/usr/bin/env bash
# shellcheck disable=SC2016 # Conky markup is intentionally emitted literally.
set -u

# Only the first default route is shown, matching the OPT-01 display.
# Conky markup below is intentionally literal, so printf templates use single quotes.
# shellcheck disable=SC2016
route_output=$(timeout 2s ip -o route show default 2>/dev/null || true)
read -r -a route <<< "$route_output"
iface=''
for ((i=0; i+1<${#route[@]}; i++)); do
    if [[ ${route[i]} == dev ]]; then
        iface=${route[i+1]}
        break
    fi
done

# Interface names are interpolated into markup consumed by execpi.
if [[ ! $iface =~ ^[a-zA-Z0-9_.:-]{1,15}$ ]]; then
    printf '${color2}${font NotoSans:bold:size=10}RED${color}\n'
    printf '${font NotoSans:size=9}Red desconectada\n'
    exit 0
fi

printf '${color2}${font NotoSans:bold:size=10}RED · %s${color}\n' "$iface"
printf '${font NotoSans:size=9}IP ${alignr}${addr %s}\n' "$iface"
printf '${font NotoSans:size=8}${lua_parse bosh_center_row title}\n'
printf '${font NotoSans:size=9}${lua_parse bosh_center_row speed %s}\n' "$iface"
printf '${template0 %s}\n' "$iface"
printf '${font NotoSans:size=8}${lua_parse bosh_center_row total %s}\n' "$iface"
