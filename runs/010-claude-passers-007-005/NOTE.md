# 010 claude passers-007-005

- image: apheris-boltz-v1.3.0-boltz2, through people/anas/run_refold.sh (same flags as run 006)
- command: people/anas/run_refold.sh 010-claude-passers-007-005 claude-passers
- seed: 42, one diffusion sample
- template: run 004's prepared/holo/template.cif, the same one runs 006 and 009 use
- batch: 16 generated designs + 4 controls (trastuzumab_wt, r004_cdrh3_4, r004_cdrh3_3, r004_cdrh3_31)
- built by: build_passers.py in this folder. candidates.csv lists each design, its run, and whether it had a fold before

## why we ran it

Runs 005 and 007 refolded only the best 10 and 12 designs by design score. Novelty was never
part of that choice, so most designs that pass the published novelty rule never got a
structure score, and the ones that did were folded against their own run's template, so
their numbers cannot sit next to the enumerated candidates of run 006.

This batch folds every generated design that is IDEAL (4/4 contacts kept, D102 and M107
changed), has no cysteine, and passes the published novelty rule (distance >= 2, identity
<= 70 %). That is 16 distinct loops: 11 never folded, 5 folded before under another
template. Two loops from run 007 were left out because they carry an unpaired cysteine
(her2_anchored_11 WGMPGFYCHT, her2_anchored_20 WSVSGFYMCD). Three run-005 designs
(0, 8, 33) are the same loop, WGPSGFYAHD, and fold once as r005_a00.

All 16 sit at distance 2, the published minimum, none at our own bar of 3. Two sit on the
70 % identity line (r007_a23, r005_a00).

## what came out

Finished 12:25 UTC, EXIT=0, 20 of 20 queries scored with people/anas/collect_refold.py.
Table: refold-010.csv in this folder.

The controls reproduce run 006 exactly (wild type iface_min 0.901, r004_cdrh3_3 0.933,
r004_cdrh3_31 0.905, r004_cdrh3_4 0.900), so these numbers sit directly next to
people/anas/refold-006.csv. Anas's best enumerated loop there is 0.915.

10 of 16 generated loops are above the wild type. Sorted by iface_min:

| query | CDRH3 | iface_min | iptm | identity | new liability |
| --- | --- | --- | --- | --- | --- |
| r005_a14 | WGPAGFYEFD | 0.932 | 0.967 | 60 % | none |
| r005_a34 | WGPAGFYHHD | 0.923 | 0.961 | 60 % | none |
| r007_a02 | WMVTGFYAFT | 0.921 | 0.960 | 50 % | new Met at 100 |
| r007_a18 | WRDYGFYYFD | 0.916 | 0.955 | 50 % | none |
| r005_a22 | WGPSGFYFFD | 0.912 | 0.953 | 60 % | none |
| r007_a37 | WGPQGFYEFD | 0.911 | 0.950 | 60 % | none |
| r007_a27 | WGWEGFYNFD | 0.909 | 0.951 | 60 % | extra Trp at 101 |
| r007_a28 | WGYLGFYEYD | 0.905 | 0.946 | 60 % | none |
| r007_a04 | WGKFGFYDFD | 0.903 | 0.948 | 60 % | none |
| r007_a26 | WAAPGFYAQP | 0.903 | 0.945 | 50 % | none |
| r007_a32 | WGASGFYYHD | 0.897 | 0.945 | 60 % | none |
| r007_a25 | WSSKGFYQHT | 0.894 | 0.941 | 40 % | none |
| r007_a23 | WGPVGFYADD | 0.893 | 0.943 | 70 % | DD at 107 |
| r005_a00 | WGPSGFYAHD | 0.876 | 0.935 | 70 % | none |
| r007_a05 | WGDGGFYENN | 0.872 | 0.931 | 50 % | DG at 101 |
| r007_a33 | WGPSGFYVDN | 0.856 | 0.923 | 50 % | none |

Wild type 0.901. All 16 sit at distance 2. "New liability" is a motif scan (extra Met or Trp,
D followed by G, S, T, D or H, N followed by G, S, T or H, N-X-S/T), which report.py does not do.
The last six are at or below the wild type. Single seed, one diffusion sample: margins under
about 0.01 are not distinguishable from noise until run 009 gives the seed spread.

## decision

(keep / drop, and why)
