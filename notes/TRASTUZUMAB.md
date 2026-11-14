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

All of this section was re-checked in AMASS against primary records. One
claim I had made from web search turned out to be **wrong**, and the
correction makes our case stronger. Both are kept below, because showing
the correction is worth more than pretending we got it right first time.

### Asp-102 isomerization: confirmed, and it is the serious one

The primary characterization of trastuzumab's charge heterogeneity
(Harris et al. 2001, 503 citations) resolves seven forms of the antibody
and assigns **a low-potency form to isomerization of heavy-chain
Asp-102**, with the Asp102 succinimide also present. Every modification
they found was in a CDR.

A later study stressing trastuzumab under physiological conditions
describes Hc-Asp-102 isomerization as a modification that **critically
affects biological activity**, and adds something useful: it was not
detected at all when the antibody was stressed **in complex with HER2**,
only when stressed free. So the position is exposed and flexible in the
unbound antibody, which is exactly the condition a vial of drug product
is in.

**D102 is one of our six non-contact positions**, and it sits in a `DG`
motif with G103, the classic isomerization pattern.

### Correction: Met-107 oxidation is real, and I was wrong about it

My earlier note said Met-107 was not susceptible to oxidation in
trastuzumab and told you to ignore it. **That was wrong.** The AMASS
records say the opposite:

- A study of oxidation sites in recombinant antibodies names heavy-chain
  **Met-107 of the HER2 antibody** as already identified as solvent
  accessible and sensitive to chemical oxidation.
- The in-use stability study of the trastuzumab biosimilar CT-P6
  routinely **measures oxidation at methionine 107**, alongside 255/256
  and 432/433. Industry treats Met-107 as a quality attribute worth
  monitoring in this exact molecule.

**M107 is also one of our six non-contact positions.**

So trastuzumab's CDRH3 carries **two** documented chemical liabilities,
D102 and M107, and **neither of them touches HER2**. That is a better
story than the one I had, not a worse one.

### Still not worth chasing

- **Light-chain Asn-30 deamidation.** Reported as not significantly
  affecting potency, and the same stress study found it drops about
  tenfold when HER2 is bound.
- **Heavy-chain Asn-55 deamidation.** In CDR2, which the HER2 checkpoints
  cannot touch anyway.

### Prior art: someone already improved trastuzumab through CDRH3

This matters for novelty and for what is achievable.

Moon et al. 2016 built a biobetter of hu4D5, which is trastuzumab, by
randomizing CDR-H3 and CDR-L3 and panning. Their clone **AH06 reached a
7.4-fold better affinity (KD 60 pM) and 7.2-fold better anti-proliferative
activity**, from substitutions in CDR-H3. Their modelling attributes the
gain to new hydrophobic contacts, including between an aromatic CDRH3
residue and **HER2 Ile-613**.

Three things follow:

1. **CDRH3 substitution really can improve affinity here.** Beating
   0.152 nM is not hopeless, and we have a published existence proof.
2. **The gain came from reaching a HER2 residue wild-type trastuzumab
   does not touch.** Ile-613 is not in our contact list. Note that our
   1N8Z construct is cropped and chain D ends at residue 607, so I613 is
   not even present in the file we design against. A design cannot be
   guided toward a residue the input does not contain.
3. **Their sequences may count as known antibodies** for the de novo
   track's identity check. Worth flagging to the organisers.

There is also a published ML study built on **193 affinity values of
single trastuzumab mutants**, which is a ready-made external dataset if
anyone wants a second opinion on ranking.

### For thermostability, look outside CDRH3 too

A 2025 study used trastuzumab as its test case and designed **stabilizing
framework mutations distal to the CDRs** that kept HER2 binding and
effector function. The HER2 checkpoints cannot make framework changes, so
this is not directly actionable with our main tool, but it is the honest
answer to "how would you improve thermostability properly" in the pitch.
One caution from the same work: a light-chain framework mutation kept
antigen binding but silently lost Fab- and Fc-mediated effector function.
Binding is not the only thing a mutation can break.

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
> and make sure **D102 and M107 are two of them**, because those are the
> molecule's two documented chemical liabilities and neither touches the
> antigen.

Why this is worth defending in a pitch, against the three scored
properties:

| scored property | why this should hold or improve |
| --- | --- |
| epitope preserved | the contacting residues are untouched by construction |
| binding | the interface is unchanged; most of it is light chain and CDR1/2 anyway |
| thermostability | D102 (isomerization) and M107 (oxidation) are the two documented liabilities, and both are free to mutate |

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

**Structure**: the hackathon's own `her2_fv_1n8z.cif`, PDB 1N8Z, cropped
to the Fv and HER2 domain IV. Analysed with `scripts/contacts.py`.

**Records, via the AMASS connector** (BiomedCore and PatentCore). These
are the primary sources, and they are what replaced the review articles
the first draft of this note relied on:

| Claim | Record |
| --- | --- |
| Asp-102 isomerization gives a low-potency form; all modifications in CDRs | Harris et al. 2001, [PMID 11270864](https://pubmed.ncbi.nlm.nih.gov/11270864/), 503 citations |
| Asp-102 isomerization critically affects activity, and is absent when HER2 is bound | Spanov et al. 2022, [PMID 35047480](https://pubmed.ncbi.nlm.nih.gov/35047480/) |
| Met-107 of the HER2 antibody is solvent accessible and oxidation-sensitive | Hensel et al. 2011, [PMID 21390239](https://pubmed.ncbi.nlm.nih.gov/21390239/) |
| Met-107 oxidation monitored as a quality attribute in a trastuzumab biosimilar | Kim et al. 2018, [PMID 30386977](https://pubmed.ncbi.nlm.nih.gov/30386977/) |
| CDRH3 substitutions gave a 7.4-fold affinity gain over trastuzumab (KD 60 pM) | Moon et al. 2016, [PMID 26743905](https://pubmed.ncbi.nlm.nih.gov/26743905/) |
| 193 single-mutant trastuzumab affinity values, CDR-H3 structural effects | Balakrishnan et al. 2021, [PMID 34392800](https://pubmed.ncbi.nlm.nih.gov/34392800/) |
| Stabilizing framework mutations on trastuzumab that keep function | Ng et al. 2025, [PMID 40653772](https://pubmed.ncbi.nlm.nih.gov/40653772/) |
| Succinimide in a CDR correlates with potency loss, fixable by formulation | VanAernum et al. 2023, [PMID 36627449](https://pubmed.ncbi.nlm.nih.gov/36627449/) |

**From web search, not yet re-checked in AMASS**: the p95HER2 and MUC4
resistance material in section 2. Treat those as weaker until someone
pulls the trial and regulatory records.

### What AMASS changed

Worth saying in the pitch, because it is the Amass track in one line:
four questions, and the answers changed the design.

1. It **corrected a wrong claim**. Web search told me Met-107 was not
   oxidation-prone in trastuzumab. The records say it is, and that a
   biosimilar manufacturer measures it. We would have left a liability in
   the molecule.
2. It **found the primary source** for Asp-102 rather than a review's
   summary of it, and a second record showing the site is protected when
   HER2 is bound.
3. It **found prior art** that CDRH3 substitution already produced a
   7.4-fold affinity gain on this exact antibody, which tells us the
   optimisation track is winnable and raises a novelty question we should
   put to the organisers.
4. It **found an external dataset** of 193 single-mutant affinities we
   did not know existed.
