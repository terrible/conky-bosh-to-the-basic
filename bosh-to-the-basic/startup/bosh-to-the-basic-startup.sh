#!/usr/bin/env bash
set -euo pipefail
CONFIG="$HOME/.config/conky/bosh-to-the-basic/bosh-to-the-basic.conf"
exec conky -c "$CONFIG"
