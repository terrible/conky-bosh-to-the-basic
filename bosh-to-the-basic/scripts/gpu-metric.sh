#!/usr/bin/env bash
set -u
metric="${1:-temp}"

command -v nvidia-smi >/dev/null 2>&1 || { printf -- '--'; exit 0; }

case "$metric" in
  temp)
    nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>/dev/null | head -n1 | tr -d ' '
    ;;
  util)
    nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null | head -n1 | tr -d ' '
    ;;
  memory)
    nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null |
      awk -F, 'NR==1 {gsub(/ /,"",$1); gsub(/ /,"",$2); printf "%s / %s MiB",$1,$2}'
    ;;
  memory_percent)
    nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null |
      awk -F, 'NR==1 {gsub(/ /,"",$1); gsub(/ /,"",$2); if ($2>0) printf "%.0f", ($1/$2)*100; else print 0}'
    ;;
  *)
    printf -- '--'
    ;;
esac
