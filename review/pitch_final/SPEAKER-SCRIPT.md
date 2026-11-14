# Umi Zoomi — slide-by-slide script

About4 minutes of speech, leaving room for animation and pauses within5 minutes. English for the judges. Use Space/Right to advance, Left to go back, F for fullscreen and M to mute.

The deck keeps its original10 stops and animation reveals. There are22 forward presses after the holding screen, including the opening alarm. The fallback PDF shows13 pages, with each candidate on its own page. Only the text in quotation marks is spoken.

## Slide1 — Opening and title ·0:00–0:15
**Two presses:** opening alarm, then title. PDF page1.

“Which antibody designs deserve our four laboratory tests? We are Umi Zoomi, and that is the decision we built our project around.”

## Slide2 — Motivation: HER2-positive breast cancer ·0:15–0:45
**Two presses:** show the starting molecule, then the goal. PDF page2.

“Trastuzumab is an established antibody for HER2-positive breast cancer. We use it as a starting point for new designs that could keep recognising the right target while becoming more stable.

Our contribution today is preclinical discovery work: new molecules and a better-supported way to choose which ones to test.”

## Slide3 — Who needs this? ·0:45–1:00
**One press.** PDF page3.

“Our user is the antibody discovery team. They can propose many designs, but testing capacity is limited. Each laboratory slot needs a clear reason.”

## Slide4 — The binding site ·1:00–1:20
**One press.** PDF page4.

“We start from the experimentally known binding site. Then we ask whether our new designs still reach it when evaluated against the whole HER2 protein. Looking well folded is only part of that question.”

## Slide5 — Method: learn, check, choose ·1:20–1:50
**One press; let the three labels appear.** PDF page5.

“We learn from the organisers’ experiments, propose new sequences, and check their predicted structures. Apheris provides the design and folding tools; JapanFold and Nebius extend the checks. Published evidence gives us a separate stability hypothesis.

The workflow, inputs and validation records are documented in GitHub, so the decisions can be inspected and repeated with the same resources.”

## Slide6 — What we learned ·1:50–2:20
**Three presses, one finding per card.** PDF page6.

“Three findings changed our approach. First, a high screening score does not necessarily mean strong affinity, so we model those measurements separately.

Second, controls matter: a docking model missed the original antibody’s site, so its negative predictions could not reject new designs.

Third, stability needs its own testable idea. We explore a published change to the antibody’s supporting structure, rather than treating a confident structure as proof of heat resistance.”

## Slide7 — From proposals to a ranked panel ·2:20–2:40
**Four presses through the funnel.** PDF page7.

“We narrowed a large set of new sequence proposals using experimental-data models and exact novelty checks. The ranked proposal contains twenty designs; our first four are optimisation designs and all pass local validation.

The two exploratory de novo designs in the wider panel still need the organisers’ complete database check.”

## Slide8 — Our four choices ·2:40–3:20
**Four presses, one candidate per press.** PDF pages8–11. These labels map to the exact IDs in `TOP4_INNSENDING.csv`.

### Pick01 — binding hypothesis
“Our first choice tests our strongest new affinity hypothesis.”

### Pick02 — matched stability comparison
“The second keeps the same binding loop and adds the framework change. This matched pair lets us test what that change contributes.”

### Pick03 — balanced alternative
“The third balances the predictions learned from screening and affinity data.”

### Pick04 — another sequence family
“The fourth tests another sequence family with the stability hypothesis, so we cover more than one idea.”

## Slide9 — Results, figure and next experiment ·3:20–4:00
**Three presses reveal the result cards; the figure stays visible.** PDF page12.

“The blue bars show that Mol1 predicts the native HER2 contact site for all four designs. The red bars show why that is not the whole answer: another model disagrees, misses the original antibody’s site, and has one missing candidate result.

These are computational results, not measured binding or improved stability. The framework change may not transfer to our new fragments.

Adaptyv’s next tests are binding, competition with the original antibody, and thermal stability. Those measurements decide whether any design meets the challenge’s improvement criteria.”

## Slide10 — Close: route to value ·4:00–4:20
**One press.** PDF page13.

“Successful molecules would then need cell testing, checks for unwanted binding, and development into a suitable medicine for a breast cancer programme.

The value we deliver today is a reasoned choice of experiments: new sequences, working checks, and four clear hypotheses ready for the laboratory. Thank you.”

---

## Preparation notes — not spoken

- **Judgment40%:** Slides6 and8 explain how controls changed selection and why each candidate earns a slot.
- **Execution20%:** Slide5 points to the implemented workflow and GitHub evidence; slide7 records local validation.
- **User fit20%:** Slides2–3 connect the breast cancer context to discovery teams with limited experimental capacity.
- **Path to value20%:** Slides9–10 connect challenge assays to subsequent cell testing and medicine development.
- Contact recall is a structural prediction, not an SPR result, competition measurement or probability of success.
- The four priorities recover19/19 native contact residues in Mol1. That shared result cannot rank their affinity.
- OpenDDE recovers2/19 for WT and15/19,0/19,not delivered,18/19 for Picks01–04. Missing is not zero; negative results are inconclusive because the WT control is weak.
- The published framework substitution is S85N/R87T in the paper’s linear numbering, verified against7MN8. It introduces a glycosylation motif; transfer to our cell-free fragments is unproven.
- The3D views use the actual selected Mol1 predictions. For readability only the antibody and local HER2 binding region are drawn; the evaluation used the full607-residue HER2 sequence.
- Clinical context: https://www.ema.europa.eu/en/medicines/human/EPAR/herceptin
- Framework evidence: https://doi.org/10.1080/19420862.2025.2532117
