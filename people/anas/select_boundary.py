#!/usr/bin/env python3
"""Select on the one rule that actually validates: sit on the novelty boundary.

fair_compare.py killed the model as a ranker. Against the SPR external set, in our own
>= 4-mutation regime, distance to the nearest known FACS high binder reaches AUC 0.821
while the gradient-boosting p_high reaches 0.704. The one-line rule wins, and it keeps
winning at >= 5 mutations (0.802 against 0.663).

The reason is in the binder rate by that distance, measured on SPR rows the models never
saw:

    d=1  n=38   97 % bind          d=4  n=179  10 %
    d=2  n=74   64 %               d=5  n=133   3 %
    d=3  n=142  37 %               d=6  n=26    4 %

Binding collapses with distance from the known binders. And the novelty rule requires
strictly more than 2 mutations from every provided sequence, which includes every known
high binder. So the challenge forces us past d=2, into the collapse, and the best legal
position is exactly d=3: still 37 %, where d=5 is 3 %.

That is the selection rule. Among legal candidates, prefer the smallest legal distance
to a known high binder, then use p_high only to order within a distance class.

  py people/anas/select_boundary.py --top 20 --out people/anas/boundary-20.csv
"""
from __future__ import annotations

import argparse
import csv
import io
import os
import zipfile

import joblib
import numpy as np

HOME = os.path.expanduser("~/team14")
DATA = os.path.join(HOME, "data/her2-trastuzumab")
ANAS = os.path.join(HOME, "people/anas")
AA = "ACDEFGHIKLMNPQRSTVWY"
AA_IX = {a: i for i, a in enumerate(AA)}
WT = "WGGDGFYAMD"
VH_PRE = "EVQLVESGGGLVQPGGSLRLSCAASGFNIKDTYIHWVRQAPGKGLEWVARIYPTNGYTRYADSVKGRFTISADTSKNTAYLQMNSLRAEDTAVYYCSR"
VH_POST = "YWGQGTLVTVSS"
# measured binder rate by nearest-high distance, from fair_compare.py on unseen SPR rows
BINDER_RATE = {1: 0.97, 2: 0.64, 3: 0.37, 4: 0.10, 5: 0.03, 6: 0.04}


def ordinal(seqs):
    return np.array([[AA_IX[a] for a in s] for s in seqs], dtype=np.int8)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--min-diff", type=int, default=3)
    ap.add_argument("--out")
    args = ap.parse_args()

    z = zipfile.ZipFile(os.path.join(DATA, "tz_her2_facs_3classes_524346.csv.zip"))
    name = [n for n in z.namelist() if not n.startswith("__MACOSX")][0]
    highs = []
    with z.open(name) as fh:
        for r in csv.DictReader(io.TextIOWrapper(fh)):
            c = r["cdrh3"]
            if r["binding_class"] == "high" and len(c) == 10 and all(a in AA_IX for a in c):
                highs.append(c)
    H = ordinal(highs)
    print(f"known high binders: {len(H):,}")

    rows = list(csv.DictReader(open(os.path.join(ANAS, "legal-scored.csv"))))
    C = ordinal([r["cdrh3"] for r in rows])
    print(f"shortlist: {len(rows):,} legal candidates")

    nn = np.empty(len(C), dtype=np.int16)
    for i in range(0, len(C), 64):
        blk = C[i:i + 64]
        nn[i:i + 64] = (blk[:, None, :] != H[None, :, :]).sum(2).min(1)

    print("\nnearest-high distance across the shortlist")
    for d in sorted(set(nn.tolist())):
        n = int((nn == d).sum())
        print(f"   d={d}: {n:>5}   measured binder rate {BINDER_RATE.get(d, float('nan')):.2f}")

    for r, d in zip(rows, nn):
        r["nn_high"] = int(d)
        r["binder_rate"] = BINDER_RATE.get(int(d), 0.0)
        r["p_high"] = float(r["p_high"])

    rows.sort(key=lambda r: (r["nn_high"], -r["p_high"]))

    final, dropped = [], 0
    for r in rows:
        if any(sum(a != b for a, b in zip(r["cdrh3"], k["cdrh3"])) < args.min_diff for k in final):
            dropped += 1
            continue
        final.append(r)
        if len(final) >= args.top:
            break

    print(f"\nfinal {len(final)}, nearest legal first, {args.min_diff}+ apart "
          f"({dropped} dropped as too similar to a better one)\n")
    hdr = f"{'#':>3} {'CDRH3':<12} {'nn_high':>8} {'rate':>6} {'p_high':>7} {'mut':>4}"
    print(hdr)
    print("-" * len(hdr))
    for i, r in enumerate(final, 1):
        print(f"{i:>3} {r['cdrh3']:<12} {r['nn_high']:>8} {r['binder_rate']:>6.2f} "
              f"{r['p_high']:>7.3f} {r['n_mut_free']:>4}")

    at3 = sum(1 for r in final if r["nn_high"] == 3)
    print(f"\n{at3} of {len(final)} sit at d=3, the closest the rules allow.")
    print("Expected binders at the measured rate for their distance: "
          f"{sum(r['binder_rate'] for r in final):.1f} of {len(final)}.")
    print("\nThis is a prior from 528 SPR rows, not a promise about any one design.")

    if args.out:
        with open(args.out, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["cdrh3", "nn_high", "binder_rate", "p_high",
                                               "n_mut_free", "binder_sequence"],
                               extrasaction="ignore")
            w.writeheader()
            for r in final:
                r.setdefault("binder_sequence", VH_PRE + r["cdrh3"] + VH_POST)
                w.writerow(r)
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
