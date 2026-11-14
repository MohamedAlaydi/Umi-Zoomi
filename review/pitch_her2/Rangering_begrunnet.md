# Why these 20 are in this order

This is an updated proposal for prioritising the same 20 optimisation designs. The earlier rank file was based in part on the model run at seed 42. The historical position is shown in the table. Four contrasts were chosen by scientific judgement. The reserves are sorted consistently on sequence score and then on mean overlap across six runs. Exact ties are broken by the number of runs with all four contacts, then by candidate ID. All the selected candidates are pairwise at least three substitutions apart. The result is a proposal for which tests are the most valuable.

The BLOSUM62 sequence score summarises which amino-acid substitutions were made from trastuzumab. At group level, a higher score was associated with a greater chance of a reportable SPR fit in the historical series. Across 584 assessable historical variants the AUROC was 0.847, against 0.751 for the FACS model. Part of that series was itself selected using BLOSUM. Only three historical variants satisfy all the sequence conditions of the new enumerated group, and all three have a fitted KD. That limits the precision available for any single candidate.

The contact fraction in the table counts model runs in which all four selected loop positions touched HER2 at 4.5 Å. Footprint overlap is the Jaccard index for the whole Fab–HER2 contact set measured against the crystal structure, then averaged over six runs. Extra or missing HER2 residues both reduce it. The parent itself scored 6/6 on the loop positions and 96.5 % mean footprint overlap. The six runs share a model and a template. None of these quantities measures KD, competition or temperature.

| New | Prev | Candidate | Sequence score | All four | Footprint overlap | Reason |
|---:|---:|---|---:|---:|---:|---|
| 1 | 1 | anas_007 | 36 | 6/6 | 98.2 % | Best combination in this test panel of a high sequence score and a stable preferred contact face. Exact HER2 footprint in five of six models. |
| 2 | 2 | anas_015 | 32 | 6/6 | 91.2 % | The contact-preserving half of the main experiment. Five substitutions and sequence score 32, the same as anas_009. All four contacts in six of six. |
| 3 | 3 | anas_009 | 32 | 0/6 | 89.6 % | The other half of the same experiment. The same four building blocks are present, but none of the six models has all four contacts at once. |
| 4 | 4 | r004_cdrh3_3 | 19 | 6/6 | 93.9 % | Challenger from a different design method. Only two of the four original amino acids are kept, yet all four positions make contact in six of six. Exact footprint in three of six. |
| 5 | 5 | anas_016 | 40 | 3/6 | 90.2 % | Highest sequence score of the 20. Only three of six models have all four contacts, so the first reserve tests the strongest sequence-based hypothesis. |
| 6 | 7 | anas_028 | 38 | 6/6 | 94.7 % | Sequence score 38 and all four contacts in six of six. A stronger overall case for early testing than the previous number six, anas_027. |
| 7 | 8 | anas_038 | 37 | 0/6 | 96.5 % | Same sequence score as anas_003, but greater mean overlap with the whole HER2 footprint. Three exact footprints, although no pose has all four loop contacts. |
| 8 | 9 | anas_003 | 37 | 6/6 | 87.0 % | Keeps all four contacts across six model runs. At the same sequence score as anas_038, its overall HER2 footprint is less like the parent's. |
| 9 | 10 | anas_004 | 35 | 6/6 | 93.9 % | Best mean overlap in the group scoring 35. All four contacts in six of six. Comparable to anas_021, which also carries four substitutions. |
| 10 | 12 | anas_036 | 35 | 6/6 | 93.2 % | Same sequence score, and the same number of runs with all contacts, as anas_002. A slightly greater mean overlap gives it a narrow priority. |
| 11 | 11 | anas_002 | 35 | 6/6 | 90.4 % | Same sequence score as the two above it, and six of six with all four contacts. Somewhat lower mean overlap. |
| 12 | 13 | anas_021 | 35 | 0/6 | 86.8 % | Lowest mean overlap of the candidates scoring 35. Gives an extra comparison pair with anas_004 if both reach the lab. |
| 13 | 14 | anas_039 | 32 | 2/6 | 86.7 % | Sequence score 32 places it ahead of the candidates scoring 31 under this rule. Only two of six keep all the contacts. Its priority over anas_014 is especially uncertain. |
| 14 | 15 | anas_014 | 31 | 6/6 | 97.5 % | Very high overlap with the whole HER2 footprint, six of six with all four contacts, and three exact footprints. First of the two scoring 31. |
| 15 | 16 | anas_026 | 31 | 6/6 | 87.5 % | Same sequence score, and the same six of six loop contacts, as anas_014, but lower overlap with the whole HER2 footprint. |
| 16 | 20 | anas_031 | 30 | 6/6 | 93.9 % | Greatest mean overlap among the four scoring 30. Keeps all four contacts in six of six. |
| 17 | 18 | anas_010 | 30 | 6/6 | 93.0 % | Second greatest mean overlap among the candidates scoring 30. All four contacts in six of six. The difference from anas_031 is small. |
| 18 | 19 | anas_040 | 30 | 4/6 | 92.3 % | Third highest mean overlap in the group scoring 30. Four of six have all the loop contacts. Its placing against anas_032 depends on which property you weight. |
| 19 | 17 | anas_032 | 30 | 6/6 | 90.6 % | All four contacts in six of six, but the lowest mean overlap among the candidates scoring 30. Loop contacts alone would have given a different order. |
| 20 | 6 | anas_027 | 22 | 0/6 | 89.0 % | A higher mean VH–HER2 model score than the parent, but sequence score 22 and no runs with all four contacts. Kept as a structure-based challenger. |

Public candidate IDs for these queries are in [notes/CANDIDATE_IDS.csv](../../notes/CANDIDATE_IDS.csv).

## De novo, after the two new refolds

The three new VHH designs were assessed by OpenFold3 and Mol-1, with both the short and the long HER2 sequence. The table counts how many of the 19 HER2 contact residues from the crystal structure are recovered in the model. This count only counts recovered residues. The Jaccard index in the Fab table also accounts for extra contacts.

| Design | OpenFold3 short / long | Mol-1 short / long |
|---|---:|---:|
| novel1 | 0 / 0 | 7 / 0 |
| novel2 | 0 / 0 | 0 / 0 |
| novel3 | 0 / 0 | 8 / 8 |

On the short reference, OpenFold3 recovered only 2 of 19 for trastuzumab itself, while Mol-1 recovered 18 of 19. No concurrent reference on the long HER2 sequence is included here. Novel3 is therefore the de novo candidate with the best grounds for follow-up: Mol-1 recovers 8 of 19 in both setups. There is as yet no laboratory measurement of competition, and no final confirmation of de novo track assignment from the organisers. VHH format and a local check alone do not settle the type-dependent identity against known antibodies. **On these data, the proposal to spend two early slots on de novo is on hold. The operative list contains 20 optimisations.**

All 20 chain pairs passed the locally recovered `abguard` build against its reference database. This ranking changes only the order. It is a qualitative prioritisation of an already selected group, and four laboratory tests do not provide enough evidence to validate the whole order.

Sources in the team repo: `review/pitch_her2/final_evidence.json`, `review/pitch_her2/Proposed_ranked_20.csv`, `review/evidence/assay_transfer.json`, `runs/011-codex-denovo-vhh/local-refold-collection.log`, `runs/011-codex-denovo-vhh/local-refold-manifest.json`, and the local validation log.
