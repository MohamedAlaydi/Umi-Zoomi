#!/bin/bash
# Boltz-2 refold for run 009, behind the team GPU lock.
#
#   run_multiseed.sh <queries-basename> <output-subdir> <seeds-csv>
#
# e.g. run_multiseed.sh queries_cand.json boltz2-cand-s1to5 1,2,3,4,5
#
# Container and every flag are copied from run 006 (people/anas/run_refold.sh +
# runs/006-anas-enumerated-top40/out/boltz2/config.json): IMG_BOLTZ2,
# apheris_boltz.cli predict, --num-diffusion-samples 1, --write-detailed-scores
# true, --query-failures skip, recycling_steps 3, sampling_steps 200 (defaults),
# --template-paths the run-006 template. Only --seeds and the query file change.
#
# Runs in the foreground so the caller gets the exit code and the wall time.
set -euo pipefail

QFILE=${1:?usage: run_multiseed.sh <queries-basename> <output-subdir> <seeds-csv>}
OUTSUB=${2:?missing output subdir}
SEEDS=${3:?missing seeds}
WHO=${4:-claude}

. "$HOME/team14/scripts/env.sh" >/dev/null
DOCS="$HOME/team14/data/rfd4-proteina/docs"
REL="runs/009-claude-multiseed-refold"
RUN="$HOME/team14/runs/009-claude-multiseed-refold"
LOG="$RUN/run-$OUTSUB.log"

[ -f "$DOCS/$REL/prepared/holo/$QFILE" ] || { echo "no $QFILE"; exit 1; }

SEEDARGS=()
IFS=',' read -ra S <<< "$SEEDS"
for s in "${S[@]}"; do SEEDARGS+=(--seeds "$s"); done

NQ=$(python3 -c "import json;print(len(json.load(open('$DOCS/$REL/prepared/holo/$QFILE'))['queries']))")
echo "$OUTSUB: $NQ queries x ${#S[@]} seeds = $(( NQ * ${#S[@]} )) folds" | tee "$LOG"
date '+start %Y-%m-%dT%H:%M:%S%z' | tee -a "$LOG"
T0=$(date +%s)

set +e
cd "$DOCS"
"$HOME/team14/scripts/gpurun" "$WHO" \
  docker run --rm --gpus all --shm-size 16g --user "$(id -u):$(id -g)" \
    -e HOME=/tmp -v /etc/passwd:/etc/passwd:ro -v "$PWD:/work" -w /work \
    "$IMG_BOLTZ2" python -m apheris_boltz.cli predict \
      --input "$REL/prepared/holo/$QFILE" \
      --output "$REL/$OUTSUB" \
      --template-paths "$REL/prepared/holo/template.cif" \
      --write-detailed-scores true --num-diffusion-samples 1 \
      "${SEEDARGS[@]}" --query-failures skip >> "$LOG" 2>&1
RC=$?
set -e

T1=$(date +%s)
echo "EXIT=$RC" >> "$LOG"
echo "WALL_SECONDS=$((T1 - T0))" >> "$LOG"
ln -sfn "$DOCS/$REL" "$RUN/out" 2>/dev/null || true
echo "$OUTSUB: EXIT=$RC wall $((T1 - T0))s for $(( NQ * ${#S[@]} )) folds"
exit $RC
