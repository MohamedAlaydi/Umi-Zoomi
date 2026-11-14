#!/bin/bash
# Refold one prepared queries.json with Boltz-2, behind the GPU lock, in tmux.
#
#   run_refold.sh <run-dir-name> [who]
#
# Same docker invocation as the organisers' Scripts/run-her2.sh predict step, but
# pointed at a prepared folder we built ourselves, so it works for candidates that
# did not come out of RFD4.
set -euo pipefail

RUNNAME=${1:?usage: run_refold.sh <run-dir-name> [who]}
WHO=${2:-anas}

. "$HOME/team14/scripts/env.sh" >/dev/null
DOCS="$HOME/team14/data/rfd4-proteina/docs"
RUN="$HOME/team14/runs/$RUNNAME"
REL="runs/$RUNNAME"
SESSION="d-$WHO"

[ -f "$DOCS/$REL/prepared/holo/queries.json" ] || { echo "no queries.json for $RUNNAME"; exit 1; }
NQ=$(python3 -c "import json;print(len(json.load(open('$DOCS/$REL/prepared/holo/queries.json'))['queries']))")

tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" \
  "cd '$DOCS' && '$HOME/team14/scripts/gpurun' '$WHO' \
     docker run --rm --gpus all --shm-size 16g --user \$(id -u):\$(id -g) \
       -e HOME=/tmp -v /etc/passwd:/etc/passwd:ro -v \"\$PWD:/work\" -w /work \
       '$IMG_BOLTZ2' python -m apheris_boltz.cli predict \
         --input '$REL/prepared/holo/queries.json' \
         --output '$REL/boltz2' \
         --template-paths '$REL/prepared/holo/template.cif' \
         --write-detailed-scores true --num-diffusion-samples 1 \
         --seeds 42 --query-failures skip > '$RUN/run.log' 2>&1; \
   echo EXIT=\$? >> '$RUN/run.log'; \
   ln -sfn '$DOCS/$REL' '$RUN/out' 2>/dev/null; \
   sleep 86400"

echo "started $RUNNAME: $NQ queries, Boltz-2, seed 42, 1 diffusion sample"
echo "  watch:    tail -f $RUN/run.log"
echo "  done?     grep EXIT $RUN/run.log"
echo "  session:  tmux attach -t $SESSION"
