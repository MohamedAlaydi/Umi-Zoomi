#!/usr/bin/env bash
set -euo pipefail
TEAM=/home/hackathon/team14
K=${1:?choose k=1 or k=2}
case "$K" in 1|2) ;; *) exit 2;; esac
date -u '+START_UTC=%Y-%m-%dT%H:%M:%SZ'
"$TEAM/scripts/gpurun" "codex-vhh-k$K" \
  docker run --rm --gpus all --shm-size 16g --user 1001:1001 \
  -e HOME=/tmp -v /etc/passwd:/etc/passwd:ro -v "$TEAM:/work" -w /work \
  quay.io/apheris/oslo-hackathon:apheris-rfd4-proteina-v0.3.0-antibody-2026-10-30 \
  module-run design --input "runs/011-codex-denovo-vhh/rfd4-variable-sequence-k$K/design.yaml" \
  --output "runs/011-codex-denovo-vhh/rfd4-variable-sequence-k$K/design" \
  --num-replicates 16 --batch-size 1 --seed 20261114 --sequence-tsr-k "$K" \
  --recycle-strategy high/front_loaded
date -u '+FINISH_UTC=%Y-%m-%dT%H:%M:%SZ'
echo EXIT=0
