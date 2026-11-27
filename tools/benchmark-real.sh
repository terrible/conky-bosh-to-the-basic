#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
smoke=0
if [[ ${1:-} == --smoke-test ]]; then smoke=1; shift; fi
if [[ $# -ne 3 ]]; then echo "Usage: $0 [--smoke-test] OPT01_THEME CANDIDATE_THEME OUTPUT.csv" >&2; exit 2; fi
for tool in systemd-run systemctl nvidia-smi conky Xvfb python3 realpath rg flock xauth xdpyinfo seq; do
    command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 2; }
done
repo=$(realpath -e -- "$(dirname -- "$0")/..")
exec {benchmark_lock}<"$repo/tools/benchmark-real.sh"
flock -n "$benchmark_lock" || { echo "Another real benchmark is running from this checkout" >&2; exit 2; }
systemctl --user show-environment >/dev/null
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
[[ ! -L $1 && ! -L $2 ]] || { echo "Theme root must not be a symlink" >&2; exit 2; }
reference=$(realpath -e -- "$1")
candidate=$(realpath -e -- "$2")
output_parent=$(realpath -e -- "$(dirname -- "$3")")
output="$output_parent/$(basename -- "$3")"
summary="$output.json"
[[ -d $reference && -d $candidate && $reference != "$candidate" ]] || { echo "Invalid theme inputs" >&2; exit 2; }
[[ -f $reference/bosh-to-the-basic.conf && -f $candidate/bosh-to-the-basic.conf ]] || { echo "Theme config missing" >&2; exit 2; }
python3 - "$repo" "$reference" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from tools.qa_runtime import verify_opt01_reference
try:
    verify_opt01_reference(sys.argv[2])
except (OSError, ValueError) as error:
    raise SystemExit(f"OPT-01 reference is not the audited source: {error}")
PY
case "$output" in "$reference"/*|"$candidate"/*) echo "Output must be outside themes" >&2; exit 2;; esac
[[ ! -e $output && ! -L $output && ! -e $summary && ! -L $summary && ! -e $output.logs && ! -L $output.logs ]] || { echo "Output/evidence paths must be new" >&2; exit 2; }
python3 - "$reference" "$candidate" <<'PY'
from pathlib import Path
import sys
for root in map(Path, sys.argv[1:]):
    if root.is_symlink() or any(path.is_symlink() for path in root.rglob("*")):
        raise SystemExit(f"Refusing symlink in benchmark input: {root}")
PY
mkdir -m 700 -- "$output.logs"
work=''
unit=''
xvfb_pid=''
cleanup() {
    local status=$?
    trap - EXIT INT TERM
    if [[ -n $unit ]]; then systemctl --user stop "$unit.scope" >/dev/null 2>&1 || :; fi
    if [[ -n $xvfb_pid ]] && kill -0 "$xvfb_pid" 2>/dev/null; then kill "$xvfb_pid" 2>/dev/null || :; fi
    if [[ -n $xvfb_pid ]]; then wait "$xvfb_pid" 2>/dev/null || :; fi
    if [[ -n $work && -d $work && ! -L $work ]]; then rm -rf -- "$work"; fi
    exit "$status"
}
work=$(mktemp -d "${TMPDIR:-/tmp}/bosh-bench.XXXXXXXX")
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
mkdir -m 700 "$work/home" "$work/bin" "$work/config-opt01" "$work/config-candidate" "$work/runtime"
chmod 700 "$work/runtime"
touch "$work/Xauthority"
chmod 600 "$work/Xauthority"
cookie=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
cp -R -- "$reference/." "$work/config-opt01/"
cp -R -- "$candidate/." "$work/config-candidate/"
real_nvidia=$(command -v nvidia-smi)
cat >"$work/bin/nvidia-smi" <<'SHIM'
#!/usr/bin/python3
import json
import os
import subprocess
import time
import uuid
started = os.times()
call_id = uuid.uuid4().hex
start_ns = time.monotonic_ns()
with open(os.environ["NVIDIA_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({"event": "start", "id": call_id, "monotonic_ns": start_ns}) + "\n")
    log.flush()
try:
    result = subprocess.run([os.environ["NVIDIA_REAL"], *os.sys.argv[1:]])
    return_code = result.returncode
except OSError as error:
    print(f"nvidia-smi wrapper failed: {error}", file=os.sys.stderr)
    return_code = 127
finished = os.times()
wrapper_cpu = (finished.user + finished.system) - (started.user + started.system)
with open(os.environ["NVIDIA_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({"event": "end", "id": call_id,
                          "monotonic_ns": time.monotonic_ns(),
                          "wrapper_cpu_seconds": wrapper_cpu,
                          "return_code": return_code}) + "\n")
    log.flush()
raise SystemExit(return_code)
SHIM
chmod 700 "$work/bin/nvidia-smi"

for label in opt01 candidate; do
    if [[ $label == opt01 ]]; then theme="$work/config-opt01"; source_theme=$reference; else theme="$work/config-candidate"; source_theme=$candidate; fi
    python3 - "$repo" "$theme" "$source_theme" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from pathlib import Path
from tools.qa_runtime import relocate_config
theme, source = Path(sys.argv[2]), Path(sys.argv[3]).resolve()
config = theme / "bosh-to-the-basic.conf"
text = relocate_config(config.read_text(), source, theme)
config.write_text(text)
if str(source) in config.read_text():
    raise SystemExit("copied executable config references source theme")
PY
    python3 "$repo/installer/conky_backend.py" "$theme/bosh-to-the-basic.conf" "$theme/bosh-to-the-basic.conf" --conky "$(command -v conky)" --xinerama-head 0 >"$output.logs/$label.backend.txt"
    python3 - "$repo" "$theme/bosh-to-the-basic.conf" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from pathlib import Path
from tools.qa_runtime import assert_no_production_reference
try:
    assert_no_production_reference(Path(sys.argv[2]).read_text())
except ValueError as error:
    raise SystemExit(str(error))
PY
done

# Private-cookie X11 display. No TCP listener; never inherit the desktop's Wayland session.
display_number=''
for _ in {1..20}; do
    candidate_display=$(python3 -c 'import secrets; print(secrets.randbelow(20000) + 100)')
    xauth -f "$work/Xauthority" add ":$candidate_display" . "$cookie"
    env -u WAYLAND_DISPLAY -u WAYLAND_SOCKET -u DBUS_SESSION_BUS_ADDRESS \
        Xvfb ":$candidate_display" -auth "$work/Xauthority" -screen 0 1024x768x24 -dpi 96 -nolisten tcp >"$output.logs/xvfb.log" 2>&1 &
    xvfb_pid=$!
    for _ in {1..50}; do
        if DISPLAY=":$candidate_display" XAUTHORITY="$work/Xauthority" xdpyinfo >/dev/null 2>&1; then display_number=$candidate_display; break; fi
        kill -0 "$xvfb_pid" 2>/dev/null || break
        sleep .1
    done
    [[ -n $display_number ]] && break
    wait "$xvfb_pid" 2>/dev/null || :
    xvfb_pid=''
    xauth -f "$work/Xauthority" remove ":$candidate_display" >/dev/null 2>&1 || :
done
[[ -n $display_number ]] || { echo "Xvfb failed; log retained at $output.logs/xvfb.log" >&2; exit 1; }
home="$work/home"
xdg_config="$home/.config"; xdg_data="$home/.local/share"
xdg_cache="$home/.cache"; xdg_state="$home/.local/state"
mkdir -p "$xdg_config" "$xdg_data" "$xdg_cache" "$xdg_state"
display=":$display_number"; authority="$work/Xauthority"
results="$work/results.csv"
printf 'variant,sample,elapsed_seconds,cgroup_cpu_seconds,cpu_one_core_percent,panel_cpu_seconds,worker_cpu_seconds,nvidia_wrapper_cpu_seconds,panel_rss_peak_bytes,worker_rss_peak_bytes,nvidia_queries,nvidia_failed_queries,nvidia_queries_per_minute,window_id,window_dimensions,log\n' >"$results"
# Reject absolute nvidia-smi calls that would bypass the counting wrapper.
set +e
rg -n --glob '*.py' --glob '*.sh' --glob '*.lua' '(/usr)?/bin/nvidia-smi' "$reference" "$candidate"
scan_status=$?
set -e
if (( scan_status == 0 )); then echo "Absolute nvidia-smi path bypasses query counter" >&2; exit 1
elif (( scan_status > 1 )); then echo "Could not audit NVIDIA query paths" >&2; exit "$scan_status"; fi

warm_seconds=30; measure_seconds=60; sample_count=3
if (( smoke )); then warm_seconds=3; measure_seconds=5; sample_count=1; fi
test_path="$work/bin:/usr/bin:/bin"
run_sample() {
    local variant=$1 config=$2 sample=$3
    unit="bosh-bench-$$-$RANDOM-$RANDOM"
    local log="$output.logs/$variant-$sample.log"
    # systemd-run itself inherits the real manager connection environment. Test-only GUI/XDG
    # variables are set only in the process launched inside the transient scope.
    systemd-run --user --scope --quiet --unit="$unit" \
        /usr/bin/env -u WAYLAND_DISPLAY -u WAYLAND_SOCKET -u XDG_SESSION_TYPE -u DBUS_SESSION_BUS_ADDRESS \
        "HOME=$home" "XDG_CONFIG_HOME=$xdg_config" "XDG_DATA_HOME=$xdg_data" \
        "XDG_CACHE_HOME=$xdg_cache" "XDG_STATE_HOME=$xdg_state" "XDG_RUNTIME_DIR=$work/runtime" \
        "XAUTHORITY=$authority" "DISPLAY=$display" "PATH=$test_path" \
        "BOSH_QA_ISOLATED_X11=1" \
        "NVIDIA_REAL=$real_nvidia" "NVIDIA_LOG=$work/nvidia.log" \
        /usr/bin/python3 "$repo/tools/benchmark_worker.py" \
        --config "$config" --warmup "$warm_seconds" --measure "$measure_seconds" \
        --log "$log" --nvidia-log "$work/nvidia.log" --csv "$results" \
        --variant "$variant" --sample "$sample" --unit-name "$unit" \
        --x11-window-checker "$repo/tools/x11_window.py"
    systemctl --user stop "$unit.scope" >/dev/null 2>&1 || :
    unit=''
}
for sample in $(seq 1 "$sample_count"); do
    if (( sample % 2 )); then order=(OPT01 candidate); else order=(candidate OPT01); fi
    for variant in "${order[@]}"; do
        if [[ $variant == OPT01 ]]; then config="$work/config-opt01/bosh-to-the-basic.conf"; else config="$work/config-candidate/bosh-to-the-basic.conf"; fi
        run_sample "$variant" "$config" "$sample"
    done
done
python3 - "$results" "$output" "$summary" "$sample_count" "$warm_seconds" "$measure_seconds" <<'PY'
import csv, json, statistics, sys
rows=list(csv.DictReader(open(sys.argv[1], newline="")))
expected=int(sys.argv[4]); warm=float(sys.argv[5]); measure=float(sys.argv[6])
report={"method":f"systemd user scope; same foreground Conky instance; {warm}s warmup then {measure}s monotonic measurement; NVIDIA calls and wrapper CPU filtered by measurement timestamps", "cpu_unit":"percent of one logical core", "variants":{}}
for name in ("OPT01", "candidate"):
    values=[r for r in rows if r["variant"]==name]
    if len(values)!=expected: raise SystemExit(f"Expected {expected} valid samples for {name}, got {len(values)}")
    fields=("cpu_one_core_percent", "panel_cpu_seconds", "worker_cpu_seconds", "nvidia_wrapper_cpu_seconds", "panel_rss_peak_bytes", "worker_rss_peak_bytes", "nvidia_queries", "nvidia_failed_queries", "nvidia_queries_per_minute")
    report["variants"][name]={}
    for field in fields:
        numbers=[float(r[field]) for r in values]
        report["variants"][name][field]={"median":statistics.median(numbers), "stdev":statistics.stdev(numbers) if len(numbers)>1 else 0.0}
with open(sys.argv[3], "x", encoding="utf-8") as stream:
    json.dump(report, stream, indent=2); stream.write("\n")
with open(sys.argv[2], "x", encoding="utf-8") as stream:
    writer=csv.DictWriter(stream, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
print(json.dumps(report, indent=2))
PY
printf 'Benchmark CSV: %s\nSummary JSON: %s\nLogs: %s\n' "$output" "$summary" "$output.logs"
