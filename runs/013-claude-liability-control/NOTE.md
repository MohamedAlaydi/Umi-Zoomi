# 013 claude liability-control

- when: 2026-11-14, after the ranked 20 was frozen
- tool: the recovered `abguard` build, `/home/hackathon/tools/abguard-venv/bin/abguard`,
  same invocation as `review/denovo/run_abguard.py`
- command: `py scripts/liability_control.py`
- reference: the package's own `reference_data` bundle; manifest hash in `input_hashes.txt`
- input: `submission.csv` in this directory, 21 rows, wild-type trastuzumab first and then
  the ranked 20 from `notes/RANKED_CANDIDATES.csv`
- output: `result.json` from abguard, `comparison.csv` derived from it
- exit code: 0. 21 designs read, **20 valid, 1 with hard errors**, 140 liability occurrences

## why we ran it

The design hypothesis says we remove two documented degradation liabilities that sit at
CDRH3 positions which touch no part of HER2: the D102 isomerization site and the M107
oxidation site. Every abguard run before this one scored only the designs. The parent was
never in the table, so "removed" and "added" were our words rather than the tool's, and we
had no way to answer the obvious question: what does the official checker say about
trastuzumab itself?

This run puts the parent in the same file, scored by the same tool against the same
reference, and lets abguard answer.

The wild-type heavy chain is not typed in by hand. The script derives it by substituting the
parent CDRH3 back into each design's own framework, asserts that all 20 designs yield one
identical parent sequence, and asserts that it matches the independent copy in
`review/denovo/test_regional.py`.

## the control behaved correctly

`trastuzumab_wt` is the one row with hard errors, and the error is
`insufficient_cdrh3_novelty`. That is the right answer: the parent is the thing a submission
has to be novel against, so the checker rejects it. It confirms the control went through the
same gates as the designs rather than down a side path.

## what abguard says about trastuzumab itself

Eight liabilities, on a molecule that has been a marketed medicine since 1998:

| tag | region | IMGT | motif | severity |
| --- | --- | --- | --- | --- |
| DeAmdH | cdr2 | 62/63 | | high |
| Isom | cdr1 | 36/37 | | high |
| DeAmdM | cdr1 | 36/37 | | medium |
| DeAmdL | cdr2 | 59/62 | | low |
| **Isom** | **cdr3** | **110/111** | **DG** | **high** |
| **MetOx** | **cdr3** | **115** | **M** | **medium** |
| TrpOx | cdr3 | 107 | W | medium |
| TrpOx | fr4 | 118 | W | medium |

The two in bold are ours. `Isom` at IMGT 110/111 carries the motif `DG`, which is D102
followed by G103, and `MetOx` at IMGT 115 is M107. So the tool's own numbering lands exactly
on the two sites the design hypothesis targets, and the literature behind them is in
`notes/TRASTUZUMAB.md`.

`TrpOx` at IMGT 107 is W99. That is one of the four residues that contact HER2, so we pin it
deliberately and every design keeps it. We are not going to remove a liability by throwing
away a contact.

The five liabilities outside CDR3 are untouchable in this competition: the HER2 checkpoints
only redesign CDRH3. Worth saying out loud, because it is the honest scope of the claim.

## the result

**All 20 designs remove both targeted liabilities.** Every single one loses
`Isom@cdr3:110/111` and `MetOx@cdr3:115`. That is the claim, and it is now the tool's
statement rather than ours.

**9 of 20 add nothing the parent did not already have:** HER2-OPT-009, HER2-GEN-003,
HER2-OPT-016, HER2-OPT-027, HER2-OPT-028, HER2-OPT-038, HER2-OPT-039, HER2-OPT-032,
HER2-OPT-010. That includes ranks 3 and 4, two of the four guaranteed tests.

**11 of 20 introduce one, and this is the part to volunteer:**

| what is added | severity | designs | honest reading |
| --- | --- | --- | --- |
| `TrpOx@cdr3:115` | medium | ranks 1, 2, 9, 10, 12, 13, 19, 20 | a tryptophan now sits where the parent had a methionine. We swapped an oxidation-prone residue for a different oxidation-prone residue at the same position. The class changed; the liability did not disappear. |
| `DeAmdH@cdr3:110/111` | high | ranks 11, 15 | a high-severity deamidation replaces a high-severity isomerization at the same position. Net zero. |
| `MetOx@cdr3:110` + `TrpOx@cdr3:115` | medium | rank 16 | reintroduces a methionine oxidation site, at a different position from the one removed. The weakest of the twenty on this axis. |

So **ranks 1 and 2, our two leading designs, both trade M107 oxidation for a tryptophan
oxidation site at the same IMGT position.** Nine designs lower down do not. That is a real
tension between the contact and sequence evidence that put ranks 1 and 2 on top and the
liability evidence here, and it is not resolved by this run. It is a question for the lab.

## what this does and does not support

- It supports: all 20 remove the parent's two CDR3 degradation sites that touch no antigen,
  by the official tool, with the parent scored in the same table.
- It does not support any claim about thermostability. Isomerization, deamidation and
  oxidation are chemical degradation over time. Adaptyv measures a melting temperature.
- It does not make a liability flag disqualifying. Trastuzumab has eight and it is a
  medicine. These are attributes to know about, not failures.
- It is a sequence-motif analysis. Whether a flagged motif is actually labile depends on
  local structure and solvent exposure, which this does not model.

## decision

Keep. The ranking is unchanged: this evidence arrived after the freeze and does not
overturn the contact and sequence reasoning in
`review/pitch_her2/Rangering_begrunnet.md`. But it is now a column a judge can check, and
if there is a question about what the designs introduced, the answer is in
`comparison.csv` rather than in a claim.
