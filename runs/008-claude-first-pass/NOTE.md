# 008 claude first-pass

- when: 2026-11-14 12:00
- image: **none** — CPU only, no container, no GPU, no network
- command: `py scripts/first_pass.py --out-dir runs/008-claude-first-pass`
- interpreter: `/home/hackathon/team14/.venv/bin/python` (Python 3.12.3, == `scripts/py`)
- seed: n/a (deterministic analysis; the Boltz-2 refold seed of the runs it reads is **42** throughout)
- exit code: **0** (full run 69 s; smoke runs at `--legal-limit 50` and `500` also exit 0)

## why we ran it

Every candidate the project has produced so far sits in a different file with a
different column set, and the pass/fail reason `rank.py` computes is printed to
stdout and then discarded — `ranked-004.csv` and `ranked-005.csv` contain only the
*survivors*, so there is no table anywhere that says why anything failed. The
planner wanted one row per candidate across all sources, every gate evaluated by
the same code, with the group labels fixed in advance.

Analysis only. New files only: this directory plus `scripts/first_pass.py`. No
existing repo file was edited, nothing was committed or `git add`ed, no run
directory was written into, `collect_refold.py` was not run, the GPU was not
touched.

## what came out

`first_pass_candidates.csv` — 5,066 rows (5,020 distinct CDRH3), 49 columns.

| source | rows | generator label |
| --- | --- | --- |
| run 001 `her2-baseline` | 2 | free-loop |
| run 004 `004-mohamed-her2-novel-n40` | 10 | free-loop |
| run 005 `005-mohamed-anchored-n40` | 10 | anchored |
| run 006 `006-anas-enumerated-top40` | 44 | enumerated (40) + control (4) |
| `people/anas/legal-scored.csv` | 5,000 | legal-scored |

66 rows have a Boltz-2 structure. Run 007 is **excluded**: it was still on the GPU,
with no manifest, no `refold_metrics.csv` and no `boltz2/` output.

Group sizes (pre-registered labels, not tuned after the fact):

| run | n | PASS_STRICT | PASS_SOFT | PASS_SEQ | FAIL_novelty_official | FAIL_novelty_margin | FAIL_liability | FAIL_grip | FAIL_iface |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 001 | 2 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 |
| 004 | 10 | 0 | 0 | 0 | 0 | 1 | 1 | 8 | 0 |
| 005 | 10 | 0 | 0 | 0 | 9 | 1 | 0 | 0 | 0 |
| 006 | 44 | **8** | **24** | 0 | 1 | 0 | 1 | 2 | 8 |
| legal-scored | 5000 | 0 | 0 | **5000** | 0 | 0 | 0 | 0 | 0 |
| ALL | 5066 | 8 | 24 | 5000 | 10 | 3 | 2 | 11 | 8 |

All 8 survey counts reproduced exactly (run 004: 10/10 official, 9/10 margin, 0/10
grip; run 005: 1/10 official, 0/10 margin, 10/10 grip; run 006: 8/40 above the WT
`iface_min` 0.9010, 0/40 above the run-004 best 0.9330). `p_high` was recomputed
for every row with `rank.p_high` and agrees with the 5,040 stored values to
max |diff| 5.0e-07 (csv rounding).

Three things the survey had wrong or did not have, now pinned down:

1. **The Boltz-2 refold seed is 42 for every run, 001–006.** Seed 1 (and 2 for run
   007) is the *RFD4 generation* seed in `design/config.json`. The survey's
   "seeds differ, 1 vs 42" caveat does not apply to anything structural.
2. **What actually breaks cross-run comparability is the template.** Each run's
   `prepared/holo/template.cif` is built from one of that run's own designs. Runs
   004 and 006 share a byte-identical template (`build_refold.py` copies run 004's),
   so they are directly comparable; runs 001 and 005 each used a different one.
   The `wt_ref` column records `in-batch` / `external-same-template` /
   `external-diff-template` accordingly.
3. **No candidate has more than one Boltz-2 seed**, so the seed noise floor cannot
   be computed. Same seed + same template is bit-reproducible (SD 0.000000 across
   the three `r004_*` designs re-folded in run 006, and run 005's triplicated loop).
   Same seed + *different* template moves `iface_min` by 0.0025 (n=1 sequence).
   The 8 "above WT" candidates beat the WT by only 0.003–0.014, i.e. the deciding
   margins are the size of the one perturbation that has been measured.

## decision

**Keep**, as the reference table for selection, with three handling rules:

- Quote per-run numbers, never the pooled `ALL` row. Generator is almost perfectly
  confounded with every sequence gate (run 004: 10/10 novel, 0/10 grip; run 005: the
  mirror image; run 006: 40/40 on both *by construction*, because the enumeration
  filtered on these gates before folding). A pooled "what do passers share" analysis
  recovers the generator setting, not biology.
- The only live shortlist is run 006: **8 PASS_STRICT + 24 PASS_SOFT**. Runs 001/004/
  005 produce zero passers, all of them stopped by `grip` or `novelty`.
- Do not act on the 8-vs-24 split until a second Boltz-2 seed exists. One short GPU
  job (≈10 candidates + WT, one batch, same template, seed ≠ 42) would settle whether
  a 0.003–0.014 `iface_min` margin is real. Until then PASS_STRICT and PASS_SOFT
  should be treated as one pool of 32.

Nothing here is an affinity claim: `p_high` is capped by the wild type at 0.998 and
`iface_min` is folding confidence (21 measured non-binders in the Champloo set score
AF3 ipTM ≥ 0.7). The PASS groups mean "worth spending a measurement on".

## files

| file | what |
| --- | --- |
| `first_pass_candidates.csv` | 5,066 rows × 49 cols, one row per candidate |
| `first_pass_summary.md` | measured inputs, funnel, distributions, per-position counts, sensitivity grid, seed noise, caveats |
| `input_hashes.txt` | sha256 of every input (scripts, model, csvs, npz, 4 templates) + a rollup over all 78 `*_scores.json` |
| `NOTE.md` | this file |

Reproduce: `cd ~/team14 && py scripts/first_pass.py --out-dir runs/008-claude-first-pass`
