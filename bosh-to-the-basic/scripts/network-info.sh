#!/usr/bin/env bash
set -u

iface="$(ip -o route show default 2>/dev/null | awk '
NR==1 {
    for (i=1; i<=NF; i++) {
        if ($i == "dev") {
            print $(i+1)
            exit
        }
    }
}')"

if [[ -z "$iface" ]]; then
    printf '${color2}${font NotoSans:bold:size=10}RED${color}\n'
    printf '${font NotoSans:size=9}Red desconectada\n'
    exit 0
fi

printf '${color2}${font NotoSans:bold:size=10}RED · %s${color}\n' "$iface"
printf '${font NotoSans:size=9}IP ${alignr}${addr %s}\n' "$iface"
printf '${font NotoSans:size=9}DESCARGA ${alignr}${downspeed %s}\n' "$iface"
printf '${downspeedgraph %s 25,259 51a2da 51a2da}\n' "$iface"
printf '${font NotoSans:size=9}Total ${alignr}${totaldown %s}\n' "$iface"
