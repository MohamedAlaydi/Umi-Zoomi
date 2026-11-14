#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH="$PWD/review/denovo/.venv/lib/python3.12/site-packages${PYTHONPATH:+:$PYTHONPATH}"
.venv/bin/python -m unittest discover -s review/denovo -p 'test_*.py' -v
.venv/bin/python review/denovo/verify_campaign.py
.venv/bin/python review/denovo/build_report.py --output "${1:?Pass output directory}"
