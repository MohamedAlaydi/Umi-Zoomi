# 003 mohamed japanfold-abag-control

- when: 2026-11-14 10:0x
- model: JapanFold `opendde-abag` (OpenDDE antibody-antigen checkpoint, on the
  Protenix-v2 stack, MSA on by default)
- command: `./submit.sh`
- seed: n/a (MSA default, model's own sampling)
- why we ran it:

  Run 001 ranked the two designs on Boltz-2 numbers alone, and Boltz-2 is also
  what produced the refold those numbers came from. Two things were missing:

  1. **An independent model.** A second opinion from the same family is not a
     second opinion. OpenDDE is a different stack and a different checkpoint.
  2. **A control.** `iptm 0.965` means nothing without the number trastuzumab
     itself gets through the same model on the same four chains. Run 001 has no
     wild-type arm, so neither design could be called better or worse than the
     baseline they are judged against.

  This run adds both: three targets in one job, the only difference between
  them being the 11-residue CDRH3 in chain B.

  | target | CDRH3 |
  | --- | --- |
  | trastuzumab_wt | WGGDGFYAMDY |
  | her2_cdrh3_2 | WGPPYFYAMDY |
  | her2_cdrh3_3 | WASSSEYYFDY |

  All four chains are carried over verbatim from run 001's
  `scored-boltz2/refold_metrics.csv`, so A (VL), C and D (HER2) are identical
  across the three and nothing but the loop moves.

- control arm verified against the organisers' own data:

  The wild-type VH and VL in this request are byte-identical to row 1 of
  `data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv`, checked rather than
  trusted. That row is the judged baseline:

  | | |
  | --- | --- |
  | CDRH3 | WGGDGFYAMD |
  | KD | **0.152 nM** |
  | call | quantified_binding |

  0.152 nM is the number Adaptyv's SPR has to be beaten against for criterion 1.
  Worth pinning somewhere prominent: nothing in run 001 was measured against it.

- CDRH3 length convention, so nobody mixes the two:

  The provided data uses a **10-residue** CDRH3 (`WGGDGFYAMD`), and
  `provided_cdrh3.npz` is grouped into `len9` / `len10` / `len16` on that basis.
  Anchoring on the `WGQGTLVTVSS` framework instead gives 11 residues
  (`WGGDGFYAMDY`). Both describe the same antibody; only the first is
  comparable to the provided set. `scripts/novelty.py` and run 001's NOTE both
  use 10, which is right. Identity percentages computed on 11 would be wrong.

- why this model and not AF2-IG:

  AF2-IG was the first choice on cost (~$0.0008/target) and because it is the
  filter Adaptyv-style pipelines use. Reading its contract ruled it out for
  *these* designs: it takes one target chain and one binder chain, and the docs
  say "a chain list is a different input and it is refused". Our binder is a Fab
  (VL + VH) against a two-fragment HER2, so there is no honest way to name one
  binder chain. AF2-IG stays on the table for single-chain VHH designs later.

  `opendde-abag` is the checkpoint that co-folds a Fab heavy/light pair with its
  antigen, 1536-residue budget against our 336, ~$0.011/target.

- what came out: (fill in)
- decision (keep / drop / why): (fill in)

## What to read in the result

`iptm` and `interface_pae` per target, and the PAE matrix in `<name>_pae.npz`.
The comparison that matters is each design **against the wild-type row**, not
against an absolute threshold.

Caveat to carry into the writeup: the whole complex was given to the model with
the framework and the antigen fixed, so confidence is expected to run high for
every arm, wild type included. That is exactly why the control is there. A
design is only interesting here if it is at least as good as the wild-type row;
none of this is affinity.

OpenDDE's own documented limitation: strong on standard antibody-antigen
complexes, weaker on some hard targets. HER2/trastuzumab is about as standard as
it gets, so this is a reasonable use of it.
