# Five-minute pitch — HER2 design with evidence

English script, approximately five minutes. Use the figure in `report/NY_KVALITETSKONTROLL.png` as the main visual. The four recommended designs are in `../../runs/014-codex-fresh-evaluation/TOP4_INNSENDING.csv`.

## 0:00–0:50 — The clinical problem and our user

A protein model can look confident and still put an antibody on the wrong part of its target. In breast cancer research, that mistake wastes experiments and slows the search for useful medicines.

We focused on HER2-positive breast cancer. Trastuzumab gives us an established target, an experimentally known binding site, and a demanding reference molecule.

Our product is a preclinical decision pipeline for antibody discovery teams. It helps them decide which sequences deserve scarce laboratory tests, using measured data, structural checks, and an explicit account of uncertainty.

The therapeutic goal is to retain useful HER2 recognition while improving stability. Our hackathon output is a set of testable binding modules and a reproducible way to choose them. Treatment efficacy remains a future experimental question.

## 0:50–1:50 — What we built

We started with the organisers' large trastuzumab FACS screen and their measured SPR affinities. These measurements answer different questions, so we trained separate models for them.

For FACS, we separated training, calibration, and test data by patterns at native contact positions, and removed SPR overlaps before fitting. For quantitative affinity, we grouped similar sequences and evaluated predictions on held-out sequence clusters.

The affinity model reached a Spearman correlation of about0.68 on180 measured constructs. A second model gave similar rankings. This supports prioritisation, while the prediction errors remain too large to promise that a new design beats trastuzumab.

We generated approximately183,000 distinct sequence proposals after the initial identity constraint. We then applied exact novelty checks, selected complementary experimental hypotheses, and validated the selected sequences with abguard.

## 1:50–2:50 — Why the decisions are more reliable

We rechecked the candidates against the complete607-residue HER2 sequence. We measured contacts with the native binding site, inspected the antibody's H3 confidence, and kept interface uncertainty separate from global structural confidence.

The controls changed our decisions. One docking model missed the native site even for trastuzumab, so its negative predictions could not veto new candidates. A binding-energy model performed too uncertainly on twelve fresh measured controls, so we removed its authority over ranking.

We also found and corrected an error in the earlier statistical evaluation: four sequences had received a non-inferiority label without the required lower confidence bound.

These are practical safeguards against selecting an attractive model score instead of a credible experiment. The sequences, parameters, references, receipts, and analysis code are recorded in our GitHub repository.

## 2:50–3:50 — The four designs and the stability hypothesis

Our first four are optimisation designs, and all four pass the installed validator with explicit reference data.

The first tests our strongest new affinity hypothesis. The second keeps that H3 and adds a literature-informed framework change, making a matched pair. The third offers a stronger balance between the FACS model and the affinity models. The fourth tests a different H3 family with the same framework hypothesis and supportive geometry from both remote structural models.

The framework change is a concrete attempt to address thermal stability separately from binding. Its transfer to our new H3 sequences and cell-free fragment format is unproven. It also creates a glycosylation motif, which matters when interpreting the published evidence.

Our wider proposal contains eighteen optimisation designs and two exploratory de novo designs. The latter still need the organisers' complete known-antibody database check. We prioritise the better-supported Fab experiments among the four guaranteed tests.

## 3:50–5:00 — The route to value

The next decision comes from the laboratory: expression, SPR affinity, competition with trastuzumab, and direct thermal measurements, with the reference tested alongside our designs.

Those results will decide S-, A-, or B-tier. We do not assign those tiers from predictions.

If a design survives that stage, the breast cancer programme proceeds to HER2-positive cell binding, specificity controls, and an appropriate therapeutic format. An isolated binding fragment does not demonstrate the effector functions or clinical benefit of a complete medicine.

For discovery teams, the immediate value is better use of experimental capacity. Our pipeline connects data-driven sequence proposals to explicit checks, exposes failed assumptions, and produces a ranked, auditable experiment list.

Additional test allocations would let us compare the matched stability hypotheses and broaden the portfolio. Each result can improve the next design round. That is the case we can defend today: a working selection pipeline, concrete new molecules, and a clear path from computation to biological evidence.

---

## Short answers for the judges

- **Are the new molecules better?** Their predictions are more promising in parts of the new sequence space. Experimental improvement has not been demonstrated.
- **Why not use global ipTM to choose?** It measures structural confidence; in Fab it also includes VH–VL interactions. It is neither affinity nor thermal stability.
- **Why two models?** Agreement can support a hypothesis; disagreement identifies uncertainty. A model that fails its WT control cannot provide a reliable negative gate.
- **What is the biggest remaining gap?** Measured thermal stability and binding for these new constructs; complete known-antibody novelty confirmation for the de novo pair.
- **Can you call this a breast cancer therapy?** It is a preclinical discovery platform for future HER2-binding therapeutic modules. Efficacy, safety, and therapeutic format remain to be established.

Clinical context: [EMA Herceptin](https://www.ema.europa.eu/en/medicines/human/EPAR/herceptin). Framework evidence and its limits are documented in the accompanying report and [Ng et al.,2025](https://doi.org/10.1080/19420862.2025.2532117).
