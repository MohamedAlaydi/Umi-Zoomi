# 007-mohamed-anchored-diverse-k1

- when: 2026-11-14 11:50
- input: her2_cdrh3_anchored.yaml, W99/G103/F104/Y105 pinned
- added: --sequence-tsr-k 1 (lower = more varied loops), seed 2
- designs: 40, refolding the best 12

## why we ran it

Run 005 proved the anchoring works: 10 of 10 refolded designs kept all four
contact residues, against 0 of 10 when the loop was free. But it bought a new
problem. Pinned to the interface, the model stays close to trastuzumab, so
9 of 10 failed the novelty filter at distance 1 or 70-80 % identity. Only
her2_anchored_14 (WGPAGFYEFD) passed both gates.

This run keeps the anchor and turns up sequence diversity, so the six free
positions move further from the parent. If it works we get designs that keep
the grip AND clear novelty, which is the submittable combination.

## what came out

(fill in with `results mohamed`)

## decision

(keep / drop, and why)
