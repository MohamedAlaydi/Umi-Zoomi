# 005-mohamed-anchored-n40

- when: 2026-11-14 11:02
- model: her2-novel-2026-11-09
- input: her2_cdrh3_anchored.yaml, our own, W99/G103/F104/Y105 pinned in
  C_SEQ and C_CRDGRP so only 100, 101, 102, 106, 107, 108 are generated
- designs: 40, refolding the best 10, seed 1, recycle high/front_loaded

## why we ran it

Run 004 generated 40 designs with the whole loop free and 0 of the 10 refolded
kept all four contact residues. G103 and F104 were lost in every single one.
So the model will not preserve the interface unless it is told to.

This run encodes the contact map we measured as a constraint on the input,
rather than hoping the model respects it. If the hypothesis is right, these
designs should keep the grip by construction and still clear novelty on the
six free positions.

## what came out

(fill in with `results mohamed`)

## decision

(keep / drop, and why)
