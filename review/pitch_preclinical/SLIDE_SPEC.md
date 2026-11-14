# Slide spec for PITCH_PRECLINICAL_DRAFT.pptx

Rules for every slide: headline is a full-sentence claim; <=40 words of body text besides tables; predicted values are labelled "predicted"; nothing is presented as measured on our own designs. Items tagged `[VERIFY]` or `[TEAM TO CONFIRM]` must appear on the slide as a small visible red tag so nobody forgets them. Speaker notes hold the spoken line and the source file for every number. Target: about 5 minutes for slides 1-7.

Source of numbers: see `review/pitch_preclinical/PITCH_PRECLINICAL_PROPOSAL.md` (sections 1-4) and the scratchpad notes `slides_notes.md`, `pipeline_notes.md`, `scoring_notes.md` (in the session scratchpad). For slides marked CARRY OVER, take the table or tiles from `review/panel18plus2/PITCH_18_PLUS_2.pptx` (deck B), using the scratchpad dump `p18.txt`, and apply only the listed edits.

---

## Slide 0 (title, not timed)
Title: "Testing better HER2 engagement, one decision at a time"
Subtitle: "Team 14 · trastuzumab CDRH3 redesign · AI x Antibodies Hackathon Oslo"
Footer: "All numbers for our designs are predictions. Nothing has been measured yet."

## Slide 1 (45 s) — "Trastuzumab transformed HER2+ breast cancer, but it still leaves patients behind"
Left column, "What it did":
- Binds HER2 domain IV near the membrane (Cho 2003, structure 1N8Z)
- Approved 1998 [VERIFY]; with chemotherapy, longer survival (Slamon 2001) [VERIFY numbers]
- Adjuvant use roughly halves recurrence [VERIFY HR]
Right column, "Where it stops" (four numbered boxes):
1. Resistance: single-agent response only about 15-35 % [VERIFY]
2. Epitope loss or masking: p95HER2 (shedding, or translation start at Met-611); MUC4
3. Bypass signalling: PIK3CA / PTEN, HER3
4. Low-density disease and the heart: HER2-low needs payload formats (T-DXd); cardiotoxicity follows HER2 signalling block
Bottom bar: "Our question: can we improve target engagement without leaving the validated epitope?"
Notes: spoken line = "Trastuzumab is validated; the open question is engagement, not a new target." Cite Cho 2003, Slamon 2001, Romond 2005, Cobleigh 1999, Vogel 2002, DESTINY-Breast04 (all to be checked).

## Slide 2 (35 s) — "Keep the epitope, change the grip, measure three things"
Left (reuse deck A slide 1 tile map, `review/pitch_her2/HER2_pitch.pptx`): CDRH3 WGGDGFYAMD; green = contacts HER2 (W99, G103, F104, Y105); grey = G100, G101, D102, A106, M107, D108. Caption: "19 HER2 contact residues; 4 of 10 redesignable CDRH3 positions touch HER2".
Right: box "Improved target engagement = three readouts vs same-run trastuzumab": SPR binding · epitope preservation (competition) · thermostability.
Footnote strip: "CDRH3 only: ten light-chain contacts stay out of reach. Trastuzumab WT in our SPR data: 8 records 0.0285-0.178 nM, median 0.1345 nM. Not 'tighter is better': tumour penetration and heart safety are tested at gate 3."
Notes: explain the 489-607 crop is domain IV.

## Slide 3 (55 s) — "Seven gates, each with a reason"
Vertical funnel, each row = count | gate | reason (<=8 words):
1. 64,000,000 | all fillings of the 6 free CDRH3 positions | free generation lost contacts or novelty (runs 004, 005)
2. 39,731,174 | pass organizer novelty rule | >2 mutations, <70 % CDRH3 identity
3. 25,208,628 | no Cys, both liabilities changed, identity <=60 % | margin below the 70 % limit; remove D102/M107 flags [TEAM TO CONFIRM source file]
4. 5,000 | top by FACS-model score plus BLOSUM62 to parent | BLOSUM beat our own model retrospectively
5. 40 | refolded with Boltz-2 on the 1N8Z template | do the four anchor contacts survive?
6. 20 | abguard-validated Fab panel | legality receipts hashed [TEAM TO CONFIRM panel formation vs run 012]
7. 4 | guaranteed lab slots | matched pair answers a question even if all fail
Side note: "Free loop: 0/10 kept all four contacts. Anchored: 10/10 kept contacts, 0/10 novel. So we enumerate."
Notes: also say that seeds, the 5,000 / 40 cut sizes and p_high >= 0.95 are pragmatic and not tuned [TEAM TO CONFIRM wording].

## Slide 4 (40 s) — "The ranker beats chance on past data, but it cannot promise a better binder"
CARRY OVER deck B slide 2 bars: random 1.28 / FACS model 2.11 / BLOSUM-to-parent 2.38, out of 4 reportable-KD hits (`historical_binding.json`).
ADD a callout (this is the null result deck B/A omit): "0 of 82 quantified historical variants beat the weakest trastuzumab record (0.185 nM)."
ADD small line: "Assay transfer AUROC: BLOSUM 0.847 vs our classifier 0.751; paired difference +0.095 (95 % interval 0.061-0.132)."
Notes: say what the bars mean (enrichment, not efficacy).

## Slide 5 (40 s) — "Where our models disagree, we treat it as uncertainty"
CARRY OVER deck B slide 3 OpenFold3 table (7/8/11 · 7/13/10 · 0/3/3 · 1/0/6 as in `OPENFOLD_RESULTS.csv`).
ADD right column, three facts:
- Trastuzumab control itself: OpenFold3 recovers only 7-13 of 19 contacts (2/19 in the broader control test), so OpenFold3 is a weak judge of this epitope
- Boltz-2 six-seed spread: SD 0.0147, minimum detectable difference about 0.054; 0 of 8 strict-pass designs stay top 8 by six-seed mean
- Mol-1 recovers 19/19 for all 18 Fabs, so it cannot rank them
REMOVE any wording that uses OpenFold3 0-6/19 as a reason to rank anas_007 first.
Notes: Apheris OpenFold is in the pipeline [TEAM TO CONFIRM it is the Apheris build].

## Slide 6 (50 s) — "Twenty designs, four slots, one decidable question"
CARRY OVER deck B slide 4/5 ranking tiles using `review/panel18plus2/TEAMBESLUTNING.md` order (anas_015, anas_007, anas_028, anas_009 as the guaranteed four; novel3 #6, novel1 #12). Edits:
- Fix the first-de-novo slot count: use "six" [TEAM TO CONFIRM six vs eight]
- Matched pair: anas_015 (6/6 contacts predicted) vs anas_009 (0/6), same BLOSUM 32. "If both bind, contact geometry did not matter; if only 015 does, it did."
- anas_007 (BLOSUM 36, 6/6, 98.2 % footprint overlap) shown without the OpenFold3-based ranking claim
Right column "Liabilities (predicted)": all 20 remove Isom D102-G103 and the Met-107 flag; 11/20 add one; top designs swap Met-107 for Trp (one oxidation flag traded for another). StaB-ddG shown with standard error; only 11 of 20 have a ddG.
Footer: "Order frozen before data. No tier claimed."

## Slide 7 (35 s) — "A pre-clinical path with go / no-go gates"
Five-column gate strip:
- Gate 0 In silico (done): receipts, 20 abguard-valid designs
- Gate 1 Adaptyv: expression, SPR, competition, Tm vs same-run WT. Go: binding at or better than WT beyond 0.054-equivalent noise, competition kept, Tm not worse
- Gate 2 Cells (IgG1 reformat): BT-474, SK-BR-3 (HER2 3+), MCF-7 (low), JIMT-1 (resistant), MDA-MB-468 (negative); binding, internalization, proliferation, ADCC
- Gate 3 Safety and developability: hiPSC-cardiomyocyte window, DSF/SEC/HIC, immunogenicity
- Gate 4 In vivo: BT-474 and JIMT-1 xenografts vs trastuzumab, PK
Mark thresholds as "proposal, team to agree".
Bottom line: "User: HER2+ patients who relapse or have low-density / masked HER2, and teams who want a lower-liability CDRH3. Value if gate 1 holds: the molecule; either way: the method."
Closing line: "Three readouts, same-run control, frozen order, replication before any general claim."

---

## Backup slides (not timed)
B1 "Decision log": table of the 12 decisions in proposal section 3 (decision | reason | rejected alternative | evidence).
B2 "What we have not justified": the six decisions with no recorded rationale (Boltz-2 seed 42 and generation seeds; N=40 / TOPN; six seeds; 5,000 and 40 cut sizes; p_high >= 0.95; Jaccard over recall) and the three open items (run 006 NOTE.md empty; DECISIONS.md stops at 13:20; 25.2 M source).
B3 "Retractions and corrections we made": epitope-footprint erosion retracted; M107 claim corrected; novelty reference 525,063 vs 610,109; reporting bug that showed another run's sequences; abguard novelty-report skipped its reference DB; 16 AntiFold variants withheld at 70.9-73.1 % identity.
B4 "Rubric map": the four criteria (Judgment 40, Execution 20, User fit 20, Path to value 20) with the slide numbers that answer each.
