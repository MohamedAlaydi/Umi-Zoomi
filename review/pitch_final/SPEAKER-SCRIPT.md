# Umi Zoomi: presentation manuscript

This manuscript follows the existing deck. The slides, figures, candidate order and numerical results are unchanged.

The spoken text is in quotation marks. The preparation notes after the script are for understanding and questions, not for reading aloud. Allow about five to six minutes for the spoken text, including slide changes. Explain the choices calmly; there is no need to recite every number on screen.

## Slide 1: Four lab slots. Which four? | PDF page 1

Two presses: opening alarm, then title.

“We are Umi Zoomi. We worked on a practical question in antibody discovery: when you can generate many possible designs, but only test a few, which ones should you make?

Our answer is a working selection workflow and four antibody variants, each chosen to test a specific idea.”

## Slide 2: Why HER2-positive breast cancer? | PDF page 2

Two presses reveal the two cards.

“We started from trastuzumab, an established antibody used in HER2-positive breast cancer. That gave us a clear target, a known binding site and an experimental reference.

We asked whether changes to the antibody could preserve its recognition of HER2 while improving binding or stability. Our work is at the design stage. Laboratory and cell experiments would have to establish whether a change is useful for a future treatment.”

## Slide 3: Who it is for | PDF page 3

One press.

“The immediate user is an antibody discovery team. They need to decide what to spend their next laboratory budget on.

We wanted to give them a ranked set of sequences, the evidence behind each choice, and a record of which assumptions still need testing.”

## Slide 4: Keep the right contact | PDF page 4

One press.

“The experimental trastuzumab–HER2 structure tells us where the antibody binds. We used that as our reference and evaluated new designs against the whole HER2 protein.

This matters because an antibody can have a plausible-looking fold and still be placed at the wrong site. We checked both the sequence and the predicted interaction.”

## Slide 5: How we chose | PDF page 5

One press. Allow the three labels to appear.

“We connected three steps: learning from measurements, checking structures and choosing experiments.

We trained separate models on the organisers’ screening data and measured binding affinities. We used those models to guide new binding-loop proposals and tested their predictions on held-out data.

We then checked selected sequences with structural models and the novelty validator. Apheris, JapanFold and Nebius supported different parts of that work. The inputs, settings, code and validation records are documented in GitHub.

The final choice combines those checks with a published stability idea. We keep the reasons visible, so a laboratory result can tell us which part of the reasoning held up.”

## Slide 6: What we learned | PDF page 6

Three presses, one per finding.

“The checks changed our decisions.

A strong screening prediction did not consistently mean stronger predicted affinity. We kept those signals separate.

One docking model missed most of the known site even for trastuzumab itself. We therefore stopped treating its negative results as a reason to reject a new design. That disagreement remains a limitation.

For thermal stability, we selected two framework substitutions reported in the literature. Their benefit in our redesigned fragments is unmeasured, so we built a comparison to test them.”

## Slide 7: From proposals to tests | PDF page 7

Four presses through the funnel.

“We generated a large set of new binding-loop proposals, scored them, and applied exact sequence-distance checks to a shortlist.

The final panel combines new proposals with earlier candidates that we re-evaluated. Twenty designs are ranked; four are our first laboratory priorities, and all four pass local abguard.

We chose three binding loops and included a matched pair. That gives us different binding ideas and a direct test of the framework changes.”

## Slide 8: The four picks | PDF pages 8–11

Four presses, one per candidate.

### Pick 01

“Pick one is a binding-loop design prioritised by the affinity models. Its screening-model support is weaker, so that prediction needs an experimental test.”

### Pick 02

“Pick two has exactly the same binding loop, with two changes to the supporting structure. Comparing one and two tests whether those changes affect binding and thermal stability.”

### Pick 03

“Pick three uses a different loop and has the highest screening-model score among these four. It gives us an alternative supported by a different signal.”

### Pick 04

“Pick four uses a third loop with the same framework substitutions as pick two. It tests that idea in another sequence background.”

## Slide 9: Results | PDF page 12

Three presses reveal the cards. Keep the figure visible.

“Mol1 predicts contact with all nineteen reference-site residues for each design. That supports the proposed binding location. Because all four score equally, this figure cannot rank their affinity or establish improved performance.

The useful outcome today is a set of eligible designs with explicit reasons to test them. Binding strength and thermal stability remain unmeasured.

Adaptyv’s next measurements are binding, competition with trastuzumab and thermal stability, with the reference tested alongside our designs.”

## Slide 10: Conclusion and next steps | PDF page 13

One press.

“Those results will tell us whether to keep a design, revise it or drop it. Promising molecules would then need cell testing and specificity checks before further therapeutic development.

We have built a route from experimental data to new sequences and a documented choice of experiments. The next test is whether that process identifies a useful improvement to a HER2-binding antibody. Thank you.”

---

# Preparation notes: understand the work behind the talk

## What is the actual contribution?

The contribution is an implemented design-and-selection workflow, applied to a demanding reference antibody. Its parts are connected: original assay data, freshly trained sequence predictors, new constrained sequence proposals, structural checks against full HER2, explicit-reference novelty validation, and a ranked submission.

The control experiments matter because they affected the selection. A model was not allowed to reject designs simply because it returned a low score: we first checked whether it could reproduce the known interaction. We also evaluated a binding-energy predictor on measured historical controls. Its performance was too uncertain to let it drive the ranking.

This makes the workflow inspectable and gives the next laboratory result a clear interpretation. It does not yet demonstrate that the workflow selects better molecules than a simpler baseline. That requires prospective experimental comparison.

A useful answer to “what did you build?” is:

“We built the software and evidence trail that connect assay data to a ranked experiment list. We generated new designs, checked their eligibility and predicted interaction site, and made the uncertainty part of the selection.”

## Slide 5: what the two assay models learn

The large FACS screen labels sequences by screening class. The fitted models estimate high-class versus other-class behaviour. The signal can depend on both binding and how well the antibody is displayed, so it is not a direct measurement of affinity.

The separate affinity model was trained on 180 distinct same-background constructs with reported SPR KD values. KD describes binding affinity; lower values mean tighter binding under the assay conditions. Constructs without reportable KD were not assigned invented affinity values.

We separated train, calibration and test contact patterns for FACS. For affinity validation, groups of related sequences were held out together. These checks reduce overly easy comparisons with close relatives in the training set. They remain within the trastuzumab scaffold and do not establish generalisation to arbitrary antibody families.

The affinity models learned useful ranking signal in that retrospective task, but their errors were substantial. Their predictions for the known WT were also biased. They support choosing hypotheses; they cannot establish that a new sequence beats trastuzumab. The models are conditional on the quantified-affinity training cohort and do not provide a calibrated probability that an arbitrary design will bind.

We trained assay predictors. We did not demonstrate a newly fine-tuned foundation design model in this fresh training round.

## Slide 6: how to discuss failed controls honestly

OpenDDE recovered only 2 of the 19 reference-site residues for the trastuzumab control. That limits the meaning of its negative predictions in this particular configuration.

For Pick 02, it predicted contact with other HER2 residues and zero overlap with the reference set. That is a different predicted pose, not an experimental failure to bind. For Pick 03, the original job and the retry failed technically. There was no completed result to interpret.

Mol1 recovered the reference site for the control and all four priorities. This is a useful check of geometric plausibility. It does not prove Mol1 correctly predicts the binding performance of new designs. The second-model disagreement remains part of the evidence and is retained in the control files.

If asked whether we picked the model that looked best:

“We checked the known binder in the same setting. Mol1 recovered its site; the other docking model did not. We therefore use Mol1 for this location check and retain the disagreement as uncertainty. Neither model establishes affinity or thermal stability.”

## Slide 7: what each funnel number actually counts

- 182,595 is the number of distinct new proposals remaining after the initial WT-identity constraint.
- The assay models shortlisted 2,000 proposals.
- Of those, 1,062 passed the sequence-distance gate against the provided data.
- A smaller diverse subset was retained and selected new loops and framework variants were structurally evaluated.
- The ranked twenty combine new proposals with re-evaluated earlier designs. They are not simply the first twenty of those 1,062 novelty passes.
- Only four laboratory tests are guaranteed. The first four are all optimisation designs. The wider panel includes two intended de novo entries whose complete known-antibody database status still needs organiser confirmation.

Novelty is an entry requirement. A sufficiently different sequence can still have poor binding, expression or stability.

## What exactly are the four designs?

All four are paired heavy/light variable antibody fragments derived from trastuzumab. They are optimisation designs, not de novo designs. Their light chains are unchanged.

| Pick | H3 core | Framework | Why test it? |
|---|---|---|---|
| 01 | WGSQGFYEMG | Original | Affinity-model-led binding-loop proposal; weaker screening-model support |
| 02 | WGSQGFYEMG | S85N/R87T | Direct comparison with 01 to test the framework changes |
| 03 | WAYEGFYEMD | Original | Different loop with stronger screening-model support |
| 04 | WRSEGFYEMR | S85N/R87T | Test the same framework changes in another loop background |

Only Picks 01 and 02 form a matched pair within the first four. Pick 04 has no unchanged-framework partner among those four, so its laboratory result alone cannot isolate the effect of the framework changes.

The selection is a reasoned allocation of experiments, not a statistically validated ordering of success probabilities. Do not describe the four as proven best binders or likely S-tier designs.

## Why use the framework substitutions?

The published S85N/R87T result provides a specific, biologically motivated change to test. It was reported in full trastuzumab. We verified its residue mapping before applying it to our sequences.

The transfer is uncertain. Our binding loops and fragment format differ, and the substitutions introduce a potential glycosylation site. A benefit observed in the published system may not appear in our cell-free fragments.

Our H3-based affinity models do not model these framework substitutions. Identical model values for Picks 01 and 02 are therefore not independent predictions that the substitutions preserve binding. The comparison needs an experiment.

## Slide 12: what 19/19 does and does not show

The reference is the known trastuzumab–HER2 structure. Nineteen HER2 residues make protein heavy-atom contacts at the 4.5-angstrom cutoff used in the analysis. For each predicted complex, we count how many of those reference residues contact the antibody.

All four recover the complete reference set in Mol1. Extra predicted contacts can exist. The metric does not require identical antibody atoms, an identical pose or an identical total interface.

It is a site-recovery check. It is not measured binding strength, a competition assay, thermal stability, or a success probability. Since the values are identical, the bar chart cannot rank the four candidates. Their priority comes from the assay-model evidence and the experimental comparisons we chose.

## How the breast cancer case should be framed

HER2-positive breast cancer gives the project a relevant target and an established reference treatment. The intended long-term use is improved HER2-binding therapeutic molecules. The immediate user is a discovery team deciding which constructs to test.

We have no evidence yet of cancer-cell effects, improved safety, reduced treatment resistance or patient benefit. A change in affinity or thermal stability would not establish those outcomes by itself.

A defensible description is:

“This is early HER2 antibody design work, using trastuzumab as the reference. We have produced testable variants and a documented way of selecting them. Experimental performance will determine whether any variant deserves further development.”

## What comes next, and what each result would mean

First, make the constructs and assess expression. Then compare binding, competition and thermal stability with the same-run reference in comparable formats and conditions. Small measured differences need uncertainty and replication considered.

| Outcome | Interpretation and next action |
|---|---|
| Pick 02 is more stable than 01 and retains binding | Support for the framework changes in this specific loop and format; confirm the result |
| Pick 02 is more stable but binds worse | A trade-off, not a complete improvement; revise or deprioritise |
| Both bind but neither improves on the reference | Useful evidence about retained binding, without demonstrated therapeutic improvement |
| A design cannot be expressed or does not bind | Examine whether the sequence model, structural prediction or expression assumption failed |
| A design performs well in the challenge assays | Move to HER2-positive cell binding, specificity controls and an appropriate therapeutic format |

If more laboratory slots are available, the unchanged-framework parent of Pick 04 would help test whether the same substitutions transfer across sequence backgrounds.

The selection method itself should eventually be compared with simpler baselines at an equal testing budget. Counting measured outcomes per submitted design would test whether the workflow adds value.

## Evidence and sources

- Candidate identities and model values: TOP4_INNSENDING.csv and TOP4_RESULTATER.csv in this folder.
- Local validator receipt: TOP4_VALIDATION.json.
- Full docking comparison and technical failures: MODEL_CONTROL_NOTES.md and MODEL_CONTROL.svg.
- Clinical context: https://www.ema.europa.eu/en/medicines/human/EPAR/herceptin
- Framework study: https://doi.org/10.1080/19420862.2025.2532117

Keep detailed model statistics and source records for questions. During the talk, explain the biological question, the choice it led to and the measurement that can answer it.
