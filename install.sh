#!/usr/bin/env bash
set -euo pipefail
exec python3 -I -B "$(dirname -- "${BASH_SOURCE[0]}")/installer/manage.py" install "$@"
