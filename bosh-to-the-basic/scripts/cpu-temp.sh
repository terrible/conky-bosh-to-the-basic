#!/usr/bin/env bash
set -u

wanted="${1:-package}"
values=()

for hw in /sys/class/hwmon/hwmon*; do
    [[ -r "$hw/name" ]] || continue
    [[ "$(<"$hw/name")" == "coretemp" ]] || continue

    for input in "$hw"/temp*_input; do
        [[ -r "$input" ]] || continue
        label_file="${input%_input}_label"
        [[ -r "$label_file" ]] || continue

        label="$(<"$label_file")"

        if [[ "$wanted" == "package" && "$label" == "Package id 0" ]]; then
            awk '{printf "%.0f", $1/1000}' "$input"
            exit 0
        fi

        if [[ "$wanted" == "avg" && "$label" =~ ^Core\ [0-3]$ ]]; then
            values+=( "$(awk '{printf "%.0f", $1/1000}' "$input")" )
        fi
    done
done

if [[ "$wanted" == "avg" && ${#values[@]} -gt 0 ]]; then
    printf '%s\n' "${values[@]}" | awk '{sum+=$1; n++} END {printf "%.0f", sum/n}'
else
    printf '%s' '--'
fi
