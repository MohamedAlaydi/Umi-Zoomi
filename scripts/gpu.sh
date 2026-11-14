#!/bin/bash
# Who is on the GPU right now?
echo "--- GPU ---"
nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu \
  --format=csv,noheader
echo "--- processes on the GPU ---"
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader \
  | while IFS=, read -r pid mem; do
      pid=$(echo "$pid" | tr -d ' ')
      [ -n "$pid" ] && printf '%s  %s  %s\n' "$pid" "$mem" \
        "$(ps -o cmd= -p "$pid" 2>/dev/null | cut -c1-90)"
    done
echo "--- lock ---"
if [ -f /tmp/team14-gpu.owner ]; then
  cat /tmp/team14-gpu.owner
else
  echo "free"
fi
echo "--- docker containers ---"
docker ps --format '{{.Names}}  {{.Image}}  {{.Status}}' 2>/dev/null | head
