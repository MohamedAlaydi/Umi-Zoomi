# 001 mohamed her2-baseline

- what: the organisers' own HER2 pipeline, unchanged, as a smoke test
- script: data/rfd4-proteina/docs/Scripts/run-her2.sh all
- model: her2-novel-2026-11-09 (86 % pass the novelty filter, best interface error 6.8 A)
- settings: N=4 designs, TOPN=2 refolded, seed 1, recycle high/front_loaded
- refold: Boltz-2 with the 1N8Z template
- why: prove the whole chain runs before we change anything, and get a
  reference set of numbers to compare our own runs against
- outcome: see scored-boltz2/refold_metrics.csv
