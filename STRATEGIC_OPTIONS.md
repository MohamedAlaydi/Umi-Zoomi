# Three ways to spend the remaining lab slots

**Decision for 14 November 2026.** Lead with the test of whether a FACS-trained ranking transfers to measured SPR outcomes. Use the matched structural control to investigate disagreements. Keep a small, explicitly labelled exploration arm in the ranked list. All three options use the team's existing designs.

| Option | Scientific credibility | Research-backed originality | Challenge impact | Feasibility | Demonstrable evidence | Pitch | Reuse | Total /70 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A. Challenge the ranking on a different assay | 9 | 8 | 9 | 10 | 9 | 9 | 9 | **63** |
| B. Measure which part of the modeled interface the score describes | 8 | 7 | 8 | 9 | 9 | 8 | 8 | **57** |
| C. Allocate the scarce assays to contrasting hypotheses | 7 | 7 | 8 | 8 | 6 | 8 | 8 | **52** |

Scores are the team's decision aid in this review, on a 1–10 scale with equal weights. Challenge impact estimates the ability to make a better selection before the deadline. No one can estimate an S-tier probability from the available labels.

The final comparison also tested the FACS ensemble developed concurrently. A nearest-high-FACS rule gave AUROC 0.849 on SPR yet tied all 40 enumerated candidates. BLOSUM62 scored 0.847 and retained 15 distinct values on those 40. The partial multi-seed table reproduced a within-sequence SD of 0.0147. These observations support the ordering above and the use of structural disagreement as an experimental contrast. [Six-score and seed comparison](review/evidence/late_comparison.json)

## A. Challenge the ranking on a different assay

**Problem and stakes.** The generator and the main classifier both used the same source FACS screen. A good score in that screen is an attractive reason to select a design, but the lab ranks on three different outcomes. Optimizing millions of loops and taking the extreme scores magnifies errors at the top.

**Test and evidence.** Freeze the team's saved classifier. On the organiser's SPR table, remove exact FACS overlaps, repeated constructs and the wild-type control. Compare the probability of the high FACS class, a simple BLOSUM62 score against the parent, and mutation count. Keep reportability of a fit and the magnitude of a fitted KD as separate endpoints. Compare within the same mutation count and report uncertainty on paired differences. Chinery et al. motivated the simple baseline. Erasmus et al. independently found that success with affinity maturation did not carry over to within-cluster ranking. [HER2 study](https://doi.org/10.1101/2024.03.26.586756) · [Blinded prospective benchmark](https://doi.org/10.1038/s41587-026-03238-6)

**Demonstration and falsifier.** The first comparison found AUROC 0.847 for BLOSUM62 versus 0.751 for the saved model across 584 variants with usable fit-status labels. A reversal on an untouched design campaign or the prospective hackathon panel would change the recommendation. Of the unseen historical non-WT ten-mers, just three match the enumerated panel's full *sequence constraints*. All three have a fitted KD. Discrimination within that subgroup is unidentifiable. We can demonstrate retrospective evidence for triage and the boundary of its use.

**Delivery and scores.** One analyst, about 1–2 hours for a tested CPU workflow, zero paid inference. Feasibility and evidence score highest because a frozen model and measured outcomes already exist. The method is established. The original contribution is the paired test on this team's score, the mutation-matched sensitivity and the count of relevant measurements behind its shortlist. Judges can see a decision reverse on evidence. The same audit can run on another campaign with a parent and independent assay outcomes.

## B. Measure the actual modeled interface

**Problem and stakes.** Foundry's metrics label B as binder and A, C and D as target. A is the antibody light chain. The coordinate template supplies different amounts of the loop in free and anchored runs. A single global ipTM cannot resolve either issue.

**Test and evidence.** Map the output chains to the experimental sequence pair and the official reference coordinates. Compare heavy–HER2 and light–HER2 scores with the same wild-type query, configuration, template and seed. Count contacts with HER2 using the deposited residue IDs, and change the contact cutoff to test sensitivity. Use the VHH cognate/shuffled matrices and the separate measured SPR panel as a stress test for confidence across targets. The original structure and the VHH benchmark support different parts of this analysis. [1N8Z](https://www.rcsb.org/structure/1N8Z) · [Smorodina et al.](https://doi.org/10.64898/2026.03.02.709004)

**Demonstration and falsifier.** In run 006, the WT heavy-to-HER2 minimum pair score is 0.901. Eight of 40 candidates exceed it in the stored single-sample refold. Identical winners across several score definitions would weaken the case for changing selection on this batch. Missing chains, unmatched templates or failure to recover the WT footprint make a purported pose comparison uninterpretable. Even a stable footprint still needs a competition assay.

**Delivery and scores.** About 1–2 hours with existing coordinate files and CPU arithmetic. The representation error is concrete and easy for a judge to inspect. The ceiling on scientific credibility and challenge impact comes from having one modeled pose per sequence and no competition measurements for the designs.

## C. Allocate lab slots to contrasting hypotheses

**Problem and stakes.** The top four are guaranteed tests. Near-duplicate candidates, or four variants selected by the same overconfident score, can all fail for the same reason. Sequence distance alone also need not imply different binding behavior.

**Test and evidence.** Use the existing candidate panel, within-panel diversity, disagreement between sequence and structural rankings, and the matched control. Put a strong consensus choice early and use some of the remaining places to distinguish whether sequence compatibility or a preserved predicted footprint is more informative. Declare the selection rule and the expected informative failures before the lab returns data. Keep expression failure, missing fit, measured affinity, competition and thermal response in separate fields. The multi-assay results of the blinded benchmark and the clinical-antibody developability panel motivate this design. [Prospective benchmark](https://doi.org/10.1038/s41587-026-03238-6) · [Ten-assay developability panel](https://doi.org/10.1080/19420862.2025.2593055)

**Demonstration and falsifier.** A reproducible order, minimum distance between selected loops and predicted disagreements are observable now. Whether this allocation yields more S-tier designs is a prospective question. If all candidates occupy one region of chemistry or the discordant variants fail expression, the small panel may resolve little. An official rejection can also change who is tested.

**Delivery and scores.** Roughly 30–60 minutes once the evidence table exists, followed by the organiser's validator. This option directly addresses the 4/8/12/16 allocation and contingency tail up to 20. Its empirical score is lowest because the lab will measure outcomes after the event. Discovery teams facing limited assay capacity are the immediate users.
