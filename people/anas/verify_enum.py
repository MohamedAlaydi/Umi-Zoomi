#!/usr/bin/env python3
"""Check the enumeration against an independently written implementation.

feasible.py marks a 6-mer illegal by expanding the neighbourhood of every provided
sequence and setting bits in a 64M bitmap. That is one person's code with one set of
off-by-one risks, and the whole submission rests on it. scripts/novelty.py was written
separately by Mohamed and decides the same question a completely different way, by
computing distances directly.

So sample both sides and see whether the two agree:
  claimed legal    -> novelty.py must accept every one
  claimed illegal  -> novelty.py must reject every one

A disagreement in either direction means the enumeration is wrong and the candidate
list cannot be trusted.

  py people/anas/verify_enum.py --n 2000
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.expanduser("~/team14/scripts"))
import novelty  # noqa: E402

AA = "ACDEFGHIKLMNPQRSTVWY"
WT = "WGGDGFYAMD"
FREE = [1, 2, 3, 7, 8, 9]
LOOPS = os.path.expanduser("~/team14/people/anas/ideal-legal-loops.txt")
MIN_DIST = 3          # our reading of "strictly more than 2 point mutations"
MAX_IDENTITY = 60.0   # our own margin, stricter than the published 70 %


def render(six: str) -> str:
    s = list(WT)
    for pos, c in zip(FREE, six):
        s[pos] = c
    return "".join(s)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    args = ap.parse_args()
    rng = np.random.default_rng(7)

    pool = novelty.load()
    total = sum(a.shape[0] for a in pool.values())
    print(f"novelty.py pool: {total:,} provided CDRH3s")

    legal = [l.strip() for l in open(LOOPS)]
    print(f"claimed legal: {len(legal):,}\n")

    # --- direction 1: claimed legal must be accepted -----------------------
    pick = rng.choice(len(legal), size=min(args.n, len(legal)), replace=False)
    bad = []
    for i in pick:
        cdr = legal[i]
        d, nearest = novelty.min_distance(cdr, pool)
        idt = novelty.identity_to_trastuzumab(cdr)
        if d < MIN_DIST or idt > MAX_IDENTITY or "C" in cdr:
            bad.append((cdr, d, idt, nearest))
    print(f"direction 1, claimed legal checked with novelty.py: {len(pick)} sampled")
    print(f"  rejected by novelty.py: {len(bad)}")
    for cdr, d, idt, nearest in bad[:10]:
        print(f"    {cdr} distance {d} identity {idt:.0f} % nearest {nearest}")

    # --- direction 2: random 6-mers NOT in the legal set must be rejected --
    legal_set = set(legal)
    tried, illegal_checked, wrongly_rejected = 0, 0, []
    while illegal_checked < args.n and tried < args.n * 200:
        tried += 1
        six = "".join(AA[j] for j in rng.integers(0, 20, len(FREE)))
        cdr = render(six)
        if cdr in legal_set:
            continue
        # only judge the ones feasible.py excluded for the novelty reason itself
        nmut = sum(1 for a, b in zip(cdr, WT) if a != b)
        if nmut < 4 or "C" in cdr or cdr[3] == WT[3] or cdr[8] == WT[8]:
            continue
        illegal_checked += 1
        d, nearest = novelty.min_distance(cdr, pool)
        idt = novelty.identity_to_trastuzumab(cdr)
        if d >= MIN_DIST and idt <= MAX_IDENTITY:
            wrongly_rejected.append((cdr, d, idt))
    print(f"\ndirection 2, excluded 6-mers checked with novelty.py: {illegal_checked} sampled")
    print(f"  novelty.py says they would have passed: {len(wrongly_rejected)}")
    for cdr, d, idt in wrongly_rejected[:10]:
        print(f"    {cdr} distance {d} identity {idt:.0f} %")

    ok = not bad and not wrongly_rejected
    print("\n" + ("AGREE: two independent implementations give the same verdict on every sample."
                  if ok else "DISAGREE: the enumeration is wrong. Do not submit from it."))
    print("\nStill true: both implementations are ours. abguard is not installed on this VM,")
    print("so neither is the official tool, and the published rules are ambiguous on whether")
    print("the bar is 2 or 3 mutations. We use 3, the stricter reading.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
