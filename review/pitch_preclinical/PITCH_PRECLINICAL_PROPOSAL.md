# Pre-clinical pitch + manuscript proposal: improving trastuzumab target engagement

Status: proposal for the team, not a decision. Built on `review/panel18plus2/PITCH_18_PLUS_2.pptx` (deck B, the team-sanctioned chassis) and the notes in `notes/`, `runs/`, `trastuzumab_epitope/`.
Clinical statements marked **[verify]** are from memory and must be checked against the primary paper before they go on a slide.

---

## 0. What the rubric rewards (task PDF p.7, field guide)

| Criterion | Weight | What it means for us |
|---|---|---|
| Judgment | 40 % | "Why you made each choice." Every pipeline gate needs a stated reason, an alternative, and evidence. |
| Execution | 20 % | Reproducible pipeline in the GitHub repo; score tables with provenance for each number. |
| User fit | 20 % | What the design is for and who needs it. |
| Path to value | 20 % | Credible route to real use, for the molecule or the method. |

Hard requirements: ranked list (up to 20), say how the top-10 / guaranteed-4 were chosen, repo link, Apheris OpenFold in the pipeline (needed for the monetary prize). No official time or slide limit; the field guide says "five minutes" informally. Novelty earns zero points (legality gate only). Model-based affinity claims are treated with suspicion. A pitch that is "we can predict structures" scores low.

So the pitch should lead with the biology and the decisions, not the models.

---

## 1. Pitch storyline (about 5 min, 7 core slides + backup)

Framing in one sentence: **we built a falsifiable, decision-logged triage of trastuzumab CDRH3 variants, so that four lab slots answer a real question about HER2 target engagement.**

"Improved target engagement" is defined operationally as the three organizer readouts, each against same-run trastuzumab: SPR binding, epitope preservation (competition), thermostability. It does **not** mean "maximum affinity" (see the caveat in section 5).

| # | Slide | Time | Source | Rubric |
|---|---|---|---|---|
| 1 | **Trastuzumab: what it did, where it stops** (NEW) | 45 s | section 2 | User fit |
| 2 | **Epitope map: 19 contacts, 4 redesignable CDRH3 positions** + the hypothesis | 35 s | deck A S1 | Judgment |
| 3 | **Pipeline funnel with the reason for each gate** (NEW) | 55 s | section 3 | Judgment, Execution |
| 4 | **Why we trust this ranker: retrospective test and the null result** | 40 s | deck B S2 | Judgment |
| 5 | **Where our models disagree** (seed noise, OpenFold3 vs Boltz-2 vs Mol-1) | 40 s | deck B S3 | Judgment |
| 6 | **The 20 and the 4 guaranteed slots** as a designed experiment, with liabilities | 50 s | deck B S4/S5 | Judgment, Execution |
| 7 | **Pre-clinical path: gates and go/no-go** (NEW) | 35 s | section 4 | Path to value, User fit |

Closing line (inside slide 7): three readouts, same-run control, frozen order, replication before any general claim, no tier claimed.

### Slides to add (new)
1. **Clinical background** (slide 1): one visual with the approval timeline, response/benefit numbers, and the four limitation classes.
2. **Pipeline funnel** (slide 3): 64 M enumerated -> 39.7 M novelty-legal -> 25.2 M "ideal" (liability-free, identity <=60 %) -> top 5,000 (FACS-model + BLOSUM) -> top 40 refolded -> 20 abguard-validated -> 4 guaranteed. Each arrow carries a 6-word reason.
3. **Pre-clinical gate roadmap** (slide 7), section 4.

### Backup slides
- Decision log table (section 3), thermostability coverage (the repo's weakest property), assay-transfer AUROCs 0.849 / 0.847 / 0.751 / 0.730 with paired interval, liability table (Isom D102-G103 and Met-107 removed in all 20; 11/20 add one), validator row-order note (the two VHHs are listed first in the output file).

### Changes to the existing deck
- Deck A shows the three retrospective bars as positive validation and omits the null result. Add "0 of 82 quantified historical variants beat the weakest WT": it is the strongest honesty signal for the Judgment criterion.
- Deck C slide 4 ranks anas_007 first for "most support for the original surface" citing OpenFold3 0-6/19, while its own slide 3 shows the WT control itself only reaches 7-13/19. Do not reuse that wording.
- Mol-1 recovery is saturated (19/19 for all 18 Fabs, 18/19 for the trastuzumab control). Do not present it as ranking evidence.
- Fix "six slots" (deck B) vs "eight slots" (deck C) for the first de novo design.

---

## 2. Background section (slide 1 + manuscript Introduction)

**What trastuzumab is.** Humanized 4D5 IgG1, FDA-approved 1998 for HER2-overexpressing metastatic breast cancer **[verify date]**. Binds HER2 domain IV near the juxtamembrane region (Cho 2003, structure 1N8Z, which is our template). HER2 is amplified or overexpressed in roughly 15-20 % of breast cancers and a subset of gastric cancers **[verify]**.

**Clinical value.**
- Added to chemotherapy in first-line metastatic disease: survival benefit (Slamon 2001 NEJM; median OS about 25 vs 20 months **[verify]**).
- Adjuvant setting: roughly halves recurrence risk (HERA, NSABP B-31/N9831, Romond 2005) **[verify HR]**.
- Residual disease after neoadjuvant therapy: KATHERINE (T-DM1) 88.3 % vs 77.0 % (already in the repo notes; it shows trastuzumab-targeted therapy keeps improving).

**Limitations in the clinic (what "better engagement" would have to address).**
1. **Primary and acquired resistance.** Single-agent response rates were modest (about 15-35 %, Cobleigh 1999, Vogel 2002 **[verify]**), and most responders progress.
2. **Epitope loss or masking.** p95HER2 lacks the extracellular domain (generated by proteolytic shedding and by alternative translation initiation at Met-611); MUC4 can mask the epitope (JIMT-1 is the standard model line).
3. **Signalling bypass.** PIK3CA mutation / PTEN loss and HER3 or IGF1R compensation make occupancy insufficient on its own.
4. **Low-density disease and heterogeneity.** HER2-low tumors respond to payload-carrying formats (T-DXd, DESTINY-Breast04) because of payload and bystander effect, not because the binder got better. A binder with better occupancy per receptor is the part that could matter here **[hypothesis]**.
5. **Toxicity.** Cardiotoxicity (LVEF decline, higher with anthracyclines) is a consequence of HER2 signalling inhibition in cardiomyocytes, not just of how tightly the antibody binds.
6. **Developability liabilities in the antibody itself.** Asp-102 isomerization in CDRH3, Asn-30 deamidation in the light chain, Trp/Met oxidation. Our abguard scan flags D102-G103 and M107.

**Why target engagement.** Trastuzumab already binds at about 0.13 nM in our SPR data (8 replicate WT records 0.0285-0.178 nM, median 0.1345 nM), so absolute affinity is not the lever by itself. Engagement that improves would mean: equal or better occupancy at low receptor density, the same epitope (so every trastuzumab-validated mechanism is preserved), and fewer chemical liabilities in the contact loop. Literature precedent that the loop has headroom: Moon 2016 (AH06, 7.4-fold affinity gain, KD about 60 pM) already in `notes/TRASTUZUMAB.md`.

**Corrections to our own notes before this goes public.**
- Met-107 oxidation: `notes/TRASTUZUMAB.md` and `trastuzumab_epitope/data/residue_literature_flags.csv` disagree (the latter: "no trastuzumab-specific oxidation report found"; Hensel 2011 is mainly about Trp oxidation, and CT-P6 saw no change). Say "flagged by the abguard liability scan; literature support is mixed", not "known oxidation site".
- p95HER2: mention both shedding and Met-611 translation initiation.
- Say explicitly that trastuzumab binds domain IV; this also justifies the 489-607 crop.
- Light-chain contacts (ten further residues) are outside what CDRH3 redesign can touch. Say "we change half of the grip".
- Do not headline "binds at 0.152 nM"; it is one of eight replicates (6.2-fold span). Quote the range and median.

---

## 3. Pipeline and the reasoning for each decision (slide 3, backup table, manuscript Methods)

Source: `pipeline_notes.md` by the pipeline reviewer. Evidence = file or run in the repo.

| # | Decision | Reason | Alternative rejected | Evidence |
|---|---|---|---|---|
| 1 | Template = trastuzumab / 1N8Z | Only crystal structure of the clinical molecule on HER2 domain IV; every other number is benchmarked against it | Pertuzumab or de novo-only | `scripts/contacts.py`: 19 contacts at 4.5 A, only W99, G103, F104, Y105 of the 10 redesignable CDRH3 positions touch HER2 |
| 2 | Redesign CDRH3 only | Organizer legality (>=3 mutations, <70 % identity); keeps framework and expression behavior | Framework mutations | abguard receipts; 20/20 valid at CDRH3 distance 3/3 |
| 3 | Free-loop generation (RFD4-Proteina + Boltz-2) | Baseline, unbiased | n/a | Run 004: 0/10 kept all four contacts; G103+F104 lost every time |
| 4 | Anchor the four contact residues | Direct response to run 004 | Keep free loop | Run 005: 10/10 contacts kept, but 0/10 clear novelty |
| 5 | Enumerate all fillings of the six free positions | Direct response to run 005; generative sampling cannot satisfy contact and novelty together | More sampling | Run 006: 20^6 = 64 M -> 39,731,174 legal -> 25,208,628 "ideal"; independent re-implementation of the enumeration |
| 6 | Rank by BLOSUM62 to parent, tie-break with our FACS model | Retrospective test on measured data | FACS model alone, random | AUROC 0.847 vs 0.751, paired +0.095 [0.061, 0.132]; reportable-KD hit rate 2.38/4 vs 2.11 vs 1.28 |
| 7 | Multi-seed refold (6 seeds) | Seed noise decides whether rankings mean anything | Single seed 42 | Seed SD 0.0147, ICC 0.567, minimum detectable delta about 0.054; 0 of 8 PASS_STRICT stay top-8 by six-seed mean |
| 8 | Cross-check with OpenFold3 / Mol-1 / OpenDDE | Prize requirement and disagreement-as-information | Single predictor | OpenFold3 recovers only 2/19 for trastuzumab itself, Mol-1 18/19; so OpenFold3 is a weak judge of this epitope |
| 9 | Controls | Prevents scoring artefacts | none | in-batch WT, byte-identical determinism controls, 30-construct SPR calibration, 7,902 shuffled VHH decoys, StaB-ddG measured controls |
| 10 | StaB-ddG + liability scan for developability | Thermostability is a judged property and our worst-covered one | Affinity only | only 11/20 candidates have a ddG; report SE |
| 11 | "Top four as a designed experiment" | A matched pair answers a question even if all four fail | Four highest scores | ranks 2/3: same four building blocks, same BLOSUM 32, 6/6 vs 0/6 contacts |
| 12 | De novo VHH on hold | OpenFold3 cannot recover the control epitope; no calibrated ranker | Ship VHH | run 011 |

**Decisions with no recorded rationale (write one line each now, or label as pragmatic choices):** Boltz-2 seed 42 and generation seeds; N=40 / TOPN=10-12; why six seeds; top-5,000 and top-40 cut sizes; `p_high >= 0.95`; Jaccard over recall.

**Open items that cost Judgment points if a juror asks:**
- Run 006 `NOTE.md` is an empty template, although the submission is drawn from run 006.
- `notes/DECISIONS.md` stops at 13:20; runs 009-014 have no entry.
- The "25.2 million" figure: the pipeline notes tie it to run 006 (25,208,628); the slide reviewer could not find a source. Link the number to the run-006 output file.

---

## 4. Pre-clinical path (slide 7, manuscript Discussion)

The panel is Fab-format; Fc-dependent mechanisms need reformatting to IgG1 at Gate 2.

| Gate | What | Readout | Go / no-go (proposal, team to agree) |
|---|---|---|---|
| 0. In silico (done) | Epitope map, enumeration, multi-seed refold, liability and ddG scans | Receipts, score tables | 20 abguard-valid designs |
| 1. Adaptyv (organizer lab) | Expression, SPR, competition vs trastuzumab, thermal stability | KD, competition, Tm vs same-run WT | Binding at or better than WT beyond the MDD; competition preserved; Tm not worse. "No material", "no fit", "inconclusive" kept distinct |
| 2. Cell biology | IgG1 reformat; flow-binding EC50; internalization; anti-proliferation; ADCC (NK/PBMC) | HER2 3+ (BT-474, SK-BR-3), HER2-low (MCF-7), trastuzumab-resistant (JIMT-1), HER2-negative control (MDA-MB-468) | Parity or better on 3+ lines; gain on low/resistant lines; no binding on negative line |
| 3. Safety and developability | hiPSC-cardiomyocyte HER2 binding and viability; DSF, SEC, HIC; immunogenicity (in silico + DC/T-cell assay) | Window between tumor and cardiomyocyte binding | No loss of safety window vs trastuzumab |
| 4. In vivo | BT-474 and JIMT-1 xenografts vs trastuzumab; PK | Tumor growth, exposure | Better than trastuzumab in JIMT-1 or equal in BT-474 with improved developability |

User fit: HER2-positive patients who relapse or have masked or low-density HER2, plus any group developing HER2 biologics who want a lower-liability CDRH3. Path to value: the **method** (decision-logged, uncertainty-aware triage with a pre-declared wet-lab design) is transferable to any template antibody; the **molecule** value is conditional on Gate 1.

Say plainly: we have zero measured results on our own designs. All affinity, contact and stability numbers for the 20 are predictions.

---

## 5. Biological caveat the jury will probably raise

More affinity is not automatically better. High-affinity binders can stall in the first cell layers of a solid tumor (binding-site barrier) and bind harder to low-HER2 normal tissue such as cardiomyocytes. That is why gate 3 includes the cardiomyocyte safety window and why our claim is "epitope-preserved, equal-or-better binding with fewer liabilities", not "tighter binder". Note also that trastuzumab does not block dimerization (pertuzumab, domain II, does); its activity comes from ADCC and signalling attenuation, so a better CDRH3 does not change that mechanism class.

---

## 6. Fix before the pitch (priority order)

1. **Freeze one ranking.** Four conflicting rankings exist (`notes/RANKED_CANDIDATES.csv`, `Rangering_begrunnet.md`, `RANKED_18_PLUS_2.csv`, `PRIZE_TOP20.csv`), plus run 014 (16:15) with a new guaranteed four of unmeasured `newML_*` sequences that include framework mutations. The team decision file (`TEAMBESLUTNING.md`) and `REGEL_OG_RANGERING.md` also give conflicting submit-this-file instructions.
2. Resolve whether de novo is "on hold" or ranked (18+2 decks vs `Rangering_begrunnet.md`).
3. Confirm the pipeline contains the **Apheris** OpenFold (prize condition).
4. Deliver the up-to-20 list and be ready to name the top 10 (PDF says 20, field guide says 10).
5. Quote the PDF prize figures (EUR 3000; 800/500/200 per track), not the draft deck's USD numbers.
6. The nine slide and wording fixes in section 1.
7. Add the missing DECISIONS.md entries and fill run 006 NOTE.md.
8. Remove or source unverified market and clinical figures.

---

## 7. Manuscript proposal

**Working title:** *A decision-logged, uncertainty-aware in silico triage of trastuzumab CDRH3 variants for HER2 target engagement, with a pre-declared wet-lab test.*

**Type / venue:** methods + registered-design paper. bioRxiv first; then mAbs or a computational-biology venue. Update with Adaptyv results as a second version.

| Section | Content | Maps to |
|---|---|---|
| Abstract | Problem, funnel, the null result, predeclared test, no efficacy claim | all |
| 1. Introduction | Trastuzumab history, resistance classes, why target engagement and developability in the contact loop (section 2) | slide 1 |
| 2. Structural basis | 1N8Z contact map; 19 residues, 4 of 10 CDRH3 positions in contact; light-chain contacts out of scope | slide 2 |
| 3. Retrospective validation of scoring | Public FACS (524,346 rows) and SPR (768 rows, 190 quantified); BLOSUM vs FACS model vs random; AUROCs with paired interval; 0 of 82 historical variants beat the weakest WT | slide 4 |
| 4. Generation and its failure modes | Runs 001-007: free loop 0/10, anchored 10/10 contacts but 0/10 novelty, enumeration 64 M -> 39.7 M -> 25.2 M | slide 3 |
| 5. Measurement noise and model disagreement | Six-seed SD 0.0147, MDD 0.054, 0/8 stable; OpenFold3 vs Boltz-2 vs Mol-1 with the WT control; determinism controls | slide 5 |
| 6. Developability | Liability scan (Isom, MetOx, Trp), StaB-ddG with SE, thermal coverage | slide 6 + backup |
| 7. Panel selection | Legality (abguard receipts), predeclared selection rule, matched-pair design for the first four slots | slide 6 |
| 8. Wet-lab plan and decision rules | Section 4 gates; no-fit / no-material / inconclusive categories; replication rule | slide 7 |
| 9. Limitations | Nothing measured; model affinity untrusted; CDRH3-only; ordering instability; record of retracted claims (epitope-footprint erosion, M107 wording, novelty reference 525,063 vs 610,109, reporting bug, abguard novelty-report skip) | all |
| 10. Data and code | Repo, receipts, hashes, run IDs | execution |

**Figures:** (1) sequence-region map and epitope colormap (already in `trastuzumab_epitope/figures/`); (2) funnel with counts; (3) retrospective benchmark bars + AUROC; (4) seed-spread plot with MDD; (5) model-disagreement table; (6) panel heatmap of contacts, ipTM, ddG, liabilities.

**Order of work:** (a) freeze the ranking and the decision log, (b) write sections 2-5 from existing run outputs (no new compute), (c) sections 1 and 8 from this document, (d) hold sections 6-7 until the panel is frozen, (e) add results when Adaptyv data return.
