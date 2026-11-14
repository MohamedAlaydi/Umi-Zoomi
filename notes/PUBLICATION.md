# Published repository snapshot

This update publishes the team's source code, review notes, ranked candidate
exports, pitch deck, completed de novo campaign report, small configuration
and job receipts, and the score ledger. It does not submit sequences to the
organisers or assert that a proposed ranking has final acceptance.

Start with `notes/SCORES.md`. Its compact panel table links to the original
matched seed-42 raw scores. `notes/SCORES_FULL.md` and `notes/SCORES.csv`
contain all 2,168 recorded score rows. Each structural score cites a small
byte-preserved snapshot under its own run's `score-evidence/`, with hashes.
The check command works without the VM's absolute output symlinks:

```bash
python3 scripts/scores.py --check
python3 -m unittest discover -s scripts -p 'test_scores.py'
```

`review/denovo/report/` is the portable offline campaign report, selected
structures and 135 checksummed files. Full provider archives, PAE tensors,
large per-token outputs and model weights stay outside Git. Their scope is
explained in `review/denovo/ARTIFACTS.md`. Credential files, virtual
environments and the participant access package are excluded.

`review/replay.py` reproduces the frozen optimisation review from 193 bundled
inputs on CPU. It requires the versions in `review/requirements.txt`. The
complete original campaign audit in `review/denovo/verify_campaign.py`
additionally needs the original model outputs and organiser datasets.

`runs/012-codex-18plus2/` is an ongoing later comparison. Its manifests,
candidate exports and job-status receipts are a work-in-progress snapshot;
its presence does not replace the ranked proposal or confirm a new result.
Likewise, the older JapanFold prompt is preserved as a dated handoff, not
an instruction to resubmit already completed jobs.

The prepublication checks covered source/provenance consistency, isolated
score verification, immutable report checksums, 4 score regression tests,
7 optimisation regression tests, 8 de novo regression tests, the original
campaign audit and the local pre-commit checks. The staged tree was also
scanned for configured credentials and common secret formats, including
archive members, without displaying secret values.
