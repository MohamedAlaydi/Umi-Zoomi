# Score table

This is the computational score ledger for the hackathon submission.

Start with the [proposed ranked 20](RANKED_CANDIDATES.csv)
and [selection rationale](../review/pitch_her2/Rangering_begrunnet.md).
The [earlier review order](../review/evidence/panel.csv) and
[earlier ensemble order](../people/anas/final-20.csv) are dated analyses,
not additional submissions.
Public candidate IDs describe the method: `HER2-OPT` for enumerated
optimisation designs and `HER2-GEN` for a generator comparator. Their numeric
suffix is stable across ranking changes. [ID mapping](CANDIDATE_IDS.csv)
connects them to the original model queries; original evidence stays intact.
Read [how scores and judging criteria differ](SCORING.md).
The [de novo campaign report](../review/denovo/CAMPAIGN_RESULTS.md) and
[campaign evidence](../runs/011-codex-denovo-vhh/local-refold-evidence.json)
record the separate hosted-model checks. The
[binding-ddG table](../people/anas/stabddg-joined.csv) is a binding prediction,
not a thermal-stability measurement.

**This file is generated.** Do not hand-edit it: run

    py scripts/scores.py

and it is rebuilt from the files the models actually wrote. Small score and
provenance files are copied byte for byte into each run's `score-evidence/`
directory, so the cited files also exist in a fresh GitHub checkout without
the VM's data directory or output symlinks. `score-evidence/SHA256SUMS` in each
run records the snapshot hashes. Heavy structures and model weights are
outside this score ledger; see the reproducibility notes for those artifacts.
`py scripts/scores.py --check` re-reads every one of those paths and fails if
the table and the files have drifted apart. Reasoning about these numbers
belongs in `notes/DECISIONS.md`, not here.

Scores taken from each query's `*_scores.json` keep the name that file uses.
`p_high` is a classifier prediction trained on measured FACS classes. It is
not measured binding, an SPR KD or a calibrated probability of improvement.
Structural confidence, predicted binding-ddG and chemical-liability flags do
not establish higher affinity, competition with trastuzumab or higher Tm.
No new experimental values for those three endpoints are reported here.
Local novelty screens are not final organiser acceptance.
`novelty_min_distance` and
`identity_percent_to_wild_type` are not recomputed here: they are read back
verbatim from the novelty table the run itself wrote into its own `run.log` or
`candidates.csv`. The `model + checkpoint` column names the file that attests
the module, the checkpoint and the seed, in brackets.

<!-- score-ledger: SCORES_FULL.md -->
All **2,168** score rows: [CSV](SCORES.csv) · [full ledger with source links](SCORES_FULL.md).

## Coverage

| Run | Designs | Score rows | Numeric seeds |
| --- | ---: | ---: | --- |
| Run 001: her2-baseline | 2 | 8 | 42 |
| Run 004: her2-novel-n40 | 10 | 60 | 42 |
| Run 005: anchored-n40 | 10 | 60 | 42 |
| Run 006: enumerated-top40 | 44 | 216 | 42 |
| Run 007: anchored-diverse-k1 | 12 | 72 | 42 |
| Run 009: multiseed-refold | 90 | 1640 | 1, 2, 3, 4, 5, 42 |
| Run 010: passers-007-005 | 20 | 112 | 42 |

## Proposed panel: original matched seed-42 scores

This preserves the proposed experimental order. These are the original run-006
complex scores, not a claim of seed robustness or measured affinity. Global ipTM
also includes the VH–VL interface. See the linked rationale for the six-seed
HER2-contact evidence used for selection. A local validator pass is not final acceptance.

BLOSUM62 and repeated-contact counts come from the supplied ranked panel,
not from these single-seed JSON files. There is no official weighted total score.

| Rank | Candidate | BLOSUM62 | Four contacts / 6 | Global ipTM | Complex pLDDT | Raw score |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 1 | HER2-OPT-007 | 36 | 6/6 | 0.94 | 95.029 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_007/seed_42/anas_007_seed_42_sample_1_scores.json) |
| 2 | HER2-OPT-015 | 32 | 6/6 | 0.941 | 96.44 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_015/seed_42/anas_015_seed_42_sample_1_scores.json) |
| 3 | HER2-OPT-009 | 32 | 0/6 | 0.948 | 96.542 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_009/seed_42/anas_009_seed_42_sample_1_scores.json) |
| 4 | HER2-GEN-003 | 19 | 6/6 | 0.967 | 97.132 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/r004_cdrh3_3/seed_42/r004_cdrh3_3_seed_42_sample_1_scores.json) |
| 5 | HER2-OPT-016 | 40 | 3/6 | 0.945 | 96.364 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_016/seed_42/anas_016_seed_42_sample_1_scores.json) |
| 6 | HER2-OPT-027 | 22 | 0/6 | 0.952 | 95.086 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_027/seed_42/anas_027_seed_42_sample_1_scores.json) |
| 7 | HER2-OPT-028 | 38 | 6/6 | 0.942 | 96.642 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_028/seed_42/anas_028_seed_42_sample_1_scores.json) |
| 8 | HER2-OPT-038 | 37 | 0/6 | 0.928 | 95.584 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_038/seed_42/anas_038_seed_42_sample_1_scores.json) |
| 9 | HER2-OPT-003 | 37 | 6/6 | 0.927 | 95.908 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_003/seed_42/anas_003_seed_42_sample_1_scores.json) |
| 10 | HER2-OPT-004 | 35 | 6/6 | 0.935 | 94.993 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_004/seed_42/anas_004_seed_42_sample_1_scores.json) |
| 11 | HER2-OPT-002 | 35 | 6/6 | 0.927 | 96.656 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_002/seed_42/anas_002_seed_42_sample_1_scores.json) |
| 12 | HER2-OPT-036 | 35 | 6/6 | 0.938 | 95.873 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_036/seed_42/anas_036_seed_42_sample_1_scores.json) |
| 13 | HER2-OPT-021 | 35 | 0/6 | 0.934 | 96.586 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_021/seed_42/anas_021_seed_42_sample_1_scores.json) |
| 14 | HER2-OPT-039 | 32 | 2/6 | 0.937 | 96.613 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_039/seed_42/anas_039_seed_42_sample_1_scores.json) |
| 15 | HER2-OPT-014 | 31 | 6/6 | 0.928 | 94.575 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_014/seed_42/anas_014_seed_42_sample_1_scores.json) |
| 16 | HER2-OPT-026 | 31 | 6/6 | 0.949 | 97.617 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_026/seed_42/anas_026_seed_42_sample_1_scores.json) |
| 17 | HER2-OPT-032 | 30 | 6/6 | 0.929 | 95.551 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_032/seed_42/anas_032_seed_42_sample_1_scores.json) |
| 18 | HER2-OPT-010 | 30 | 6/6 | 0.939 | 97.223 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_010/seed_42/anas_010_seed_42_sample_1_scores.json) |
| 19 | HER2-OPT-040 | 30 | 4/6 | 0.922 | 95.644 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_040/seed_42/anas_040_seed_42_sample_1_scores.json) |
| 20 | HER2-OPT-031 | 30 | 6/6 | 0.943 | 95.854 | [JSON](../runs/006-anas-enumerated-top40/score-evidence/modules/boltz2/anas_031/seed_42/anas_031_seed_42_sample_1_scores.json) |
