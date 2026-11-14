# 009 claude multiseed-refold

- when: 2026-11-14 12:14 - 13:30 (UTC)
- image: `quay.io/apheris/oslo-hackathon:apheris-boltz-v1.3.0-boltz2` (`$IMG_BOLTZ2` from
  `scripts/env.sh`), used strictly as a black-box inference/scoring executable
  (`python -m apheris_boltz.cli predict`). No training, no fine-tuning, no weight change.
- interpreter: `/home/hackathon/team14/.venv/bin/python` (Python 3.12.3, via `scripts/py`)
- seed: Boltz-2 refold seeds **1, 2, 3, 4, 5, 42** (candidates) and **42, 1, 2**
  (calibration). RFD4 generation seeds are irrelevant here: nothing was generated.
- why we ran it: step 2 (`runs/008-claude-first-pass`) established that every run
  001-006 was folded at Boltz-2 seed 42 only, so the seed-to-seed noise of
  `iface_min` was **unmeasured**, while the 8 PASS_STRICT designs beat the in-batch
  wild type by only +0.003..+0.014. This run measures that noise floor, and
  calibrates the structural metrics against **measured** SPR affinity, to decide how
  much weight they deserve as selection scorers.

## One common protocol

Everything folded here went through the same protocol, copied from run 006 so that
numbers are comparable to the existing shortlist:

| item | value |
| --- | --- |
| container | `$IMG_BOLTZ2` = `...:apheris-boltz-v1.3.0-boltz2` |
| entry point | `python -m apheris_boltz.cli predict` |
| template | run 006's `prepared/holo/template.cif`, copied verbatim (byte-identical to run 004's; sha256-16 `719541a9bd7fb1cd`) |
| chains | A = trastuzumab VL (fixed), B = `VH_PRE + CDRH3 + VH_POST` (120 aa), C and D = HER2 taken verbatim from run 004's `queries.json` - exactly `people/anas/build_refold.py`'s construction |
| flags | `--num-diffusion-samples 1 --write-detailed-scores true --query-failures skip`, recycling 3, sampling 200 (container defaults, as in run 006's `boltz2/config.json`) |
| what varies | only `--seeds` and the query file |

Because runs 001/004/005 used different templates, folding their loops here under the
run-006 template is what makes all 60 loops comparable for the first time. Runs 004 and
006 already shared a template; runs 001 and 005 did not.

## Commands

```
# query sets + calibration draw (CPU, no network)
scripts/py runs/009-claude-multiseed-refold/prep_queries.py

# GPU, always through scripts/gpurun (the team flock on /tmp/team14-gpu.lock);
# no other job was killed, pre-empted or touched.
bash runs/009-claude-multiseed-refold/run_multiseed.sh queries_timing.json   boltz2-timing      1          claude
bash runs/009-claude-multiseed-refold/run_multiseed.sh queries_cand42.json   boltz2-cand-s42    42         claude
bash runs/009-claude-multiseed-refold/run_multiseed.sh queries_cand.json     boltz2-cand-s1to5  1,2,3,4,5  claude
bash runs/009-claude-multiseed-refold/run_multiseed.sh queries_calib.json    boltz2-calib       42,1,2     claude

# analysis (CPU)
scripts/py scripts/multiseed_analysis.py
```

## Query sets

| set | file | queries | seeds | folds |
| --- | --- | --- | --- | --- |
| timing probe | `queries_timing.json` | 1 (`trastuzumab_wt`) | 1 | 1 |
| candidates, new seeds | `queries_cand.json` | 60 unique CDRH3 over the 66 structure-backed first-pass rows, wild type included | 1,2,3,4,5 | 300 |
| candidates, seed 42 | `queries_cand42.json` | 16 loops from runs 001/004/005 (seed 42 is new for them under this template) + 3 run-006 loops as a determinism check | 42 | 19 |
| calibration | `queries_calib.json` | 30 measured SPR sequences | 42,1,2 | 90 |

Seed 42 for the 44 run-006 loops was **reused** from run 006 rather than recomputed,
after verifying bit-level determinism (below). The timing probe doubles as a
batch-of-1 vs batch-of-60 determinism check at seed 1.

## Calibration set: how the 30 were drawn

Source: `data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv` - the HER2/trastuzumab
SPR table (768 rows, 190 with a quantified KD). `data/spr-supplementary` was inspected
and **not** used: it is the Champloo nanobody/antigen set, a different construct that
cannot be folded under this protocol. `provided_cdrh3.npz` and
`people/anas/feasible.py` were used only to confirm which CDRH3 pool the SPR loops
belong to.

Procedure, fixed before looking at any structure:

1. keep 10-mer CDRH3 only, so the folded construct is identical in length to every
   candidate. `vh_sequence` in that file is byte-equal to `VH_PRE + cdrh3 + VH_POST`
   for all 740 of them (checked), so the construct needs no change.
2. `WT_KD` = median of the 8 wild-type replicate rows = **0.1345 nM**; binder bar
   `2 x WT_KD` = **0.2690 nM**.
3. one row per unique CDRH3 (median KD when measured more than once); the wild-type
   CDRH3 itself is excluded - it is already in the candidate set and is the paired
   reference.
4. strata: **binder** = quantified and KD <= 2 x WT_KD (only 9 unique non-WT loops
   qualify, so the stratum is topped up to 10 with the next-best measured KD, the
   brief's "or the best available"; effective bar 0.282 nM); **intermediate** =
   quantified, 2 x WT_KD < KD < 100 nM (90 available); **weak/non-binder** = 5 drawn
   from quantified KD >= 100 nM (79 available) + 5 drawn from
   `binding_result == no_reportable_kd` (441 available).
5. draw: `numpy.random.default_rng(20261114).choice`, without replacement, from each
   stratum sorted lexicographically by CDRH3, so the draw is reproducible regardless
   of file row order.

Result: 30 sequences, 25 with a quantified KD spanning 0.023 - 13,863 nM, 10 labelled
binder and 10 labelled non-binder. Overlap with the candidate CDRH3 set: **0**.

## Pre-registered labels (fixed before the folds were read)

- `PASS_ROBUST` = all other first-pass gates pass (novelty margin, no Cys,
  liabilities 2/2, grip 4/4, `p_high >= 0.95`) **and** one-sided 95 % lower bound of
  the mean WT-paired `iface_min` delta >= 0 **and** BH q <= 0.10
- `NONINFERIOR` = other gates pass **and** one-sided 95 % upper bound >= -0.03
  **and** not `PASS_ROBUST`
- `FAIL_ROBUST` = upper bound < 0
- anything else = `INDETERMINATE`

Labels are assigned in that order. The `NONINFERIOR` and `FAIL_ROBUST` definitions
overlap for -0.03 <= upper < 0; the count affected is reported in
`multiseed_summary.md` rather than resolved by changing the rule.

## Outputs

| file | what |
| --- | --- |
| `multiseed_metrics.csv` | one row per (sequence, seed): scores + geometry |
| `multiseed_summary.csv` | one row per sequence: mean/SD/min/max across seeds, WT-paired delta, bounds, p, q, v2 label |
| `first_pass_candidates_v2.csv` | step 2's 5066-row table **copied** with `v2_*` columns added (step 2's own file is untouched) |
| `calibration.csv` | the 30 measured sequences, seed-mean metrics, KD, strata |
| `multiseed_summary.md` | the full numeric report |
| `analysis_stats.json` | machine-readable variance components, noise floor, labels, calibration |
| `geometry_cache.json` | per-structure geometry, keyed by CIF path (lets the analysis re-run in seconds) |
| `run-*.log` | one Boltz-2 log per job, each ending in `EXIT=` and `WALL_SECONDS=` |

Structures stay on disk under
`data/rfd4-proteina/docs/runs/009-claude-multiseed-refold/boltz2-*/` (reachable as
`runs/009-claude-multiseed-refold/out/`), gitignored like every other run's output.

## Budget

One fold was timed before committing: 51 s wall for a single query including container
start and weight load, of which ~16 s was the fold itself; the 19-fold job then gave
the steady-state marginal rate. Projection and actuals are in the results section
below. Nothing was cut.

## Scope

New files only. Nothing outside this run directory and `scripts/multiseed_analysis.py`
was created or modified; no `git add`, no commit. No network, no hosted service.

## What came out

See `multiseed_summary.md` for the full tables; the headline numbers and the decision
are in the "Results" section appended below.
