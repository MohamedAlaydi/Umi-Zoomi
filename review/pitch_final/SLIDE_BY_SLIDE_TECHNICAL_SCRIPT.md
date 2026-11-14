# Umi Zoomi — technical script matched to the actual slides

Use the PDF page numbers below. The live presentation has 11 main stops because Picks 01–04 share one animated slide. PDF pages 8–11 show those four states separately.

**“Say” is the presentation narrative. “Optional depth” is material to add while that slide is visible or use for questions.** This is deliberately longer than five minutes. The detailed implementation audit remains in `TECHNICAL_MASTER_MANUSCRIPT.md`; you do not need to narrate that audit during the presentation.

## Page 1 — Umi Zoomi: antibody redesign for HER2+ breast cancer

**On screen:** the team name and the clinical theme.

**Say:**

“We are Umi Zoomi. Our project explores antibody-fragment redesign against HER2, motivated by HER2-positive breast cancer.

We started from trastuzumab and built a workflow that learns from experimental measurements, generates new antibody sequences and checks the evidence supporting each proposal. Our aim is to identify useful molecules to test, while keeping the distinction between a model prediction and an experimental result clear.

I’ll explain the biological objective, how we built the pipeline, what the models actually found and which experiments would tell us whether these changes are useful.”

**Transition:** “First, why start with trastuzumab?”

## Page 2 — Why HER2-positive breast cancer? / What should improve?

**On screen:** two cards: clinical motivation and the properties to improve. Reveal and explain them in that order.

**Say:**

“Trastuzumab is an established HER2-directed treatment. It gives us a relevant starting molecule, a known experimental binding site and a demanding reference to compare against.

Our engineering question is whether we can change the antibody’s sequence while preserving recognition of that site, and potentially improve affinity or thermal stability.

These correspond to the hackathon’s experimental endpoints: HER2 binding by surface plasmon resonance, competition with trastuzumab, and direct thermal measurements. They are distinct questions. Binding at the intended site does not automatically mean tighter binding, and tighter binding does not automatically mean a more stable protein.

The breast cancer connection is the reason to pursue this research. Our present constructs are paired variable domains, not full therapeutic antibodies. Any useful fragment would require further development and testing before we could claim therapeutic benefit.”

**Optional depth:** A lower dissociation constant, KD, means tighter affinity under comparable conditions. Our historical WT median is 0.1345 nM, already a strong benchmark. Use a matched reference in the new assays; historical KD is only our modelling normalisation. Do not suggest that this project has demonstrated improved tumour killing, resistance reversal or reduced toxicity.

**Transition:** “With that objective, what does a discovery team need from the computational workflow?”

## Page 3 — Build. Test. Learn.

**On screen:** workflow purpose and the number four.

**Say:**

“The immediate user is a discovery team deciding which molecules to make and test. Generating a large number of sequences is useful only if we can explain why particular sequences deserve the laboratory budget.

Our workflow connects each proposed sequence to its experimental-data support, submission checks and predicted structural behaviour. It also records missing results and model disagreements.

The four on this slide are our first experimental priorities. They have been evaluated computationally; they have not yet completed laboratory validation. The wider ranked list contains twenty designs, but the initial four form a small panel with specific questions: three different binding loops, including a matched comparison of two framework changes.

The build–test–learn cycle will become an experimental learning loop when those measurements return. At present, we have implemented the design and evaluation stages and defined what the next tests must establish.”

**Optional depth:** Four tests are guaranteed under the challenge allocation. Extra tests depend on placement and judge nominations. The twenty are ranked because only the top allocated number will go forward. Our current order has all four initial positions in the optimisation track.

**Transition:** “To understand those choices, we first need to locate the part of the molecule we changed.”

## Page 4 — Keep the right contact

**On screen:** molecular context and the intended binding region. Point to the molecule as you explain it.

**Say:**

“This is the molecular question behind the redesign: can we change the antibody while keeping it compatible with trastuzumab’s HER2 binding site?

We focused on CDR-H3, the third complementarity-determining loop of the heavy variable domain. It contributes to the binding surface together with the other loops and the light chain.

The ten-residue core we changed is `WGGDGFYAMD` in trastuzumab. The full numbered H3 also includes fixed flanking residues, giving `SRWGGDGFYAMDY`. That distinction matters because the models use the ten-residue core, while the final novelty checks use the full loop.

In the molecular views, blue identifies the heavy variable domain, cream the light variable domain, green the displayed HER2 region and yellow the redesigned loop. These colours identify parts, not binding strength or prediction confidence.

We compare predicted contacts with the experimental trastuzumab complex, 1N8Z. This gives a concrete reference-site question rather than relying only on a global model score.”

**Optional depth:** Each prioritised construct has a 120-residue heavy variable domain plus an unchanged 107-residue light variable domain: 227 residues combined. The redesigned core is at linear heavy-domain positions 99–108. The four contact-associated core positions W1/G5/F6/Y7 were sampled less frequently for mutation, but were not frozen. The structural input uses a 607-residue HER2 target construct; it does not reproduce the entire membrane receptor and cellular environment. Candidate views show target residues 489–607 for readability.

**Transition:** “We then combined experimental sequence models with structural evaluation.”

## Page 5 — What we built: Learn → Check → Choose

**On screen:** three pipeline labels. Follow their order. This is the main methods slide; put training detail here rather than on the candidate slides.

### Learn

**Say:**

“The learning stage uses two kinds of experimental data, with separate models because the measurements mean different things.

The FACS dataset contains 524,346 unique H3 cores, assigned to high, medium or low screening classes. We predict high class versus the other two classes. This is a screening phenotype influenced by binding and display; it is not a numerical affinity measurement.

We removed 37 sequences overlapping the SPR data. We then grouped sequences by their amino acids at four contact-associated positions and assigned whole groups to training, calibration and testing. The resulting partitions contain 375,230, 83,098 and 65,981 sequences.

We trained a categorical gradient-boosting model and a simpler one-hot logistic model, then calibrated each on the separate calibration set. Their held-out AUC values are 0.971 and 0.926. We use the lower of their two calibrated outputs as a conservative agreement score. That minimum is a ranking heuristic, not a validated probability that a molecule binds.

For affinity, the SPR table contains 768 rows. After selecting comparable quantified constructs and aggregating repeated observations, we have 180 unique constructs. We predict log-ten KD relative to the historical WT median of 0.1345 nanomolar.

The primary model is regularised Ridge regression. We also fitted a Gaussian process as a secondary sensitivity analysis. Their role is to help compare affinity hypotheses. I’ll show their validation and limitations on the results slide.”

### Check

**Say:**

“Next, we evaluate predicted complexes against the 607-residue target construct. JapanFold provided Mol1 and OpenDDE predictions. We also used a smaller local Boltz-2 panel with a different template and MSA setup.

We examine whether the predicted antibody reaches the reference epitope, its interface uncertainty, loop confidence and obvious geometric overlaps. We run the known WT reference through the same model protocol so that a failed control can change how we interpret a candidate prediction.”

### Choose

**Say:**

“Finally, we combine the sequence requirements, assay-model hypotheses and structural checks to choose a diverse panel. Abguard checks the antibody format and sequence rules against the supplied references. Published framework evidence gives us a separate, testable stability hypothesis.

The code, settings, candidate identities and evidence are recorded in GitHub. We retrained the assay predictors in this fresh phase; we did not fine-tune the foundation folding models.”

**Optional depth — training settings:**

| Component | Implementation |
|---|---|
| FACS grouping | 10,329 four-position contact patterns; deterministic hashed nominal 70/15/15 split; seed 271828 |
| Categorical GBM | 120 iterations, maximum 15 leaves, minimum leaf size 40, L2 0.5 |
| Logistic regression | 200 one-hot features, C = 1 |
| Calibration | Separate scalar Platt calibration for each classifier |
| Ridge | 200 one-hot features plus mutation fraction; alpha 10 |
| Affinity validation | Five folds; 126 connected sequence groups linking edit distance ≤2 |
| Proposal uncertainty heuristic | Sixteen bootstrap Ridge fits; mean plus one parameter-spread SD |
| Fresh primary Mol1 | Seed 271828, one sample, no supplied template or hotspots |

The fresh remote evidence snapshot has 103 usable model–target rows: 87 Mol1 and 16 OpenDDE. These are model evaluations across candidates and controls, not 103 independent antibodies. The predictors learn within the trastuzumab background; their validation does not establish transfer to VHHs or new frameworks.

**Transition:** “Three findings from these checks changed how much weight we gave each result.”

## Page 6 — Screen ≠ affinity / Controls matter / Test stability separately

**On screen:** reveal and discuss one card at a time.

**Say — Screen ≠ affinity:**

“First, a good screening score is not the same as stronger affinity. Despite high FACS classification AUC, the screening models have weak correlations with measured log KD in the quantified external cohort: approximately minus 0.18 and minus 0.07. We therefore kept screening and affinity models separate, and selected proposals representing both kinds of evidence.”

**Say — Controls matter:**

“Second, model negatives need controls. At our 4.5-angstrom contact definition, the native reference site contains nineteen HER2 residues. Mol1 recovers all nineteen for WT. OpenDDE recovers only two.

That means an OpenDDE prediction away from the site is not a reliable veto on a new design. We keep its output as evidence of agreement or disagreement, but we cannot treat it as a validated nonbinding test. The local Boltz-2 WT also misses the site in its different configuration.”

**Say — Test stability separately:**

“Third, we need a distinct stability hypothesis. We introduced heavy-framework substitutions S85N and R87T, motivated by published experiments on trastuzumab. We verified the numbering before applying them.

Their effect in our redesigned fragment backgrounds remains unknown. The changes introduce a potential glycosylation site, which adds another reason to test transfer in the actual expression system. We have no measured melting temperature for these variants, and our H3-only assay models cannot predict the framework effect.”

**Optional depth:** Contact recall is the number of reference target residues contacted by the prediction divided by nineteen. It is not nineteen measured chemical bonds. OpenDDE negatives remain uncertain because of the WT control, but this does not prove those negatives are wrong. StaB-ddG was also checked on twelve historical controls: Spearman 0.322, bootstrap interval −0.350 to 0.830. That was insufficient support to make it a major ranker. Binding-ddG is not a thermal-stability measurement. Framework source: [Ng et al., 2025](https://doi.org/10.1080/19420862.2025.2532117).

**Transition:** “With those limitations explicit, this is how we narrowed the design space.”

## Page 7 — The funnel: 182.6k → 1,062 → 20 → 4

**On screen:** four funnel states. Explain each number when it appears; the figure is a summary of linked stages, not a single uninterrupted filtering operation.

**Say — 182.6k:**

“We made 200,000 mutation attempts from WT and six measured parent loops. After the initial identity gate and deduplication, 182,595 distinct loop proposals remained. Each attempt changes three to six positions relative to its sampled parent. We exclude cysteine from the substitution alphabet and reduce, rather than eliminate, mutation sampling at the four contact-associated positions.”

**Say — 1,062:**

“We scored these proposals and shortlisted 2,000 using screening agreement and the affinity-risk heuristic. Of that shortlist, 1,062 passed the exact distance gate against the provided data.

Our conservative optimisation policy requires full H3 identity below seventy percent to WT and at least three edits from every provided reference H3. The reference collection contains 525,063 unique full loops. The 1,062 are passes among the 2,000 shortlisted proposals, not among every generated sequence.”

**Say — 20:**

“The final twenty combine selected new proposals with earlier sequences evaluated again. Eighteen are optimisation entries and two are intended de novo VHHs. The de novo entries still need confirmation against the organisers’ complete known-antibody database; our local checks do not establish that universal novelty claim.”

**Say — 4:**

“The first four are locally validated optimisation designs. They cover three H3 loops and two framework-modified constructs. We deliberately retained a matched framework pair so that the first experimental panel can test a specific intervention.”

**Optional depth:** The diverse generated list contains 68 proposals; twelve new H3s were selected for structure work, then four framework variants and a framework WT control were added. The final panel also includes re-evaluated earlier designs. Local checks pass all twenty, but the two intended de novo entries remain provisional. They are at ranks 15 and 16. The funnel bar colours distinguish stages; their widths are illustrative rather than a linear scale across the very different counts.

**Transition:** “Here is the experimental question attached to each of the first four.”

## Page 8 — Pick 01: Binding loop A

**On screen:** Pick 01 molecule, its ten-letter core, yellow conserved-position tiles and screen score 0.16.

**Say:**

“Pick one is an optimisation design with H3 core `WGSQGFYEMG`. It changes four of the ten core residues relative to trastuzumab while retaining the four highlighted contact-associated amino acids.

We selected this loop for its affinity-model hypothesis. Its screening agreement is only 0.16, which is visible here. That is weak joint screening support, not a sixteen-percent measured binding rate.

The molecule shown is the selected Mol1 prediction. It reaches the reference site with relatively low predicted interface uncertainty. That supports a pose hypothesis, but does not tell us its KD.

The question for the laboratory is whether this affinity-led loop expresses and binds as usefully as predicted, despite the weaker screening-model signal. On the comparison slide, we will see that the two affinity models disagree about whether it beats WT.”

**Optional depth:** ID `newML_b973259db36d`; full H3 `SRWGSQGFYEMGY`. Mol1: 19/19 reference contacts, interface PAE 3.05 Å, H3 pLDDT 88.64. OpenDDE: 15/19, PAE 5.14 Å. Ridge predicts KD/WT 2.94; GP predicts 0.94. Neither number is a new measurement.

**Transition:** “Pick two keeps this same loop and changes its supporting framework.”

## Page 9 — Pick 02: Loop A with two changes

**On screen:** same loop letters, modified molecule, screen score 0.16 with an asterisk.

**Say:**

“Pick two has the same H3 and light chain as Pick one. Its difference is the pair of heavy-framework substitutions, S85N and R87T.

Comparing these two constructs asks whether those framework changes alter binding, expression or thermal stability on this redesigned loop background. This is the clearest matched experiment in our four-design panel.

The screen score remains 0.16 because the assay model only sees H3. The asterisk matters: the identical score is an inherited parent-loop estimate, not evidence that the framework edits preserve binding.

The structural evidence is mixed. Mol1 retains the reference site, OpenDDE predicts another site, and local Boltz-2 recovers the reference contacts in its different setup. We preserve that disagreement. The experimental comparison must resolve whether the framework intervention helps.”

**Optional depth:** ID `newML_b973259db36d_FW85N87T`. Mol1: 19/19, interface PAE 3.51 Å. OpenDDE: 0/19 reference contacts, PAE 23.99 Å; it contacts a different target region. Local Boltz-2: 19/19. Zero reference contacts does not mean zero contact with HER2. No new Tm is available.

**Transition:** “Pick three explores the other major signal: stronger screening support.”

## Page 10 — Pick 03: Binding loop B

**On screen:** a different core and the highest screen score, 0.84.

**Say:**

“Pick three uses core `WAYEGFYEMD`, again with four substitutions relative to the WT core and the original framework.

Its defining feature is the screening agreement of 0.84, the highest among these four. It represents stronger joint support from the two screening models, whereas Pick one is more affinity-led.

That does not mean it is predicted to be our tightest binder. Both affinity models estimate a weaker KD than the historical WT reference. So this candidate tests whether strong screening support translates into a useful expressible binder, rather than simply selecting four versions of the same model preference.

Mol1 places it at the intended site. Its second-model job failed technically, so that result is missing. We do not treat a failed job as either a positive result or a prediction of no binding.”

**Optional depth:** ID `newML_a7acfcc8dce3`; full H3 `SRWAYEGFYEMDY`. Mol1: 19/19, PAE 3.08 Å, H3 pLDDT 88.93. KD/WT estimates: Ridge 5.84 and GP 2.31. If the slide’s wording ‘favourable affinity predictions’ comes up, qualify it: it was competitive within our candidate selection, not predicted improvement over WT by either model.

**Transition:** “The fourth design combines another loop with the framework hypothesis.”

## Page 11 — Pick 04: Loop C with two changes

**On screen:** third loop, framework-modified construct and screen score 0.27 with an asterisk.

**Say:**

“Pick four uses core `WRSEGFYEMR` and carries the same framework substitutions as Pick two. This core has five changes relative to WT.

Its screen agreement is 0.27, and again the asterisk means the framework effect is outside the assay model. Its distinctive support is that Mol1 and OpenDDE both place it close to the reference site: nineteen and eighteen of the nineteen reference contacts, respectively.

This explores the framework intervention on a second H3 background. However, its unmodified-framework parent is not in the first four. A favourable result for Pick four alone would therefore not tell us whether the loop, the framework or their combination caused it.

Together, the four designs form three loop hypotheses and one direct matched framework comparison. They are all optimisation designs, not four de novo antibodies.”

**Optional depth:** ID `newML_5753ea077281_FW85N87T`; full H3 `SRWRSEGFYEMRY`. Mol1 PAE 4.02 Å; OpenDDE PAE 4.40 Å. KD/WT: Ridge 3.96, GP 2.96. Both predict weaker affinity than the historical reference. Expand the panel with its original-framework parent to isolate the framework effect.

**Transition:** “Now we can compare the evidence across the four rather than looking at each model in isolation.”

## Page 12 — Four variants: different model signals

**On screen:** the four-row numerical table. Explain left to right: screening, affinity ratios, then interface uncertainty.

**Say:**

“The screening column summarises agreement between two high-class predictors. Pick three has the highest value, 0.84; Picks one and two have 0.16; Pick four has 0.27. These are not measured binding probabilities.

The middle columns estimate KD relative to the historical WT median. Lower is tighter, and one means the historical reference. Pick one’s loop has the lowest estimates here: 2.94 times WT from Ridge and 0.94 times WT from the Gaussian process. The models disagree on whether it improves on WT.

For Pick three, both ratios exceed one: 5.84 and 2.31. Pick four is also above one in both models. So this table does not establish stronger binding for the panel. The small nominal GP advantage for loop A is especially uncertain.

Picks two and four have asterisks because the models do not evaluate their framework changes. The last column is Mol1 interface PAE, ranging from 3.05 to 4.02 angstroms. This measures predicted positional uncertainty, not KD or measured structural error.

All four recover nineteen of nineteen reference contacts in Mol1, but that identical result cannot distinguish their affinity or stability. The useful finding is the difference between model signals, and the experiments that those differences motivate.”

**Numbers to point at:**

| Pick | Screen | KD/WT: Ridge / GP | Mol1 interface PAE |
|---|---:|---:|---:|
| 01 | 0.16 | 2.94 / 0.94 | 3.05 Å |
| 02* | 0.16* | 2.94 / 0.94* | 3.51 Å |
| 03 | 0.84 | 5.84 / 2.31 | 3.08 Å |
| 04* | 0.27* | 3.96 / 2.96* | 4.02 Å |

The asterisk applies to both affinity estimates as well as the screening score for framework variants. No new measured KD or Tm is available.

**Transition:** “To decide how seriously to take these affinity numbers, we need to inspect their historical validation.”

## Page 13 — Held-out test: 180 constructs, rank correlation 0.68

**On screen:** measured-versus-predicted affinity plot and three explanatory cards. Point to the axes, diagonal and red WT reference in that order.

**Say:**

“Each blue point represents a historical measured construct. The horizontal axis is measured KD and the vertical axis is the primary model’s held-out prediction. Both axes are logarithmic. A point on the diagonal would be an exact numerical prediction.

We grouped close sequence relatives together before splitting the 180 constructs into five folds. That means a point’s prediction was made without fitting its sequence group. There are 126 such groups.

The rank correlation of 0.68 indicates useful ordering signal across this measured series. It is not sixty-eight-percent accuracy and does not establish that the model resolves small improvements near WT.

The red point highlights that limitation. WT’s historical median is 0.1345 nanomolar, while its held-out prediction is approximately 9.08 nanomolar, about 67.5 times higher. Calibration near the strong reference is poor.

That is why we interpret the new affinity numbers as hypotheses. A nominal six-percent GP advantage for one loop is much smaller than the observed prediction errors. This model can inform an experiment list; it cannot certify that our designs beat trastuzumab.”

**Optional depth:** Primary Ridge Spearman 0.6752; log10 MSE 0.6505; RMSE 0.8065 log units. Secondary GP Spearman 0.6727; MSE 0.5911; RMSE 0.7688. The 95th percentiles of historical absolute log error correspond to about 58-fold and 49-fold error magnitudes, not guaranteed novel-design intervals. The plotted predictions are grouped out-of-fold Ridge predictions; candidate estimates average separate bootstrap fits. All affinity training is conditional on reportable KD, not a validated classifier of arbitrary binder/nonbinder outcomes.

**Transition:** “What does this leave us with, and what decision should come next?”

## Page 14 — Thank you: conclusion and next steps

**On screen:** closing slide. There is no new result chart here; draw the conclusion from pages 12 and 13.

**Say:**

“We built and documented a workflow that connects experimental data, sequence generation, eligibility checks and structural controls. It produced new HER2 variable-region designs and a ranked panel with explicit experimental questions.

Our four initial priorities cover three loops and a matched framework comparison. Their primary predicted structures retain the intended site, but the assay models disagree, framework effects remain unmodelled and improved performance is unproven.

The next step is expression followed by matched HER2 affinity, competitive-binding and thermal measurements alongside the reference. We should record failures and missing measurements, not only successful binders. Those experiments will determine the actual challenge results.

If a useful variant emerges, the breast cancer programme would then need cell-surface HER2 binding, specificity and further development in an appropriate therapeutic format. Separately, we should compare the workflow prospectively with simpler selection methods at the same laboratory budget.

Our result today is a reproducible path from sequence ideas to testable molecules. The next evidence must come from the laboratory.”

**Optional depth for questions:** No confirmed S-tier design; no demonstrated cancer-cell efficacy; no new measured affinity or thermal gain. The strength of the current work is the implemented pipeline and explicit handling of controls and uncertainty. Its experimental advantage over the earlier approach or a simpler baseline remains to be tested.

---

## Quick navigation

| PDF page | Live stop | What to explain here |
|---|---:|---|
| 1 | 1 | Project and objective |
| 2 | 2 | Clinical motivation and three experimental endpoints |
| 3 | 3 | Discovery-team user and experimental-panel purpose |
| 4 | 4 | H3, molecular parts, target and reference site |
| 5 | 5 | Data, training, structural models and eligibility pipeline |
| 6 | 6 | Three findings that changed interpretation |
| 7 | 7 | Generation counts, novelty filtering and panel allocation |
| 8–11 | 8, four states | One candidate and experimental question at a time |
| 12 | 9 | Compare actual candidate model outputs |
| 13 | 10 | Interpret the validation plot and uncertainty |
| 14 | 11 | Conclusion and next experiments |

Numerical sources: `RESULTS_AND_SOURCES.json`, `FOUR_DESIGN_COMPARISON.csv`, `MODEL_VALIDATION_DATA.csv` and the frozen run-014 evidence indexed in `TECHNICAL_MASTER_MANUSCRIPT.md`. Clinical context: [EMA Herceptin](https://www.ema.europa.eu/en/medicines/human/EPAR/herceptin). The slide wording is preserved; the spoken qualifications above prevent ‘evaluated’, ‘full HER2’ or ‘favourable’ from implying more evidence than exists.
