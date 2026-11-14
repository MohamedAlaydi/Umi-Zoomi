# Umi Zoomi — technical manuscript for the whole presentation

This is the extended English version for understanding, editing and questions from the judges. It deliberately exceeds five minutes. The sections follow the existing presentation: PDF pages 1–14, with four candidate pages. No slides have been changed for this version.

All project numbers refer to the frozen fresh-evaluation snapshot in run 014. Historical experimental measurements, newly trained model results and proposed future experiments are identified separately. A completed computation is not a completed laboratory experiment.

## Slide 1 / PDF page 1 — What we built

“We are Umi Zoomi. We built a data-guided workflow for redesigning antibody fragments against HER2, with HER2-positive breast cancer as the clinical motivation.

Our starting point is trastuzumab. We combine its known experimental binding geometry with large screening data, smaller quantitative affinity data, sequence generation and several structural checks. The output is a ranked set of proposed experiments, with the evidence and uncertainty attached to each sequence.

The wider submission contains 20 designs: 18 optimisation entries and two intended de novo entries. Our first four laboratory priorities are all optimisation designs. They contain three different H3 loops and a matched comparison that tests two framework substitutions.

We have computational results for these new sequences. We do not yet have their measured affinities, thermal transitions or competition results. The contribution today is the implemented design and evaluation process, the new molecules it proposes, and a clear explanation of what each experiment would establish.”

## Slide 2 / PDF page 2 — Why this belongs in a breast cancer programme

“Trastuzumab gives us a clinically relevant reference: it is an established HER2-directed breast cancer treatment. That makes HER2 a meaningful place to study antibody engineering. It also sets a demanding benchmark, because we are trying to improve an already useful antibody rather than comparing ourselves with an arbitrary weak binder.” [Clinical context: EMA Herceptin](https://www.ema.europa.eu/en/medicines/human/EPAR/herceptin).

“For this hackathon, the experimental questions are HER2 binding by SPR, preservation of the trastuzumab epitope through competitive binding, and thermostability. The eventual S-, A- and B-tier assignments depend on the organisers’ experimental evaluation of those properties.

We treat those as separate endpoints. A favourable docking pose does not measure affinity. A sequence that binds in a screen has not automatically demonstrated a lower dissociation constant. A favourable binding-energy estimate does not demonstrate a higher melting temperature.

The link to breast cancer treatment is therefore a development hypothesis: can we generate a useful HER2-recognising variable region that deserves further development in a therapeutic format? Our current paired constructs contain variable domains, without the constant regions or Fc of a full therapeutic antibody. We cannot attribute the clinical actions of trastuzumab to our fragments.

An improvement in affinity or thermal stability could justify further development, but it would not by itself establish improved treatment, tumour-cell killing, safety or activity against resistant disease.”

Technical preparation: the challenge write-up says each team receives four guaranteed tests, with additional tests from placement and judge nominations. That is why the order of the twenty matters. The write-up also describes an expression step before assays; failure to express is a real experimental failure mode, even when a sequence passes the submission validator.

## Slide 3 / PDF page 3 — Who uses the workflow, and what the stages answer

“The immediate user is an antibody discovery team choosing a small experimental panel. Such a team needs to know more than which sequence has the largest model score. It needs to know what was changed, which evidence supports that change, whether the sequence is eligible, and what remains uncertain.

Our workflow separates those questions:

1. Experimental-data analysis asks what the existing assays actually measured.
2. Screening and affinity models provide different sequence-level hypotheses.
3. Generation proposes new loops under explicit sequence constraints.
4. Novelty and antibody-domain checks test submission eligibility.
5. Cofolding and geometry analysis test whether a proposed complex is compatible with the intended binding site.
6. Controls test whether a model deserves influence over ranking.
7. Panel selection balances the remaining hypotheses within the available laboratory budget.

Each stage has a narrower job than ‘predict whether the antibody is good’. That lets us retain useful evidence without turning every score into a claim about clinical performance.”

The resources have different roles. Apheris supplied the hackathon design/model environment, including the RFD4-Proteina branch and local model images. JapanFold supplied the remote Mol1 and OpenDDE predictions used in the fresh evaluation. Local GPU resources supported Boltz-2 and binding-ddG work. The new assay predictors and mutation generator were fitted or implemented in our own scripts. Adaptyv is the planned experimental evaluator; it has not supplied new laboratory measurements for our four candidates. AMASS should be credited only for project work documented in its own run records, not as a source of these affinity labels or final wet-lab results.

## Slide 4 / PDF page 4 — Exactly what H3 is, and exactly what we changed

“H3 means CDR-H3: the third complementarity-determining region of the heavy variable domain. It is one of the loops at the antigen-binding surface. Its sequence and shape can influence recognition, alongside the other heavy-chain loops and the light chain.

We focused our optimisation on a ten-residue H3 core. In trastuzumab, that core is `WGGDGFYAMD`. The full H3 used for the IMGT-based novelty checks is thirteen residues, `SRWGGDGFYAMDY`, because it includes fixed flanking residues.

That distinction matters. The learning models use ten core positions; the final identity check uses the full numbered loop. We must not interchange those denominators when quoting percentage identity.

Each of the four prioritised designs has a 120-residue heavy variable domain and the same 107-residue light variable domain. The combined length is 227 residues. The two framework-modified designs additionally carry S85N and R87T in the heavy domain. Otherwise, our main optimisation preserves the trastuzumab variable-region background.

The ten redesigned positions correspond to linear heavy-domain positions 99 through 108. We identified four original contact-associated positions within that core: W at core position 1, G at position 5, F at position 6 and Y at position 7. We gave these positions a lower mutation sampling weight, but we did not freeze them. Preserving a binding-site hypothesis while allowing some contact residues to change was the intended compromise between conservative redesign and the challenge’s novelty requirements.”

### What the presentation colours actually encode

| Visual element | Meaning in this deck | What it does not encode |
|---|---|---|
| Blue molecular backbone | Heavy variable domain outside the highlighted loop | Binding strength or confidence |
| Pale/cream molecular backbone | Light variable domain | Lower confidence |
| Green molecular backbone | Displayed HER2 target region | A favourable score |
| Yellow molecular loop | The ten positions we redesigned | Only conserved residues, or a pLDDT scale |
| Yellow letter tiles | Original amino acid retained at one of the four selected contact-associated core positions | Experimental binding or recovered HER2 contacts |
| Red/blue/yellow/green machinery and decorations | Presentation styling | Molecular properties |

“The colours identify molecular components and highlight the redesigned loop. They are not a heat map of affinity, PAE, pLDDT or molecular matching. In the letter strip, yellow has the more specific meaning of retaining an original residue at a selected contact position.”

The 3D candidate views use backbone coordinates from the actual selected Mol1 predictions. Their smooth tubes simplify the backbone, omit side-chain detail and use a cropped target view for readability. These are predicted structures, not new experimental structures. HER2 residues 489–607 are displayed; the structural evaluation used the complete 607-residue target construct. “Full HER2” in earlier deck wording refers to that target construct, not the entire receptor in its membrane and cellular environment.

## Slide 5 / PDF page 5 — Data, learning models and generation

### 5A. Experimental-data audit

“We began with the original assay tables rather than trusting the earlier candidate ranking. The FACS dataset contains 524,346 unique ten-residue H3 cores: 172,149 in the high class, 190,011 in the medium class and 162,186 in the low class.

FACS is a screening phenotype. In this setting, its signal can reflect both binding and antibody display. We therefore trained it to predict high screening class, not to predict a numerical affinity or a melting temperature.

The SPR table is much smaller: 768 rows representing 754 distinct full variable-domain constructs. Of those rows, 190 have quantified binding values, 460 have no reportable KD, 104 are inconclusive and 14 have no reported result.

Those categories are not interchangeable. A missing or unreportable numerical KD is not a licence to invent a weak affinity, and it is not automatically a proven nonbinder. For quantitative regression we retained comparable, same-background ten-core constructs with reported KD, then aggregated repeated observations by full construct. That produced 180 unique constructs.

The historical WT observations have a median KD of 0.1345 nanomolar, or 134.5 picomolar. The eight available values range from about 0.0285 to 0.178 nanomolar. We use their median as a numerical reference, while recognising that these historical observations are not a replacement for a matched WT measured in the new experimental batch.”

| Data quantity | Verified count | Role |
|---|---:|---|
| Unique FACS cores | 524,346 | High-class screening models |
| FACS cores after removal of SPR overlaps | 524,309 | Leakage-reduced FACS modelling set |
| SPR rows / unique full constructs | 768 / 754 | Assay audit and eligibility references |
| Quantified SPR rows | 190 | Starting pool for numerical affinity analysis |
| Comparable aggregated quantified constructs | 180 | Affinity training and grouped validation |
| Historical WT measurements | 8 | Historical normalisation, median 0.1345 nM |
| Unique full H3 loops in the provided-data reference | 525,063 | Exact sequence-distance checks |

“One useful reality check came from the historical assay audit. Among 82 quantified constructs in the selected FACS-unseen, same-background cohort at four to six edits from WT, none had a lower KD than the WT reference. That remained true across the available historical WT baseline range. This does not tell us the success probability of our new proposals, because the cohort was selected and numerical reporting is conditional. It does show why beating this reference should be treated as difficult.”

### 5B. Screening models: split design, fitting and calibration

“For FACS, we removed all 37 core sequences overlapping the SPR table before fitting. We then grouped sequences by the amino-acid pattern at the four original contact-associated positions. There are 10,329 such patterns.

We hashed those patterns with seed 271828 into nominal 70%, 15% and 15% training, calibration and test partitions. Because whole patterns are assigned together, the row counts are not exactly those percentages: 375,230 training rows, 83,098 calibration rows and 65,981 test rows. No contact-pattern group occurs in more than one partition.

We fitted two deliberately different predictors. The first is a categorical histogram gradient-boosting classifier. It can learn interactions between positions. The second is logistic regression on a 200-dimensional one-hot representation: ten positions multiplied by twenty possible amino acids. It provides a simpler, more additive comparison.

Both predict high class versus the combined medium and low classes. We calibrated each model’s output with a scalar Platt calibration fitted on the separate calibration partition.”

| Component | Actual configuration |
|---|---|
| Categorical GBM | 120 iterations; maximum 15 leaves; minimum 40 samples per leaf; L2 regularisation 0.5; all ten input positions categorical |
| Logistic regression | 200 one-hot features; C = 1; L-BFGS; maximum 500 iterations |
| Platt calibration | Logistic model of the clipped raw logit; C = 100; maximum 300 iterations |
| Reproducibility | Seed 271828; source hashes and protocol saved before fitting |

| Held-out FACS metric | Categorical GBM | One-hot logistic |
|---|---:|---:|
| ROC AUC | 0.9713 | 0.9255 |
| Brier score, lower is better | 0.0639 | 0.1069 |
| Test sequences | 65,981 | 65,981 |
| High-class sequences in test set | 28,283 | 28,283 |
| Score versus measured log KD, external quantified cohort: Spearman | −0.1763 | −0.0713 |

“The high AUC means the model separates historical high-class examples from the other classes well under this split. It is not 97% accuracy, a 97% chance that a new sequence binds, or a 97% chance of beating trastuzumab.

The external affinity correlations are weak. That is direct evidence that strong screening prediction is not equivalent to accurate affinity prediction.

For candidate generation we used the minimum of the two calibrated high-class scores. This penalises proposals supported by only one screening model. However, taking the minimum creates a new heuristic score; we have not established that the minimum itself is a calibrated probability.

This split is stronger than a simple random row split for testing new contact patterns, but it still concerns one antibody background. It does not establish transfer to arbitrary antibodies or VHHs.”

The candidate screening score is:

`screen(x) = min[p_GBM,calibrated(high | x), p_logistic,calibrated(high | x)]`.

### 5C. Quantitative affinity: a separate model and a different validation problem

“For the affinity model, the target is the base-ten logarithm of KD relative to the historical WT median:

`y = log10(KD / 0.1345 nM)`.

A value of zero corresponds to the historical WT KD; a positive value corresponds to weaker affinity; a negative value corresponds to tighter affinity. A difference of one log unit is a tenfold KD difference.

The primary model is Ridge regression with alpha 10. Its 201 features are the 200 one-hot core features plus the fraction of core residues changed from WT. Ridge regularisation limits coefficient size in a small, correlated dataset.

We did not validate by independently scattering close sequence neighbours across folds. We linked constructs whose cores are at edit distance two or less, formed connected components, and kept each component together. The 180 constructs form 126 groups. Five-fold GroupKFold produces an out-of-fold prediction for every construct without fitting that construct’s sequence group.

The primary model reaches a Spearman rank correlation of 0.675 and a mean squared log error of 0.651. This is useful evidence that it captures some ordering across the measured affinity range. The corresponding root mean squared error is 0.807 log units, so individual numerical predictions remain rough.

We also fitted a Gaussian-process model as a secondary sensitivity analysis using the same sequence groups. It reaches a similar rank correlation, 0.673, and mean squared log error of 0.591. Agreement between two model families is informative, but it does not remove the selection bias or the small-data problem.”

| Affinity validation | Primary Ridge | Secondary GP |
|---|---:|---:|
| Unique measured constructs | 180 | 180 |
| Sequence groups / folds | 126 / 5 | 126 / 5 |
| Spearman rank correlation | 0.6752 | 0.6727 |
| MSE in log10 KD ratio | 0.6505 | 0.5911 |
| RMSE in log10 KD ratio | 0.8065 | 0.7688 |
| 95th percentile of absolute out-of-fold log error | 1.7622 | 1.6884 |
| Multiplicative magnitude corresponding to that percentile | 57.8-fold | 48.8-fold |

“Those last values describe observed historical validation errors. They are not guaranteed confidence intervals for new designs. They explain why a nominal six-percent advantage in a new model estimate cannot establish a genuine improvement.

The descriptive constant-mean MSE is 1.054. In our saved implementation, that constant uses the overall cohort mean; it is not a separately fitted training-fold baseline. We should therefore describe it as context for the error scale, not as a rigorous prospective comparison against every simpler model.

For proposal scoring, we fitted sixteen bootstrap Ridge models. Their average prediction gives a point estimate, and the spread between those fitted models provides a parameter-sensitivity penalty. This spread is not the full biological prediction error. It does not include every source of assay variation, model misspecification or failure to express.

The GP uses a constant-amplitude RBF kernel plus white noise, with hyperparameters fitted inside each training fold. The final fitted kernel has amplitude approximately 0.988 squared, length scale 2.45 and white-noise level 0.144 on its normalised response scale. Its posterior standard deviation depends on that assumed model; it is not experimental confidence.

The GP analysis followed the frozen primary protocol. It is a sensitivity analysis using the same historical validation cohort, not a new untouched test after all model choices.”

Important terminology: we retrained these assay predictors from the original data. We did not fine-tune Mol1, OpenDDE, Boltz-2 or the RFD4 foundation models during this fresh rebuild.

## Slide 6 / PDF page 6 — What the controls changed

### 6A. We rebuilt the candidate evidence

“The audit reconstructed candidate sequences from the earlier generation inputs rather than inheriting the old ranking. After deduplication by full heavy/light sequence, the raw pool contained 162 constructs: 98 paired designs and 64 VHHs.

An explicit-reference local validation retained 127: 64 paired and 63 VHH. The other 35 comprised 34 novelty failures and one VHH with an odd cysteine count. This meant some earlier attractive-looking results were not eligible under our conservative interpretation of the sequence rules.

We also corrected several evaluation weaknesses. Same-length sequences can still have a small Levenshtein distance after a shifted segment, so Hamming distance was not a sufficient replacement for edit distance. We corrected a confidence-bound direction used by an older screening comparison. We made structure collection reject ambiguous run or seed selection rather than taking the first matching file. And we explicitly checked chain identities and PAE token mapping.

These changes improve the reliability of the evidence. They do not prove that the new molecules outperform the old ones experimentally.”

Audit detail: the edit-distance correction did not change the nearest-distance value for the 98 raw paired constructs in this audit. Eighteen earlier loose passes failed the stricter full-H3 numerical policy; those failures should not all be attributed to the Hamming correction. The corrected noninferiority-style check concerns a model-score margin of −0.03, not clinical or experimental noninferiority. Geometry, regression and evidence suites recorded 23 passing tests across the relevant suites.

### 6B. A docking model needs a matched reference control

“The new remote cofolds use the 607-residue HER2 target construct, not only an isolated short patch. For the primary Mol1 protocol we used one sample with seed 271828 and supplied no template or hotspot restraints.

The frozen scoring table contains 103 usable model–target rows: 87 Mol1 and 16 OpenDDE. These are repeated model evaluations across candidates and controls, not 103 distinct antibody designs and not 103 laboratory measurements. Not every intended job was included at the freeze, so missing outputs stay missing.

For the known trastuzumab reference, Mol1 recovered all nineteen reference contact residues. OpenDDE recovered only two of nineteen under its matched full-target protocol. That is a crucial control: when a model misses the known reference site, a negative prediction for a new design cannot be treated as a reliable binding veto.

We still retain OpenDDE’s positive and conflicting predictions. We use them to expose uncertainty, rather than choosing whichever output looks most favourable.”

The declared fresh plan covered 104 Mol1 target evaluations and 25 OpenDDE evaluations. The actual OpenDDE target list contains 17 new-sequence/framework experiment targets, WT, three historical controls and four VHHs. A free-text selection description says five VHHs, but the enumerated 25-target list contains four; the target list is authoritative. Twenty-six intended model–target evaluations were not part of the final 103-row remote snapshot. This is a coverage limitation, not a favourable result.

### 6C. Local Boltz-2 is a supplementary check with different conditioning

“We ran a smaller local Boltz-2 panel using the same 607-residue target and seed. These runs used an antigen-only template, no antibody template and no MSA. That differs from the remote sequence-only protocol, so the outputs are not interchangeable replicates.”

| Local Boltz-2 construct | Global ipTM | Reference contacts recovered at 4.5 Å |
|---|---:|---:|
| Trastuzumab WT | 0.283 | 0/19 |
| Pick 01 | 0.325 | 0/19 |
| Pick 02 | 0.495 | 19/19 |
| Intended de novo VHH `3e17…` | 0.329 | 0/19 |
| Intended de novo VHH `66a1…` | 0.699 | 0/19 |

“The highest ipTM in that small panel belongs to a VHH that does not recover the reference epitope. That illustrates why a global confidence number cannot replace a site-specific question. The WT also misses the site, so we do not treat the negative results as decisive. Pick 02’s positive result is additional pose support, with the protocol differences kept explicit.”

Local Boltz-2 interface PAE was unavailable in the frozen local evidence; it is not silently filled from another model. Initial container/cache/template errors were technical run failures, not biological observations. Older project multi-seed results belong to their original protocols; the fresh primary run is not a six-seed robustness study.

### 6D. Binding-ddG was tested against controls before being trusted

“We also ran a native-pose StaB-ddG analysis for 76 variants: 64 existing paired candidates and twelve measured historical controls. The setup uses the variable-domain pair against the experimentally resolved target, with twenty Monte Carlo samples, seed 271828 and 0.1 Å coordinate noise.

The output is predicted binding free-energy change in kcal/mol, mutant minus WT; a negative value suggests stronger binding within this model’s convention. That is different from a folding-stability or melting-temperature prediction.

Across the twelve controls, the rank correlation was about 0.322, with a construct-bootstrap 95% interval from −0.350 to 0.830. That is too uncertain to justify making it a major ranker. We kept it informational.

The Monte Carlo standard error describes sampling variation within this computation. It does not measure the model’s predictive error against an experiment. The newly generated seventeen-target experiment branch was not included in the executed StaB-ddG batch, so we do not assign those new candidates an invented ddG score.”

### 6E. The framework hypothesis is specific, but transfer remains untested

“To address the stability objective, we introduced S85N and R87T in two prioritised heavy-chain frameworks. Published work on full trastuzumab reported increased thermal stability with retained binding/function for this substitution pair. We verified the residue identities against the paper’s 7MN8 heavy-chain sequence before applying the changes.” [Ng et al., mAbs, 2025](https://doi.org/10.1080/19420862.2025.2532117).

“The numbering is important: these are the paper’s linear heavy-variable-domain positions 85 and 87, not IMGT positions 85 and 87. The combined change also introduces an NLT potential glycosylation sequon. The expression system and construct format could therefore affect what transfers.

We have not measured the effect in our new H3 backgrounds or in the challenge’s cell-free fragment system. The honest claim is a literature-informed stability experiment, not a predicted or measured Tm gain.

Our assay models only see H3. Consequently, a framework variant receives the same assay scores as its parent loop. Those identical values mean that the framework is outside the model’s input; they do not demonstrate that binding was preserved.”

## Slide 7 / PDF page 7 — How the new sequences were generated and selected

### 7A. Mutation proposals

“The fresh generator starts from seven parent cores: WT plus six quantified tight-binding historical parents. They are `WGGDGFYAMD`, `WGSQGFYAYD`, `WGSDGWYAMD`, `WGGQGFYAMD`, `WGGSGPYLFD`, `WGGEGFYAMD` and `WGGDGFYLMD`.

Using seed 271828, we made 200,000 mutation attempts. Each attempt samples one parent and changes three to six distinct positions. That mutation count is relative to the sampled parent, not necessarily relative to WT.

The substitution alphabet excludes cysteine. The four original contact-associated positions receive weight 0.4 each, versus weight 1 for each of the other six positions. They remain mutable. We did not force removal of a particular Asp or Met simply because it appeared in the old design logic.

The initial WT-core identity gate and deduplication leave 182,595 distinct suggestions. We score those with the screening ensemble and the bootstrap affinity ensemble. We take a union of the top 1,000 by screening agreement and the top 1,000 by the lower-affinity-risk proposal score; this produces 2,000 shortlisted cores.”

For proposal generation, the affinity risk heuristic is the bootstrap mean predicted log KD plus one bootstrap parameter standard deviation. This is a cautious search penalty, not a one-sigma biological prediction bound.

### 7B. Exact eligibility and diversity gates

“We check the shortlist against 525,063 unique full H3 reference loops reconstructed from the supplied data. Our optimisation policy requires full H3 identity below 70% to WT and a minimum Levenshtein distance of at least three from every provided reference loop.

We used this conservative policy because the detailed write-up is stricter than the summary slides: the write-up says under 70% identity and strictly more than two mutations; the slides use less restrictive boundary wording. We apply the stricter interpretation, while leaving final acceptance to the official validator.

Of the 2,000 shortlisted loops, 1,062 pass the exact provided-data distance gate. That is 53.1% of the shortlist, not 53.1% of all 182,595 proposals.

We then use Pareto fronts to retain candidates with complementary screening and affinity scores, plus sequence diversity. Ordinary generation diversity requires at least three edits between retained loops. The first saved diverse list contains 68 proposals. The intended cap was 64; the first implementation finished a Pareto front before stopping and overshot that cap. We corrected the cap in the code while keeping the original 68-proposal output as the audit record.

From that output, we chose twelve new H3s: four led by screening, four by predicted affinity and four balancing both. We then added four framework variants and a framework-modified WT control, creating a seventeen-target structure experiment.”

| Generation stage | Count | Meaning |
|---|---:|---|
| Mutation attempts | 200,000 | Sampling operations, including duplicates |
| Unique suggestions after the initial WT-core identity gate | 182,595 | Assay-model search pool |
| Assay-shortlisted suggestions | 2,000 | Union of screen-led and affinity-led proposals |
| Exact provided-data distance passes | 1,062 | Passes within the shortlist |
| Saved diverse proposals | 68 | First run; cap overshoot retained transparently |
| New H3s chosen for structural experiment | 12 | Four screen-led, four affinity-led, four balanced |
| Additional framework candidates / WT framework control | 4 / 1 | Seventeen experiment targets overall |

“The final twenty are not simply the first twenty of those 1,062 passes. They combine the new branch with earlier sequences that were evaluated again.”

### 7C. De novo means more than a sequence not appearing in our own data

“The wider panel includes two intended de novo VHHs from the RFD4 branch. These need an additional novelty test: less than 70% identity to known antibodies under the organisers’ database check.

We expanded our local comparison to 48 antibody entities obtained through RCSB searches and extracted their variable domains before comparing identity. This avoids diluting a similarity calculation by comparing a short VHH with an entire heavy chain containing constant domains. We also used two identity calculations conservatively rather than relying on a single favourable alignment.

The two selected VHHs have maximum conservative identity values of approximately 69.77% and 67.41% in that reference collection. The first is close to the 70% boundary. Passing this local comparison does not prove a pass against Adaptyv’s complete antibody database.

That uncertainty is why their status remains provisional. The first four priorities are all optimisation designs, where the evidence and local eligibility checks are stronger.”

| Intended de novo entry | Maximum identity in checked reference set | Mol1 reference contact recovery | Mol1 interface PAE |
|---|---:|---:|---:|
| `vhh_66a1ab11c27f` | 69.77% | 9/19 | 13.83 Å |
| `vhh_3e17aea82221` | 67.41% | 8/19 | 24.32 Å |

Neither VHH has the structural support of the first four paired designs in this snapshot. Both still require the full official novelty check; neither has measured binding, competition or thermal results. They occupy positions 15 and 16 in the selected twenty, so they will only be tested if the team receives a sufficiently large allocation.

## How the structural evaluation actually works — expands Slides 5–7

“Our structural reference is the experimental trastuzumab–HER2 complex, PDB 1N8Z. The queried target construct contains 607 residues. The native structure resolves 581 of them; 26 target residues have no native coordinates. We distinguish a missing native coordinate from a residue absent from the target sequence.

The geometry code first identifies heavy, light and target chains by sequence. It does not assume that every model uses the same chain letters. It reads protein heavy atoms with valid occupancies and handles alternate locations consistently.

We define a target contact residue by whether any of its heavy atoms lies within the chosen distance of an antibody heavy atom. We examine 4.0, 4.5 and 5.0 Å cutoffs. The native reference sets contain seventeen, nineteen and nineteen target residues respectively.

At 4.5 Å, the nineteen target positions are 557, 558, 560, 561, 569, 570, 571, 572, 573, 579, 591, 593, 596, 598, 600, 602, 603, 604 and 605.

For a predicted contact set P and reference set R, contact recall is the fraction of R recovered by P. Jaccard overlap divides the common contacts by the union of both sets. Recall asks whether the reference site is covered; Jaccard also penalises additional contacts. A prediction can therefore recover nineteen out of nineteen while still placing extra contacts elsewhere.

We separately report predicted contacts at positions unresolved in the native structure, because those positions cannot be treated as observed native negatives. All four having 19/19 is a site-recovery result. It does not mean nineteen measured bonds, an identical interface, a perfect structure or a perfect antibody.”

Formulas:

`contact recall = |P ∩ R| / |R|`

`contact Jaccard = |P ∩ R| / |P ∪ R|`

“We also map the PAE sidecar to the actual written structure token order and verify its dimensions. For the paired 120 + 107 + 607 construct, that means 834 residue tokens. A PAE matrix indexed using the wrong chain order could produce plausible-looking but incorrect interface numbers.

Our reported interface PAE is the mean, symmetrised PAE across unique contacting residue pairs. It describes the model’s predicted uncertainty in relative positions. It is neither measured structural error nor an affinity value.

H3 pLDDT describes predicted local confidence around the loop. We report regional means and lower-decile values rather than relying only on global confidence. Experimental B-factors from the native structure are not interpreted as pLDDT.

We compute target-aligned geometry at three scales: all 581 observed target C-alpha positions; the 109 observed positions in the binding region; and the nineteen-residue native epitope. Alignment uses a proper Kabsch rotation, with reflections excluded. We count severe cross-interface atom overlaps below 2 Å, and ask whether the candidate’s predicted placement would overlap native WT after target alignment.

Such an overlap supports a competition hypothesis. It does not replace the competition experiment: proteins are flexible, the assay has its own conditions, and a static protein-only model does not reproduce all target glycans or the cell surface.”

One additional limitation: earlier cropped-target protocols and the fresh protocol differ in both target context and seed. Any difference cannot be attributed solely to adding target context. Multiple models can also share learned structural preferences; cross-model agreement is not equivalent to independent experimental replication.

## Slides 8 / PDF pages 8–11 — The four variants in detail

### The panel-selection logic

“For the optimisation candidates, our internal structural support gate required local abguard passage, Mol1 contact recall at least 0.8, interface PAE at most 10 Å and at most five counted interface atom clashes below 2 Å. These are our heuristic thresholds, not official hackathon cutoffs or universally validated biological criteria.

We then considered the more pessimistic of the Ridge and GP log-affinity estimates. The wider allocation aimed to include affinity-led hypotheses, screening-balanced proposals, high-screening hedges and up to two framework experiments. Ordinary panel diversity required at least two H3 edits. A same-H3 framework pair was deliberately allowed so we could test the framework change directly.

This is an adaptive research selection rule, informed by the outputs we inspected. It has not been prospectively shown to maximise the number of successful molecules.”

### Pick 01 — affinity-led loop A, original framework

ID: `newML_b973259db36d`.

“Pick one changes the ten-residue core from `WGGDGFYAMD` to `WGSQGFYEMG`. Its full H3 is `SRWGSQGFYEMGY`. It has four core substitutions relative to WT, while retaining the four highlighted original contact-associated residue identities.

This is our strongest affinity-led hypothesis among the first four. The bootstrap Ridge estimate corresponds to KD 2.94 times the historical WT KD. The secondary GP estimate corresponds to 0.94 times WT. In absolute terms, those estimates are approximately 0.395 and 0.126 nanomolar, but they are predictions with substantial error.

The two models therefore disagree on the key question of beating WT. The GP’s nominal six-percent improvement is far smaller than the model’s historical error and the variation in the historical reference values. We cannot present it as demonstrated improvement.

The screening agreement score is relatively low, 0.162. This is an important weakness: the affinity-led proposal does not receive strong support from both screening models.

Mol1 recovers nineteen of nineteen reference contacts, with interface PAE 3.05 Å and H3 mean pLDDT 88.64. OpenDDE recovers fifteen of nineteen with PAE 5.14 Å. Local Boltz-2 does not recover the reference site in this configuration, but its WT control also fails. Overall, this is a plausible geometry hypothesis with conflicting assay evidence, which is precisely why an experiment is useful.”

### Pick 02 — loop A with the framework substitutions

ID: `newML_b973259db36d_FW85N87T`.

“Pick two uses the identical H3 and light chain as Pick one, but introduces heavy-domain S85N and R87T. The one-versus-two comparison is the cleanest causal question in the panel: what changes when we alter those two framework residues on the same loop background?

The screening and affinity values are identical to Pick one’s because the models only take H3 as input. They describe the parent loop on the training framework and do not predict the effect of our framework mutations.

Mol1 still recovers nineteen of nineteen contacts, with interface PAE 3.51 Å and H3 pLDDT 88.56. OpenDDE instead places the antibody at a different region: zero of the nineteen reference contacts and interface PAE 23.99 Å. That result still has contacts with other target residues; zero reference-site recovery is not zero molecular contact.

Local Boltz-2 recovers nineteen of nineteen for this variant. We therefore have structural disagreement, not a unanimous model consensus and not a measured loss of binding. The laboratory comparison must establish binding, competition, expression and thermal behaviour. The published stability result is the reason to test this variant, not a substitute for that measurement.”

### Pick 03 — screening-led loop B, original framework

ID: `newML_a7acfcc8dce3`.

“Pick three uses core `WAYEGFYEMD` and full H3 `SRWAYEGFYEMDY`. It also has four core substitutions relative to WT and retains the highlighted original contact-associated residues.

Its screening agreement is 0.836, the highest of our four priorities. That gives it a different rationale from Pick one: the two screening models provide substantially stronger joint support.

The quantitative affinity estimates are less favourable: Ridge predicts KD 5.84 times WT and GP 2.31 times WT. On the historical scale those correspond to approximately 0.786 and 0.311 nanomolar. Both predict weaker affinity than the historical WT reference.

Mol1 again recovers nineteen of nineteen reference contacts, interface PAE 3.08 Å and H3 pLDDT 88.93. The OpenDDE job and its retry failed technically, so there is no valid second-model result for this design. We display that as missing, not zero and not a favourable prediction.

The question is whether strong screening support translates into an expressible, measurable HER2 binder in the new assay. It also provides a useful test of how screening and quantitative affinity models disagree.”

### Pick 04 — loop C with the framework substitutions

ID: `newML_5753ea077281_FW85N87T`.

“Pick four uses core `WRSEGFYEMR`, full H3 `SRWRSEGFYEMRY`, and the same two framework substitutions as Pick two. The core differs from WT at five positions; across the full heavy domain there are seven substitutions when we include the two framework edits.

The screening agreement is 0.272. The Ridge and GP estimates correspond to KD 3.96 and 2.96 times WT, or approximately 0.532 and 0.398 nanomolar on the historical scale. Neither estimate supports stronger affinity than WT.

Mol1 recovers nineteen of nineteen reference contacts, with interface PAE 4.02 Å and H3 pLDDT 89.07. OpenDDE recovers eighteen of nineteen with interface PAE 4.40 Å. This gives relatively consistent site support across those two models.

This design asks whether the framework hypothesis transfers to another H3 background. Its unmodified-framework parent is not one of the first four. Consequently, Pick four alone cannot isolate the framework effect; that comparison would require its matched parent in an expanded panel.”

## Slide 9 / PDF page 12 — The real quantitative results

“This table is the result comparison we want the panel to see. All entries are model outputs. The columns answer different questions, and they do not collapse into a demonstrated therapeutic score.”

| Pick | Core | Changes in heavy domain versus WT | Screen agreement | Predicted KD / WT: Ridge | Predicted KD / WT: GP | Mol1 interface PAE | Mol1 H3 pLDDT |
|---|---|---:|---:|---:|---:|---:|---:|
| 01 | WGSQGFYEMG | 4 | 0.162 | 2.94× | 0.94× | 3.05 Å | 88.64 |
| 02* | WGSQGFYEMG | 6 | 0.162* | 2.94×* | 0.94×* | 3.51 Å | 88.56 |
| 03 | WAYEGFYEMD | 4 | 0.836 | 5.84× | 2.31× | 3.08 Å | 88.93 |
| 04* | WRSEGFYEMR | 7 | 0.272* | 3.96×* | 2.96×* | 4.02 Å | 89.07 |

`*` H3-only assay estimates: framework effects are not modelled. Ratios use the historical 0.1345 nM WT median. Lower KD is tighter binding; a ratio above one means weaker estimated affinity than this historical reference.

| Reference-site recovery at 4.5 Å | WT | Pick 01 | Pick 02 | Pick 03 | Pick 04 |
|---|---:|---:|---:|---:|---:|
| Mol1 | 19/19 | 19/19 | 19/19 | 19/19 | 19/19 |
| OpenDDE | 2/19 | 15/19 | 0/19 | Missing: technical failure | 18/19 |

“There are three main findings. First, all four retain the intended site in the primary Mol1 prediction, but that shared score cannot rank them. Second, screening and affinity predictions favour different loops. Third, the framework intervention is outside the assay models and requires a direct experiment.

These results support a panel of testable hypotheses. They do not support saying that we have four improved antibodies, four high-affinity binders, or four S-tier designs.”

The ratios are not normalised to the model’s own predicted WT. That would be a different quantity. The actual table uses measured historical WT KD as the denominator. The primary bootstrap model predicts WT itself substantially worse than its observed value, which is why the validation plot matters.

## Slide 10 / PDF page 13 — How to explain the validation figure properly

“The validation plot contains 180 historical measured constructs. The horizontal axis is measured KD and the vertical axis is the primary model’s out-of-fold predicted KD. Both are logarithmic. On the diagonal, the numerical prediction would be exact; above it, the model predicts weaker affinity than was measured; below it, the model predicts tighter affinity.

Every point was predicted with its sequence-connected group excluded from fitting. The overall rank correlation is about 0.68, which means the model captures a substantial part of the ordering across this dataset. It does not mean each individual estimate is accurate.

The highlighted WT is especially important. Its measured historical median is 0.1345 nanomolar, while the group-held-out prediction is approximately 9.08 nanomolar: about 67.5 times higher. That is poor calibration at the strong-binding reference.

This is why we should resist presenting 0.94 times WT for a new sequence as a reliable gain. We can use the model to prioritise hypotheses, but its errors near the benchmark are large. The training cohort also contains only reportable numerical KD values, so this plot does not validate a binder-versus-nonbinder classifier for arbitrary new designs.”

The plotted model is the primary grouped out-of-fold Ridge model. Candidate Ridge values come from the separate sixteen-fit bootstrap ensemble trained on the measured cohort; they are related outputs, but not identical fitting procedures. The GP is a secondary analysis. Avoid calling the chart an independent prospective validation of the complete adaptive design process.

## Slide 11 / PDF page 14 — Conclusion, limitations and the next decisions

“We have produced new HER2 antibody-fragment sequences, rebuilt the assay predictors, implemented exact sequence checks and evaluated structural hypotheses with controls. The four initial priorities cover three H3 loops and a matched framework comparison. The wider twenty explore additional optimisation proposals and two provisional de novo VHHs.

The strongest result today is that we can trace the decisions from experimental data through sequence generation to a concrete experimental panel. The largest uncertainty is whether those computational preferences survive expression and measurement. We have not yet demonstrated improved affinity, retained competition, improved thermal stability or a better breast cancer therapy.

The first decision comes from expressing the constructs and measuring them alongside a matched trastuzumab variable-region reference. We need quantitative HER2 affinity, competition with trastuzumab and direct thermal measurements in the same experimental programme. We should record expression failures and unreportable measurements rather than scoring only the successful constructs.

Picks one and two test the framework change on an otherwise matched sequence. Pick three tests the stronger screening signal. Pick four tests another framework-plus-loop combination, with its matched parent needed to isolate the mechanism.

If a molecule improves on the relevant challenge endpoints, it becomes a candidate for further research. For the breast cancer programme, subsequent work would need to establish cell-surface HER2 binding, specificity and the behaviour of an appropriate therapeutic antibody format. The move from a variable-domain fragment to a full therapeutic construct changes the biological question and requires new evidence.

In parallel, the method itself needs a prospective benchmark. At the same experimental budget, does it produce more useful molecules than simpler sequence selection? That is how we would show that the workflow creates value for a discovery team.”

## Technical questions to prepare for

### Have we made an S-tier antibody?

No S-tier status has been established. The organisers’ assays determine that. In particular, we have no new measured KD, competitive-binding result or thermal-stability result for any of the four.

### Is Pick 01 predicted to beat trastuzumab?

Only the secondary GP gives a nominal improvement, approximately 0.94× the historical KD. The primary Ridge estimate is 2.94×. The size of the nominal GP advantage is small compared with model error and historical WT variation. The accurate description is disagreement about the benchmark, with enough interest to test the sequence.

### Does 19/19 mean perfect molecular matching?

It means the predicted antibody contacts all nineteen target residues in the reference contact set at a specified distance cutoff. It does not require identical atom contacts, exclude additional contacts, establish affinity, or measure competition. The same value for all four is not a ranking result.

### Does zero of nineteen mean no binding?

No. It can mean a prediction at a different site. Pick 02’s OpenDDE model contacts other HER2 residues but none of the reference nineteen. The WT control also performs poorly in that protocol. A job failure is a separate category and must remain missing.

### Are Picks 01 and 02 two independent loop successes?

No. They share one H3 and differ at two framework positions. They form a useful matched experiment. Across four constructs, there are three distinct loops and two framework-modified versions.

### Are the four de novo?

No. All four are trastuzumab-derived optimisation designs. The two intended de novo VHHs are in the wider twenty and have unresolved full-database eligibility.

### Did we use every available dataset and model?

No claim of that kind is justified. We used the supplied FACS and SPR data directly for fresh learning and sequence checks, and used multiple design/structure resources in distinct branches. The bucket also contains large predicted-complex collections. Availability is not evidence that a dataset was incorporated into these fitted predictors. In this fresh training, the labels are the audited experimental FACS and SPR data, not 1.8 million additional measured affinities. Similarly, optional developability tools named in the challenge are not completed analyses unless their outputs exist in the run records.

### Why not train a single end-to-end probability of S-tier?

We lack suitable joint labels for binding, competition and thermal improvement in the submitted format. Combining unrelated model confidences into a numerical S-tier probability would imply calibration we have not demonstrated. We kept the endpoints and uncertainties separate.

### Did the fresh rebuild improve results?

It improved the auditability of the claims, the separation of assay endpoints, the novelty checks and the control-based interpretation. It produced new candidates and fresh results. We do not yet know whether it improved experimental hit rate, affinity or stability relative to the earlier approach. That requires a prospective comparison.

### What is the largest weakness in the training?

The affinity model uses only 180 reportable, same-background constructs, with poor calibration for WT and no direct modelling of expression failure, missing KD mechanisms or new frameworks. The much larger FACS dataset does not solve that quantitative-affinity problem, because its labels measure a different phenotype.

### What would we improve next in the modelling?

First, fit a reportability/expression component only when the assay metadata can support defensible labels; do not reclassify all missing KD as nonbinding. Second, assess affinity performance specifically near strong binders and under scaffold or mutation-distance shifts. Third, retain nested model selection and a genuinely untouched evaluation set when choosing between model families. Fourth, collect matched framework data rather than copying an H3 prediction onto a new framework. Fifth, perform selected multi-seed structural checks using a consistent protocol and matched WT controls. Finally, use the next experimental batch in an active-learning loop whose success is evaluated against an equal-budget baseline.

### What should the next experimental panel include?

The first four, a matched original-framework WT, and—if additional capacity permits—the framework-modified WT and Pick 04’s original-framework parent. Use the same expression format and matched assay conditions. Include appropriate assay controls, report uncertainty and inspect expression, affinity kinetics, competition and thermal behaviour separately. Later therapeutic-format and cell studies are new stages, not results already obtained.

## Reproducibility and source map

The GitHub repository is [Umi-Zoomi](https://github.com/MohamedAlaydi/Umi-Zoomi). Paths below are relative to its root. They identify the evidence underlying this manuscript, not external instructions to execute.

| Claim or stage | Source |
|---|---|
| Clinical motivation | EMA Herceptin link above |
| Experimental endpoint and entry rules | The two attached Apheris challenge PDFs; detailed write-up takes the stricter boundary in our policy |
| Fresh protocol and initial pool | `review/fresh_evaluation/report/evidence/predeclared.json`; `pool.json` |
| Experimental-data counts and WT values | `review/fresh_evaluation/report/evidence/fresh-assay-audit.json` |
| FACS split and frozen model configuration | `review/fresh_evaluation/report/evidence/training__protocol-before-fit.json` |
| Fresh fitting and proposal generation | `review/fresh_evaluation/train_generate.py` |
| Primary validation metrics | `review/fresh_evaluation/report/evidence/training__metrics.json`; `training__SPR-OOF.csv` |
| GP sensitivity and error quantiles | `review/fresh_evaluation/affinity_sensitivity.py`; `report/evidence/training__affinity-sensitivity.json` |
| Generation funnel | `review/fresh_evaluation/report/evidence/training__generation-summary.json` |
| New H3 and framework experiment | `review/fresh_evaluation/report/evidence/new-sequence-experiment.json` |
| Framework intervention source | Ng et al. DOI above; verified against 7MN8 heavy chain E |
| Remote structure geometry | `review/fresh_evaluation/report/evidence/fresh-full-context-geometry.csv` |
| Local Boltz-2 controls | `review/fresh_evaluation/report/evidence/local-boltz2-evidence.json` |
| Binding-ddG validation | `review/fresh_evaluation/report/evidence/binding-ddg-calibration.json` |
| Local known-antibody checks | `review/fresh_evaluation/report/evidence/fresh-known-antibody-recheck.csv` |
| Panel policy | `review/fresh_evaluation/report/evidence/prioritisation-policy.json` |
| Four identities, structures and assay scope | `review/pitch_final/RESULTS_AND_SOURCES.json`; `TOP4_RESULTATER.csv` |
| Four-design table | `review/pitch_final/FOUR_DESIGN_COMPARISON.csv` |
| Held-out plot values | `review/pitch_final/MODEL_VALIDATION_DATA.csv` |
| Final twenty and track labels | `submissions/umi-zoomi.csv` |
| Display colours and letter highlights | `review/pitch_final/deck.html`: `CHAIN`, `LOOP0`, `LOOP1`, `ANCHOR`, and letter-tile `keep` logic |

Inputs are hashed, model protocols and job identifiers are recorded, and missing results retain their status. Passing local abguard establishes only the checks exercised with the supplied references; it does not certify the full de novo reference database or an experimental tier. The prepared CSV is an output file, not proof that it was posted to the organisers’ Slack channel.
