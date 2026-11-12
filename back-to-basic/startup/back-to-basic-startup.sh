#!/usr/bin/env bash
set -euo pipefail
CONFIG="$HOME/.config/conky/back-to-basic/back-to-basic.conf"
exec conky -c "$CONFIG"
