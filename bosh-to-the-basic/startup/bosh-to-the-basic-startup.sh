#!/usr/bin/env bash
set -euo pipefail
theme=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
# Lock the installed theme inode across the delay and foreground Conky process.
exec 9<"$theme"
flock -n 9 || exit 0
sleep 8
exec conky -c "$theme/bosh-to-the-basic.conf"
