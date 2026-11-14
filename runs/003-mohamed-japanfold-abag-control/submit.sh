#!/usr/bin/env bash
# Submit the three-target opendde-abag job and follow it to a terminal state.
#
#   ./submit.sh            submit, then poll until done
#   ./submit.sh poll       just follow the job already recorded in job_id
#
# Needs JAPANFOLD_API_KEY in the environment. The key is never printed.
set -euo pipefail
cd "$(dirname "$0")"

[ -n "${JAPANFOLD_API_KEY:-}" ] || {
  echo "JAPANFOLD_API_KEY is not set. Get one at japanfold.aiand.com/account/token," >&2
  echo "add it to ~/.bashrc, then open a new shell." >&2
  exit 1
}

BASE=${JAPANFOLD_BASE_URL:-https://api.japanfold.aiand.com}
H=(-H 'X-JapanFold-Client: skill' -H "Authorization: Bearer $JAPANFOLD_API_KEY")

if [ "${1:-}" != "poll" ]; then
  # An idempotency key means a timed-out submit can be resent without paying twice.
  [ -f idempotency_key ] || python3 -c 'import uuid; print(uuid.uuid4())' > idempotency_key
  IDEM=$(cat idempotency_key)

  curl -s "${H[@]}" -X POST "$BASE/v1/predictions" \
    -H 'Content-Type: application/json' \
    -H "Idempotency-Key: $IDEM" \
    --data @request.json > submit_response.json

  python3 - <<'PY' > job_id
import json, sys
r = json.load(open("submit_response.json"))
if "id" not in r:
    sys.exit("submit failed: %s" % r.get("detail", r))
print(r["id"])
PY
  echo "job $(cat job_id) submitted"
fi

JOB=$(cat job_id)
: "${JOB:?no job id}"

# ?wait=60 holds the GET until the job ends or 60 s pass, so loop with no sleep.
while :; do
  curl -s "${H[@]}" "$BASE/v1/jobs/$JOB?wait=60" > job.json
  S=$(python3 -c 'import json;print(json.load(open("job.json")).get("status"))')
  Q=$(python3 -c '
import json
q = json.load(open("job.json")).get("queue") or {}
print("queued behind %s account(s): %s" % (q.get("accounts_ahead"), q.get("reason")) if q else "")
')
  echo "$(date +%H:%M:%S)  $S  $Q"
  case "$S" in queued | running) ;; *) break ;; esac
done

if [ "$S" = succeeded ]; then
  curl -s "${H[@]}" "$BASE/v1/jobs/$JOB/results" > results.json
  curl -fsLOJ "${H[@]}" "$BASE/v1/jobs/$JOB/archive"
  echo "results.json and the archive are in $(pwd)"
else
  echo "job ended $S; see job.json" >&2
  exit 1
fi
