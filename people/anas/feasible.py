#!/usr/bin/env python3
"""Is the IDEAL design even legal? Enumerate the space exactly.

Run 005 anchored the four contact residues and 0 of 10 designs passed novelty:
eight failed the official rule outright, at distance 1 from a provided sequence.
That is not bad luck. Anchoring W99/G103/F104/Y105 leaves six free positions, and
the provided 525,063 CDRH3s cover that subspace densely.

So enumerate all 20^6 = 64,000,000 fillings of the six free positions and mark
every one that is too close to a provided sequence. A provided sequence that
differs at g of the four anchored positions needs only (3 - g) differences in the
free positions to be 3 away in total, so:

    g = 0   the free 6-mer must be >= 3 from it
    g = 1   >= 2
    g = 2   >= 1   (not identical)
    g >= 3  always fine

Then apply our own bar: identity to trastuzumab <= 60 %, which with the grip kept
means at least 4 of the 6 free positions changed, and both liabilities (D102, M107)
among them.

  py people/anas/feasible.py              counts, and 20 example loops
  py people/anas/feasible.py --dump FILE  write every legal loop
"""
from __future__ import annotations

import argparse
import csv
import io
import itertools
import os
import sys
import zipfile

import numpy as np

DATA = os.path.expanduser("~/team14/data/her2-trastuzumab")
AA = "ACDEFGHIKLMNPQRSTVWY"
AA_IX = {a: i for i, a in enumerate(AA)}
WT = "WGGDGFYAMD"
CONTACT = [0, 4, 5, 6]            # W99 G103 F104 Y105
FREE = [1, 2, 3, 7, 8, 9]         # G100 G101 D102 A106 M107 D108
LIAB_FREE = [FREE.index(3), FREE.index(8)]   # D102, M107 within the free 6-mer
K = len(FREE)
BASE = 20 ** np.arange(K - 1, -1, -1, dtype=np.int64)


def load_provided() -> list[str]:
    seqs = set()
    z = zipfile.ZipFile(os.path.join(DATA, "tz_her2_facs_3classes_524346.csv.zip"))
    name = [n for n in z.namelist() if not n.startswith("__MACOSX")][0]
    with z.open(name) as fh:
        for r in csv.DictReader(io.TextIOWrapper(fh)):
            seqs.add(r["cdrh3"])
    for r in csv.DictReader(open(os.path.join(DATA, "trastuzumab_her2_spr_all_768.csv"))):
        seqs.add(r["cdrh3"])
    return [s for s in seqs if len(s) == 10 and all(a in AA_IX for a in s)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump")
    args = ap.parse_args()

    provided = load_provided()
    print(f"provided 10-mers: {len(provided):,}")

    arr = np.array([[AA_IX[a] for a in s] for s in provided], dtype=np.int8)
    wt = np.array([AA_IX[a] for a in WT], dtype=np.int8)
    g = (arr[:, CONTACT] != wt[CONTACT]).sum(1)          # mismatches at anchored positions
    free = arr[:, FREE]

    print("provided, by mismatches at the four anchored positions:")
    for k in range(5):
        print(f"  g={k}: {(g == k).sum():>9,}")

    forbidden = np.zeros(20 ** K, dtype=bool)

    def mark(refs: np.ndarray, radius: int) -> None:
        """Forbid every 6-mer within `radius` of any row of refs."""
        if refs.size == 0:
            return
        forbidden[(refs.astype(np.int64) * BASE).sum(1)] = True
        if radius >= 1:
            for p in range(K):
                for a in range(20):
                    m = refs[:, p] != a
                    if not m.any():
                        continue
                    v = refs[m].copy()
                    v[:, p] = a
                    forbidden[(v.astype(np.int64) * BASE).sum(1)] = True
        if radius >= 2:
            for p, q in itertools.combinations(range(K), 2):
                for a in range(20):
                    for b in range(20):
                        v = refs.copy()
                        v[:, p] = a
                        v[:, q] = b
                        forbidden[(v.astype(np.int64) * BASE).sum(1)] = True

    print("\nmarking the forbidden neighbourhoods (this is the slow part)")
    mark(free[g == 0], 2)
    print(f"  after g=0 (radius 2): {forbidden.sum():,} of {forbidden.size:,} forbidden")
    mark(free[g == 1], 1)
    print(f"  after g=1 (radius 1): {forbidden.sum():,}")
    mark(free[g == 2], 0)
    print(f"  after g=2 (exact):    {forbidden.sum():,}")

    legal = ~forbidden
    print(f"\nnovelty-legal fillings of the six free positions: {legal.sum():,} "
          f"of {legal.size:,}  ({100.0 * legal.sum() / legal.size:.2f} %)")

    # our own bar, on top: >= 4 of 6 changed, and both liabilities among them
    idx = np.flatnonzero(legal)
    digits = ((idx[:, None] // BASE) % 20).astype(np.int8)
    wt_free = wt[FREE]
    nmut = (digits != wt_free).sum(1)
    liab_ok = (digits[:, LIAB_FREE[0]] != wt_free[LIAB_FREE[0]]) & \
              (digits[:, LIAB_FREE[1]] != wt_free[LIAB_FREE[1]])

    for label, m in [("legal", np.ones(len(idx), bool)),
                     (">=4 of 6 changed (identity <= 60 %)", nmut >= 4),
                     ("  and both liabilities changed", (nmut >= 4) & liab_ok),
                     ("  and no cysteine", (nmut >= 4) & liab_ok & (digits != AA_IX["C"]).all(1))]:
        print(f"  {label:<38} {m.sum():>12,}")

    keep = (nmut >= 4) & liab_ok & (digits != AA_IX["C"]).all(1)
    final = idx[keep]
    finald = digits[keep]
    print(f"\nIDEAL designs that are also novelty-legal: {len(final):,}")

    def render(d: np.ndarray) -> str:
        s = list(WT)
        for pos, v in zip(FREE, d):
            s[pos] = AA[v]
        return "".join(s)

    if len(final):
        rng = np.random.default_rng(0)
        pick = rng.choice(len(final), size=min(20, len(final)), replace=False)
        print("\n20 examples (grip kept, both liabilities changed, novelty-legal):")
        for i in pick:
            print("   " + render(finald[i]))

    if args.dump and len(final):
        with open(args.dump, "w") as fh:
            for i in range(len(final)):
                fh.write(render(finald[i]) + "\n")
        print(f"\nwrote {len(final):,} loops to {args.dump}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
