# 001 mohamed her2-baseline

- when: 14 Nov 2026, 09:12 to 09:40
- what: the organisers' own HER2 pipeline, unchanged, as a smoke test
- script: data/rfd4-proteina/docs/Scripts/run-her2.sh all
- model: her2-novel-2026-11-09, the checkpoint with 86 % novelty pass and
  the best reported interface error (6.8 A)
- settings: N=4 designs, TOPN=2 refolded, seed 1,
  recycle_strategy high/front_loaded
- refold: Boltz-2 with the 1N8Z template
- outcome: EXIT=0, the whole chain works end to end

## Numbers

| design | min_ipae | iptm | binder_plddt | binder_ptm | backbone_rmsd |
| --- | --- | --- | --- | --- | --- |
| her2_cdrh3_3 | 0.310 | 0.965 | 98.51 | 0.993 | 0.744 |
| her2_cdrh3_2 | 0.331 | 0.946 | 95.57 | 0.991 | 1.041 |

The `pass` column is empty, as the Apheris docs warn it is for the HER2
exercise, so these are the columns to rank on.

## Novelty, checked locally

abguard is missing from this VM, so scripts/novelty.py checks the two
published numeric rules against all 525,063 provided CDRH3s.

| design | CDRH3 | min distance | identity to trastuzumab |
| --- | --- | --- | --- |
| her2_cdrh3_3 | WASSSEYYFD | 3 | 30 % |
| her2_cdrh3_2 | WGPPYFYAMD | 2 | 70 % |

## Decisions this run drives

1. The pipeline is sound, so we can spend the day on sampling and
   filtering rather than plumbing.
2. `her2_cdrh3_2` sits exactly on both limits: distance 2 and 70 %
   identity. The task PDF says "under 70 %" and the Apheris slides say
   "at most 70 %". A design on the line is a coin flip we should not take.
   Treat distance >= 3 and identity <= 60 % as our own internal bar, and
   keep the margin.
3. Both designs keep trastuzumab's framework and only CDRH3 changes, so
   these are optimisation-track designs, not de novo.
4. Confidence here is very high (iptm 0.965, plddt 98.5) and that is
   expected to overstate, because the framework and target are given.
   Do not read it as affinity.
