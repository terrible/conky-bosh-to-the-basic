#!/usr/bin/env bash
set -u

# shellcheck source=/etc/os-release
. /etc/os-release

name="${NAME:-Linux}"
version="${VERSION_ID:-}"

if [[ -n "$version" ]]; then
    printf '%s %s' "$name" "$version"
else
    printf '%s' "$name"
fi
