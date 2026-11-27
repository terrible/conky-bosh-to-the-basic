#!/usr/bin/env bash
# Legacy scalar interface. The panel calls the batched reader directly.
exec python3 -BEs "$(dirname -- "$0")/hardware_metrics.py" intel "${1:-load}"
