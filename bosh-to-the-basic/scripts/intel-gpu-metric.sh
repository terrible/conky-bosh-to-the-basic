#!/usr/bin/env bash
set -o pipefail

intel_gpu_top -J -s 1000 -n 2 2>/dev/null |
python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
    busy = float(data[-1]["engines"]["Render/3D"]["busy"])
    print(f"{busy:.0f}")
except Exception:
    print("--")
'
