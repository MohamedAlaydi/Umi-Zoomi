# What we know about trastuzumab, and where the opening is

Measured from the structure we are actually designing against, plus the
published literature on trastuzumab's weaknesses. 14 Nov 2026.

---

## 1. The epitope, measured not assumed

Computed from `Data/12-her2/her2_fv_1n8z.cif` with
`scripts/contacts.py`: every HER2 heavy atom within 4.5 Å of the
antibody. 19 HER2 residues are in contact.

| HER2 residue | contacts | touched by |
| --- | --- | --- |
| E558 | 6 | heavy CDR1/CDR2 |
| P572 | 6 | light CDR3, **CDRH3 W99, Y105** |
| P571 | 4 | light chain, **CDRH3 Y105** |
| F573 | 4 | heavy CDR1/CDR2, **CDRH3 W99, Y105** |
| D560 | 3 | light T94, heavy R50, R59 |
| D570, P579, I591, K593 | 1-2 | **CDRH3 G103, F104, Y105** |
| D596, E598, A600, Q602, P603, C604, P605 | 1-2 | light chain only |
| P557, Q561, K569 | 1 | heavy / light |

### The finding that matters

The model redesigns **CDRH3 positions 99 to 108**, ten residues. Only
**four of them touch HER2 at all**:

```
position   99  100 101 102 103 104 105 106 107 108
residue     W   G   G   D   G   F   Y   A   M   D
contacts   YES  -   -   -  YES YES YES  -   -   -
```

So six of the ten positions we are allowed to change make **no contact
with the antigen**: G100, G101, D102, A106, M107, D108.

That is the opening. We can mutate the non-contact positions freely to
clear the novelty filter and improve stability, while leaving W99, G103,
F104 and Y105 alone to preserve binding and the epitope.

### The other half of the binding is out of reach

The light chain contributes ten contact residues (D28, N30, T31, A32,
S50, F53, H91, Y92, T93, T94) and heavy CDR1/CDR2 another six (Y33, R50,
Y52, Y57, T58, R59). **The HER2 fine-tuned checkpoints only redesign
CDRH3**, so they can never touch the majority of the interface. If we
want to move affinity rather than preserve it, that needs the
`antibody-2026-10-30` checkpoint on the other CDRs.

---

## 2. What is published about trastuzumab's weaknesses

### The chemical liability is Asp-102, and it is in CDRH3

Trastuzumab's documented potency loss on storage has been attributed to
**isomerization of heavy-chain Asp-102 in CDR-H3**. The functional size of
the effect is disputed: one line of work ties potency loss to it, another
reports only a minor effect on target binding. Either way it is the
recognised liability in this molecule, and Asp isomerization in CDR-H3 is
a general developability concern across clinical-stage antibodies, not a
quirk of this one.

**D102 is one of our six non-contact positions.** It also sits in a `DG`
motif with G103, which is the classic isomerization pattern.

### What is *not* worth chasing

- **Met-107 oxidation.** Reported as not susceptible to oxidation in
  trastuzumab. Methionine oxidation in this molecule is an Fc-region
  issue, and we are not designing the Fc. Do not spend time on it.
- **Light-chain Asn-30 deamidation.** Reported as not significantly
  affecting potency.
- **Heavy-chain Asn-55 deamidation.** Reported as only moderately
  affected, and it is in CDR2, which the HER2 checkpoints cannot touch
  anyway.

This is worth saying out loud in the pitch: we checked three plausible
liabilities and dropped them on evidence, keeping one.

### The clinical picture, for the "who needs this" part of the pitch

Trastuzumab resistance is real and poorly solved. The two mechanisms that
bear on an epitope-preserving design:

- **p95HER2.** Proteolytic shedding of the HER2 ectodomain leaves a
  truncated, constitutively active membrane fragment that trastuzumab
  cannot bind, because the epitope is on the part that was cut off. Cells
  expressing it are insensitive to trastuzumab while cells expressing
  full-length HER2 are inhibited.
- **MUC4 epitope masking.** In the resistant JIMT-1 line, MUC4 level is
  inversely correlated with trastuzumab binding, and knocking MUC4 down
  restores sensitivity. Steric hindrance of the epitope is the proposed
  mechanism.

**Be careful how we use this.** Both are well supported preclinically and
neither has produced a validated clinical biomarker or therapy. The MUC4
evidence rests largely on one cell model. A pitch that claims we are
solving resistance would be overclaiming, and at least two of the judges
will know that.

The honest framing: both mechanisms are about **access to the epitope**,
which is precisely the property this challenge scores. A variant that
keeps the epitope while being more stable is a better starting molecule
for the formats that address resistance, such as ADCs and bispecifics,
rather than a resistance cure itself.

---

## 3. The design hypothesis this gives us

For the **optimisation track**:

> Keep W99, G103, F104 and Y105, the four CDRH3 residues that actually
> contact HER2. Mutate at least four of the six non-contact positions,
> prioritising D102 to remove the documented isomerization liability.

Why this is worth defending in a pitch, against the three scored
properties:

| scored property | why this should hold or improve |
| --- | --- |
| epitope preserved | the contacting residues are untouched by construction |
| binding | the interface is unchanged; most of it is light chain and CDR1/2 anyway |
| thermostability | D102 is the known liability, and it is free to mutate |

And it clears the novelty filter by construction: four mutations gives
60 % identity to trastuzumab, inside our ≤ 60 % internal bar and clear of
the official 70 % limit.

This is a hypothesis, not a result. It needs the designs run, scored and
checked like anything else. But it is a reason to pick a molecule, which
is exactly what Judgment is 40 % of the score for.

### How to test it cheaply

1. Generate with the HER2 checkpoint as normal.
2. For each design, check whether positions 99, 103, 104, 105 are
   conserved and whether 102 changed. `scripts/contacts.py` gives the
   contact list; the comparison is a few lines on top of `report.py`.
3. Rank designs that match the hypothesis above the ones that do not, and
   say in the pitch that this is what we did and why.

---

## 4. Reproducing the structural analysis

```bash
py scripts/contacts.py
```

Reads the hackathon's own 1N8Z file, no network, no model, no credits. It
prints the epitope, what CDRH3 touches, the paratope, and a suggested
automatic epitope check.

## Sources

Structure: the hackathon's `her2_fv_1n8z.cif`, PDB 1N8Z, cropped to the Fv
and HER2 domain IV.

Literature:
- [Deamidation and isomerization liability analysis of 131 clinical-stage antibodies](https://pubmed.ncbi.nlm.nih.gov/30526254/)
- [Antibody modification monitoring by LC-MS peptide mapping](https://www.americanpharmaceuticalreview.com/Featured-Articles/331529-Multi-Attribute-Monitoring-of-Antibody-Modifications-by-Semi-Automated-Liquid-Chromatography-Mass-Spectrometry-Peptide-Mapping/)
- [Biophysical characterization of monoclonal antibodies](https://www.azolifesciences.com/article/Exploring-the-Biophysical-Characterization-of-Monoclonal-Antibodies.aspx)
- [Trastuzumab resistance mechanisms review](https://www.frontiersin.org/journals/oncology/articles/10.3389/fonc.2024.1389390/full)
- [p95HER2 and resistance](https://pmc.ncbi.nlm.nih.gov/articles/PMC3376449)
- [MUC4 epitope masking in JIMT-1](https://pmc.ncbi.nlm.nih.gov/articles/PMC3045786)

These came from web search, not from AMASS. Once the AMASS credits are
claimed, every claim above should be re-checked there so the pitch can
cite records rather than reviews.
