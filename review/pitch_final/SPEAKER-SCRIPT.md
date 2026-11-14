# Umi Zoomi: whole-presentation manuscript

Approximately five minutes at a steady presentation pace. Read the quoted paragraphs; headings and click instructions are not spoken. This follows the existing 14-page PDF, including the four-design table on page 12 and model-validation plot on page 13. No slide changes are needed.

## Slide 1: Title | PDF 1 |0:00–0:20
Two presses: alarm, then title.

“We are Umi Zoomi. We used experimental data and protein models to redesign antibody fragments against HER2. We built a workflow that generates new sequences, checks their predicted behaviour and produces variants with specific questions to test in the laboratory.”

## Slide 2: Motivation | PDF 2 |0:20–0:45
Two presses reveal the two cards.

“Trastuzumab is an established treatment for HER2-positive breast cancer. It gives us a known target, binding site and experimental reference.

We investigated changes that might preserve HER2 recognition while improving binding or thermal stability. Our work concerns early antibody development; a benefit for patients would require much more evidence.”

## Slide 3: What the workflow is for | PDF 3 |0:45–1:00
One press.

“For a discovery team, generating sequences is only the beginning. The difficult step is connecting a proposed change to evidence and deciding what an experiment should establish. We made that connection explicit in our workflow.”

## Slide 4: What we changed | PDF 4 |1:00–1:25
One press.

“We focused on H3, the third binding loop on the antibody’s heavy chain. It helps form the surface that recognises HER2.

We redesigned its central sequence while retaining the light chain and most of the original structure. We then checked whether the predicted complexes still contacted trastuzumab’s known binding site.”

## Slide 5: Methods | PDF 5 |1:25–2:00
One press; let the labels appear.

“We trained separate models on screening data and measured affinities. Screening reflects binding and antibody display. Affinity measurements describe how tightly the interaction holds.

Those models guided new sequence proposals. Structural predictions tested their placement against full HER2, while abguard checked the sequence requirements.

We used Apheris, JapanFold and Nebius across the design and evaluation work. The code, settings and validation records are available in GitHub.”

## Slide 6: What changed our approach | PDF 6 |2:00–2:30
Three presses, one finding per card.

“The checks exposed limits. Screening and affinity predictions sometimes favoured different sequences. One docking model missed most of the known binding site for trastuzumab itself, so its negative predictions could not reliably reject new candidates.

For stability, we introduced two framework substitutions from published work. Their benefit in our redesigned fragments is still unmeasured.”

## Slide 7: Generation and evaluation | PDF 7 |2:30–2:55
Four presses through the funnel.

“We generated about 183,000 distinct loop proposals after the initial identity constraint. Of 2,000 model-shortlisted proposals, 1,062 passed the provided-data distance gate.

The ranked twenty combine new proposals with earlier designs evaluated again. The first experimental panel contains four locally validated optimisation designs. It covers three binding loops and a matched framework comparison.”

## Slide 8: Four variants | PDF 8–11 |2:55–3:35
Four presses, one per candidate.

### Pick 01

“Pick one is an affinity-model-led loop. Its screening-model support is weaker, which is a reason to test the prediction.”

### Pick 02

“Pick two has the same loop, with two framework changes. Comparing one and two tests their effect on binding and stability.”

### Pick 03

“Pick three has a different loop and the highest screening-model score among the four.”

### Pick 04

“Pick four carries the framework changes on a third loop. It explores another sequence background.”

## Slide 9: Four-design results | PDF 12 |3:35–4:05
Three presses reveal the cards. Keep the table visible.

“The screening score is about 0.16 for Pick one and 0.84 for Pick three. The affinity models favour Pick one’s loop, but disagree about whether it improves on the reference.

The framework variants inherit H3-only assay scores, so those scores do not evaluate the framework changes. Structural confidence and the shared binding-site recovery also do not establish stronger binding or improved stability.”

## Slide 10: Model validation | PDF 13 |4:05–4:30
One press.

“On 180 historical measured constructs, the affinity model reached a rank correlation of about 0.68, with related sequences held out together. Each dot compares predicted and measured affinity; the diagonal means exact agreement.

There is useful ranking signal, but substantial error, including for the reference antibody. The model supports hypotheses, not precise promises about improvement.”

## Slide 11: Conclusion and next steps | PDF 14 |4:30–5:00
One press.

“Our results are new sequences, an implemented evaluation workflow and four testable variants. Improved performance remains unproven.

Next are expression, binding, competition and thermal-stability measurements alongside trastuzumab. Promising designs would then need cell testing and specificity checks before further therapeutic development.

That is the next question for this HER2 programme: which proposed changes survive measurement?”

---

# Preparation notes: not spoken

## What H3 means

CDR-H3 is the third complementarity-determining region of the heavy variable domain. It is one of the loops that form an antibody’s binding surface. Other loops and the light chain also contribute to recognition.

The yellow loop in the presentation shows the 10-residue central H3 segment we redesigned. In the full IMGT convention used for checks, the loop also contains fixed flanking residues. We did not redesign the whole antibody or demonstrate a full therapeutic IgG.

A plain explanation is: “H3 is one of the small loops at the binding end of the antibody. We changed its sequence to explore different interactions with HER2.”

## The four variants, precisely

All four are optimisation designs derived from trastuzumab, with paired heavy and light variable domains. They are not de novo designs. Their light chains are unchanged.

| Pick | H3 core | Framework changes | Experimental question |
|---|---|---|---|
|01|WGSQGFYEMG|None|Does the affinity-model-led loop bind as predicted?|
|02|WGSQGFYEMG|S85N/R87T|What changes when we modify the framework around the same loop?|
|03|WAYEGFYEMD|None|Does the stronger screening-model signal translate into useful binding?|
|04|WRSEGFYEMR|S85N/R87T|How does another loop behave with the same framework changes?|

Picks 01 and 02 are the matched pair. Pick 04’s unchanged-framework parent is not among the first four, so its result alone cannot isolate the effect of the framework substitutions.

S85N/R87T was reported to improve stability in full trastuzumab, with retained binding/function in that published system. We verified the numbering before applying it. It creates a potential glycosylation site, and transfer to our new loops and cell-free fragment format is uncertain.

## Reading the table on PDF page 12

| Pick | Screen score | Estimated KD/WT, Ridge | Estimated KD/WT, GP | Mol1 interface PAE |
|---|---:|---:|---:|---:|
|01|0.16|2.94|0.94|3.05 Å|
|02*|0.16|2.94|0.94|3.51 Å|
|03|0.84|5.84|2.31|3.08 Å|
|04*|0.27|3.96|2.96|4.02 Å|

These are computed model outputs. There are no new measured KD or melting-temperature values for these four designs.

- Screen score is the minimum of two calibrated predictions of high screening class. It is not the probability of binding or beating trastuzumab. The minimum itself has not been established as a calibrated probability.
- KD is the dissociation constant. Lower KD means tighter affinity under the same conditions. A predicted KD/WT ratio above 1 means weaker estimated affinity than the historical reference, while below 1 means stronger estimated affinity. The small nominal GP advantage for Pick 01 is not evidence of a genuine improvement.
- Ridge is the primary model family; candidate values average bootstrap Ridge fits. GP is the secondary Gaussian-process sensitivity model. Both have substantial uncertainty and poor WT calibration.
- The asterisks mean the assay scores apply to the H3 sequence in the original framework. Framework effects are unmodelled. Identical scores for Picks 01 and 02 do not establish preserved binding after the framework change.
- Interface PAE is predicted uncertainty in relative positions at the interface. It is not observed structural error or an affinity measurement.

The table exposes conflicting evidence. It does not show that all four designs are strong binders or better than the parent.

## The historical validation plot on PDF page 13

The primary affinity model was evaluated using 180 distinct quantified-affinity constructs. Related sequences were assigned to the same held-out group. Each plotted prediction was made without fitting that sequence group.

Horizontal position is measured KD; vertical position is predicted KD. Both axes are logarithmic. A point on the diagonal would be an exact prediction. The highlighted WT point shows poor prediction near the strong-binding reference.

Rank correlation is about 0.68. That describes ordering across this measured series, not accuracy on each design or a probability of success for new proposals. Models were trained on constructs with reported KD, so their performance does not establish a reliable binder/nonbinder classifier for arbitrary sequences.

## What 19/19 means

Nineteen HER2 residues form the reference protein-contact set in the experimental trastuzumab complex at the 4.5 Å cutoff used here. Mol1 predicts contact with every residue in that set for all four variants.

This is contact recall. Extra contacts may exist, and the result does not require an identical pose or atom-by-atom interface. It supports a location hypothesis, but does not establish affinity, competition or thermal stability. The identical scores cannot rank the four.

The full second-model control is retained. OpenDDE recovered 2/19 for trastuzumab, then 15/19,0/19,not delivered and18/19 for Picks 01–04. For Pick 02 it predicted a different site; Pick 03’s original job and retry failed technically. Neither means a measured absence of binding. The weak WT control limits the use of its negatives.

## Why the funnel is a summary

182,595 distinct proposals remained after the initial identity gate. The assay models shortlisted 2,000, and 1,062 of those passed the distance gate against provided sequences. A smaller diverse subset was retained and selected new loops and framework variants were structurally evaluated.

The final twenty also include re-evaluated earlier candidates. They are not simply the first twenty of the 1,062 novelty passes. The first four are optimisation designs. Two intended de novo entries in the wider panel still need complete known-antibody database confirmation.

## The breast cancer claim we can defend

HER2-positive breast cancer provides the clinical motivation and trastuzumab the reference. The immediate contribution is early antibody-fragment design and evaluation. We have not shown cancer-cell efficacy, improved safety, reduced resistance or patient benefit.

If the challenge assays show a useful improvement, the next research stage includes HER2-positive cell binding and specificity controls, followed by development in an appropriate therapeutic format. Improved affinity or thermal stability would not by itself establish a better treatment.

The method’s benefit also needs testing: a prospective comparison with simpler selection baselines at an equal laboratory budget would show whether the workflow improves the yield of useful designs.

## Sources and questions

Candidate identities and scores: TOP4_INNSENDING.csv, TOP4_RESULTATER.csv, FOUR_DESIGN_COMPARISON.csv and RESULTS_AND_SOURCES.json. Historical validation: MODEL_VALIDATION_DATA.csv. Local validator: TOP4_VALIDATION.json. Second-model details: MODEL_CONTROL_NOTES.md.

Clinical context: https://www.ema.europa.eu/en/medicines/human/EPAR/herceptin
Framework evidence: https://doi.org/10.1080/19420862.2025.2532117

The spoken argument covers the four judging criteria: reasoning behind the designs, implemented and documented work, a defined discovery-team user, and a sequence of experiments toward possible therapeutic relevance.
