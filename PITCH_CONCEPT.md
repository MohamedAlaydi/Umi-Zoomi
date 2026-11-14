# Which model should choose the next four HER2 experiments?

**Recommended pitch.** Lead with the first concept. Show the left half of the figure when describing the measured comparison, then the right half when explaining why the team kept a free-loop candidate. End on the four proposed experiments and the result that would change your mind. [Pitch figure](review/evidence/assay-and-contacts.png) · [Ranked panel](review/evidence/panel.csv)

## 1. When the assay changed, the ranking changed

| Element | What to tell the judges |
|---|---|
| Hook | Our FACS model scored 0.994 on its source assay. Our numerically best historical SPR rule then gave the same answer for every one of the 40 designs. |
| Overlooked problem | The model and generator drew evidence from the same screen. Selecting the highest scores among millions of loops compressed the 40 shortlisted probabilities to 0.991–0.996. None of those probabilities was calibrated to the measured lab endpoint. |
| Insight | A fixed comparison against the parent carried more information about whether a historical SPR fit could be reported, even among variants with the same mutation count. |
| Contribution | We verified framework and chain compatibility, removed exact training-screen overlap and repeated WT measurements, kept inconclusive outcomes visible, and compared three scores on the same constructs. We carried the outcome into an explicit panel order. |
| Proof | 152 reportable fits and 432 nonfits. Nearest high-FACS distance AUROC 0.849, BLOSUM62 0.847, FACS booster 0.751, new ensemble 0.730. The paired 95% interval for the BLOSUM–booster difference was +0.061 to +0.132. Nearest-high distance was exactly three for all 40 candidates. |
| Why it matters | An assay scientist choosing four constructs from a nearly tied shortlist needs evidence about the next assay. A retrospective result can expose how far the current evidence travels. |
| Limitation | The source SPR library was partly selected using BLOSUM. Only three historical cases match the enumerated candidates' full sequence constraints and all three have a fit. We have no direct estimate of the fraction of our four that will succeed. |
| Path to value | Freeze competing selection rules, use equal synthesis capacity on a separately chosen campaign and score them against same-assay controls. Compare usable measurements per slot and the three endpoint outcomes. |

**Spoken opening, about 80 seconds**

“Imagine you have room for four antibodies in the next experiment. Our model can predict the high class in a yeast-display screen with an AUROC of 0.994, even when related sequence groups are held apart. It gave all forty of our shortlisted designs scores above 0.99. Which four would you choose?

We went back to measured HER2 data. On 584 variants with an interpretable SPR fit status, after removing training-screen overlaps and the repeated wild type, our model scored 0.751. Two simple rules did better. Distance to a high-FACS sequence scored 0.849. A substitution score against the parent reached 0.847. Yet every shortlisted design was exactly three changes from its nearest high-FACS neighbour. The first rule gave us a forty-way tie. The second could still order the designs.

Then we counted how many measured variants really looked like our shortlist. Three. That changed our decision again. We chose one candidate supported by both scores, one favoured by sequence, one favoured by structure, and a free-loop challenger whose modeled HER2 footprint matched the crystal. Our deliverable is a ranked set of experiments with a reason for each slot. The lab will measure binding, competition and thermal stability against the same wild type. Those results can overturn our ranking.”

## 2. Forty loops kept the letters. Twenty-eight kept the contacts.

| Element | What to tell the judges |
|---|---|
| Hook | Every enumerated Fab retained the four specified CDRH3 residues. Twelve of the 40 predicted poses lost at least one of their HER2 contacts at 4.5 Å. |
| Overlooked problem | A global interface score can include the antibody's heavy–light interface. The HER2 input is also split across an unresolved stretch. Counting matched amino acids does little to establish where those amino acids sit in a new pose. |
| Insight | The distinction is observable on the team's models. A free-loop comparator retained two reference identities and still recovered the exact 19-residue HER2 footprint. |
| Contribution | We matched the physical chains and author residue IDs to the 1N8Z reference. We computed Fab–HER2 contact sets from the saved coordinates at three distances and extracted the four antibody-to-antigen pair scores with a same-batch WT. |
| Proof | The WT recovered all 19 reference residues at 4.5 Å. Exact footprint recovery occurred in 14/40 enumerated poses. Counts with all four loop contacts were 25/40 at 4.0 Å, 28/40 at 4.5 Å and 28/40 at 5.0 Å. At 4.0 Å the crystal itself includes only two of the four. |
| Why it matters | A structural biologist can see which part of a predicted complex drove a selection and where the reference template might be forcing agreement. |
| Limitation | One templated sample per design in the matched batch. HER2 residues 581–590 have no coordinates. A plausible footprint can coexist with weak binding, and competition is a distinct experimental readout. |
| Path to value | Compare measured competition with predeclared contact-overlap estimates across the next annotated panel. Re-evaluate different templates and seeds if the overlap proves sensitive to the setup. |

Use this concept if judges want a structural walkthrough. Display the 40/28 bars and the free-loop row of the panel. Speak of “predicted contacts” when showing candidates and “crystal contacts” when showing WT. [Coordinate analysis](review/structure_checks.py) · [Experimental reference structure](https://www.rcsb.org/structure/1N8Z)

## 3. What can four test slots teach us?

| Element | What to tell the judges |
|---|---|
| Hook | The laboratory guarantees four slots. Only three historical constructs satisfy all the sequence constraints behind forty of our candidates. Which experiment is worth the fourth slot? |
| Overlooked problem | Four near-identical, high-ranked loops can fail for the same reason. Historical fit data say little about the new panel's competition or thermal stability. |
| Insight | Reserving slots for explicit disagreements can reveal whether a selection rule earned its place. The strongest free-loop comparator provides a realistic challenge to the team's anchored designs. |
| Contribution | A deterministic ranked list, full heavy and light chains, traceable selection reasons, and at least three pairwise loop differences throughout. The first four cover a sequence-and-pose choice, a sequence-led contrast, a geometry-led contrast and the free-loop comparator. |
| Proof | The four candidates span BLOSUM scores 19–40, minimum VH confidence deltas −0.0025 to +0.0320 versus WT, and predicted footprint overlap 0.864–1.000. Run 010 reproduced the free-loop comparator's seed-42 coordinates. These are real differences in how the four were chosen. |
| Why it matters | The people commissioning expression and assays can trace why each construct consumed a slot, including a candidate that challenges the original design hypothesis. |
| Limitation | Four is too small for a reliable between-strategy hit-rate comparison. Pairwise sequence difference supplies no guarantee of functional diversity. A validator rejection changes the tested set. |
| Path to value | Retain the original order, replacements and failures. Across multiple future campaigns, test whether contrasting allocation improves the number of usable and jointly successful results per fixed assay budget. |

## Scorecard and close

| Pitch weight | What the speaker can show |
|---|---|
| **40% judgment** | Show the measured assay-transfer reversal, its paired interval and the three matching examples. Name the selection decision each finding changed. |
| **20% execution** | Show the immutable evidence checksums, reproducible CPU comparison, chain verification and the full order with a reason and paired sequence hash on every row. Have the team's GitHub link ready for the actual submission. |
| **20% user fit** | Name the assay lead deciding which Fab constructs to express under a fixed capacity. Show the four rows they would actually review. |
| **20% path to value** | Describe a prospective, equal-budget comparison in a second campaign. Predefine costs, expression availability, reportable KD, competition and thermal result. Report outcomes for all selected candidates. |

For a question about S-tier prospects, show the three lab readouts separately. HER2 SPR measures affinity, competition tests preservation of the reference epitope operationally, and the lab directly measures thermostability. All three remain open for the ranked designs. The pharmacology, safety and clinical benefit of a therapeutic product extend far beyond these assays. [Official challenge](https://oslo-ai-antibodies-hackathon.vercel.app/) · [Evidence and limitations](RESEARCH_INTELLIGENCE.md)
