#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
if [[ $# != 3 ]]; then echo "Usage: $0 OPT01_THEME CANDIDATE_THEME NEW_OUTPUT_DIR" >&2; exit 2; fi
for tool in Xvfb conky import compare identify realpath python3 rg setsid xauth xdpyinfo; do
    command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 2; }
done
repo=$(realpath -e -- "$(dirname -- "$0")/..")
[[ ! -L $1 && ! -L $2 ]] || { echo "Theme root must not be a symlink" >&2; exit 2; }
reference=$(realpath -e -- "$1")
candidate=$(realpath -e -- "$2")
parent=$(realpath -e -- "$(dirname -- "$3")")
output="$parent/$(basename -- "$3")"
for source in "$reference" "$candidate"; do
    [[ -d $source && -f $source/bosh-to-the-basic.conf && ! -L $source ]] || { echo "Invalid theme input" >&2; exit 2; }
done
python3 - "$repo" "$reference" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from tools.qa_runtime import verify_opt01_reference
try:
    verify_opt01_reference(sys.argv[2])
except (OSError, ValueError) as error:
    raise SystemExit(f"OPT-01 reference is not the audited source: {error}")
PY
[[ $reference != "$candidate" ]] || { echo "Inputs must differ" >&2; exit 2; }
case "$output" in "$reference"/*|"$candidate"/*) echo "Output must be outside theme sources" >&2; exit 2;; esac
[[ ! -e $output && ! -L $output ]] || { echo "Output directory already exists" >&2; exit 2; }
mkdir -m 700 -- "$output"

# Reject symlinks before copying themes into the isolated display environment.
python3 - "$reference" "$candidate" <<'PY'
from pathlib import Path
import sys
for root in map(Path, sys.argv[1:]):
    if root.is_symlink() or any(path.is_symlink() for path in root.rglob("*")):
        raise SystemExit(f"Refusing symlink in visual input: {root}")
PY
work=''
xvfb_pid=''
conky_pid=''
window_id=''
cleanup() {
    local status=$?
    trap - EXIT INT TERM
    if [[ -n $conky_pid ]]; then stop_conky; fi
    if [[ -n $xvfb_pid ]] && kill -0 "$xvfb_pid" 2>/dev/null; then kill "$xvfb_pid" 2>/dev/null || :; fi
    if [[ -n $xvfb_pid ]]; then wait "$xvfb_pid" 2>/dev/null || :; fi
    [[ -z $work || ! -d $work || -L $work ]] || rm -rf -- "$work"
    exit "$status"
}
stop_conky() {
    kill -TERM -- "-$conky_pid" 2>/dev/null || :
    for _ in {1..20}; do
        kill -0 -- "-$conky_pid" 2>/dev/null || break
        sleep .1
    done
    kill -KILL -- "-$conky_pid" 2>/dev/null || :
    wait "$conky_pid" 2>/dev/null || :
    conky_pid=''
    window_id=''
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
work=$(mktemp -d "${TMPDIR:-/tmp}/bosh-visual.XXXXXXXX")
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
mkdir -m 700 "$work/home" "$work/bin" "$work/opt01" "$work/candidate" "$work/runtime"
chmod 700 "$work/runtime"
touch "$work/Xauthority"
chmod 600 "$work/Xauthority"
cookie=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
cat >"$work/bin/ip" <<'IP'
#!/usr/bin/env bash
printf '%s\n' 'default via 192.0.2.1 dev enp0s3 proto static'
IP
chmod 700 "$work/bin/ip"
export PATH="$work/bin:/usr/bin:/bin" HOME="$work/home" LC_ALL=C.UTF-8
export XDG_CONFIG_HOME="$HOME/.config" XDG_DATA_HOME="$HOME/.local/share"
export XDG_CACHE_HOME="$HOME/.cache" XDG_STATE_HOME="$HOME/.local/state"
export XDG_RUNTIME_DIR="$work/runtime" XAUTHORITY="$work/Xauthority" BOSH_QA_ISOLATED_X11=1
mkdir -p "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$XDG_CACHE_HOME" "$XDG_STATE_HOME"
unset DISPLAY WAYLAND_DISPLAY WAYLAND_SOCKET XDG_SESSION_TYPE DBUS_SESSION_BUS_ADDRESS
display_number=''
for _ in {1..20}; do
    candidate_display=$(python3 -c 'import secrets; print(secrets.randbelow(20000) + 100)')
    xauth -f "$XAUTHORITY" add ":$candidate_display" . "$cookie"
    Xvfb ":$candidate_display" -auth "$XAUTHORITY" -screen 0 1024x1200x24 -dpi 96 -nolisten tcp >"$output/xvfb.log" 2>&1 &
    xvfb_pid=$!
    for _ in {1..50}; do
        if DISPLAY=":$candidate_display" XAUTHORITY="$XAUTHORITY" xdpyinfo >/dev/null 2>&1; then
            display_number=$candidate_display
            break
        fi
        kill -0 "$xvfb_pid" 2>/dev/null || break
        sleep .1
    done
    [[ -n $display_number ]] && break
    wait "$xvfb_pid" 2>/dev/null || :
    xvfb_pid=''
    xauth -f "$XAUTHORITY" remove ":$candidate_display" >/dev/null 2>&1 || :
done
[[ -n $display_number ]] || { echo "Could not start private Xvfb; see $output/xvfb.log" >&2; exit 1; }
DISPLAY=":$display_number"
export DISPLAY
printf 'DISPLAY=%s\nresolution=1024x1200x24\ndpi=96\nbackend=X11/Xvfb (not KDE Wayland validation)\ntransparency=limited without a compositor\n' "$DISPLAY" >"$output/environment.txt"

render() {
    local label=$1 source=$2 target="$work/$1" config="$work/$1/bosh-to-the-basic.conf"
    cp -R -- "$source/." "$target/"
    python3 "$repo/tools/visual_fixture.py" "$source" "$target" >"$output/$label.fixture.txt"
    python3 "$repo/installer/conky_backend.py" "$target/bosh-to-the-basic.conf" "$config" --conky "$(command -v conky)" --xinerama-head 0 >"$output/$label.backend.txt"
    python3 - "$repo" "$config" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from pathlib import Path
from tools.qa_runtime import assert_no_production_reference
try:
    assert_no_production_reference(Path(sys.argv[2]).read_text())
except ValueError as error:
    raise SystemExit(str(error))
PY
    local log="$output/$label.log" stdout="$output/$label.stdout" probe_log="$output/$label.window-probe.log"
    setsid conky -c "$config" >"$stdout" 2>"$log" &
    conky_pid=$!
    geometry=$(python3 "$repo/tools/x11_window.py" "$conky_pid" --log "$log" --timeout 6 2>"$probe_log") || geometry=''
    if ! kill -0 "$conky_pid" 2>/dev/null; then wait "$conky_pid" || { echo "Conky exited; see $log" >&2; return 1; }; fi
    if [[ -n $geometry ]]; then read -r window_id width height <<<"$geometry"; fi
    [[ -n $window_id ]] || { echo "No visible Conky window for PID $conky_pid; see $log" >&2; return 1; }
    sleep 2
    set +e
    rg -i '\[(error|fatal)\]|lua.*(error|failed)|unknown (?:setting|key)' "$log" "$stdout"
    local render_scan_status=$?
    set -e
    if (( render_scan_status == 0 )); then
        echo "Conky/Lua render error for $label; see logs" >&2; return 1
    elif (( render_scan_status > 1 )); then
        echo "Unable to inspect Conky logs for $label" >&2; return "$render_scan_status"
    fi
    [[ $width =~ ^[0-9]+$ && $height =~ ^[0-9]+$ && $width -gt 0 && $height -gt 0 ]] || { echo "Invalid Conky window dimensions" >&2; return 1; }
    import -display "$DISPLAY" -window "$window_id" "$output/$label.png" 2>>"$log"
    [[ -s $output/$label.png ]] || { echo "Empty capture: $label" >&2; return 1; }
    local captured
    captured=$(identify -format '%wx%h' "$output/$label.png")
    [[ $captured == "${width}x${height}" ]] || { echo "Capture/window dimensions differ: $captured vs ${width}x${height}" >&2; return 1; }
    printf 'window_id=%s\nwindow_pid=%s\nwindow_dimensions=%s\n' "$window_id" "$conky_pid" "$captured" >"$output/$label.window.txt"
    stop_conky
}
render opt01 "$reference"
render candidate "$candidate"
set +e
compare -metric AE "$output/opt01.png" "$output/candidate.png" "$output/difference.png" 2>"$output/compare-metric.txt"
compare_status=$?
set -e
printf 'compare_exit=%s (0 identical, 1 pixels differ; >1 error)\n' "$compare_status" >>"$output/compare-metric.txt"
if (( compare_status > 1 )); then echo "ImageMagick compare error: exit $compare_status; see $output/compare-metric.txt" >&2; exit "$compare_status"; fi
identify "$output/opt01.png" "$output/candidate.png" "$output/difference.png" >"$output/image-dimensions.txt"
printf 'Visual comparison completed: exit=%s; evidence=%s\n' "$compare_status" "$output"
