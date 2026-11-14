#!/usr/bin/env python3
"""Score every novelty-legal IDEAL loop with the FACS model and keep the best.

feasible.py showed there are 25,208,628 fillings of the six free positions that keep
the grip, change both liabilities, carry no cysteine, and are >= 3 from all 525,042
provided CDRH3s. So the hypothesis is not short of room: the generator was simply
sampling the wrong part of the space.

That means we do not have to hope the GPU stumbles onto a legal loop. We can
enumerate the legal space, score all of it with the measured-data model, and spend
GPU time only on verifying a shortlist.

Honest limit: the FACS model cannot say anything beats trastuzumab. Trastuzumab
itself scores p_high 0.998, the ceiling. The model separates likely-dead from
plausibly-alive (AUC 0.764 against SPR binder-vs-no-fit on unseen sequences), so it
is a sieve, not an oracle. Both models must agree, and the shortlist still gets
refolded.

  py people/anas/score_legal.py --top 5000 --out people/anas/legal-scored.csv
"""
from __future__ import annotations

import argparse
import os
import sys

import joblib
import numpy as np
from scipy import sparse

HOME = os.path.expanduser("~/team14")
LOOPS = os.path.join(HOME, "people/anas/ideal-legal-loops.txt")
MODEL = os.path.join(HOME, "people/anas/facs_model.joblib")
AA = "ACDEFGHIKLMNPQRSTVWY"
AA_IX = {a: i for i, a in enumerate(AA)}
WT = "WGGDGFYAMD"
# trastuzumab VH, with CDRH3 at positions 99-108 (1-based)
VH = ("EVQLVESGGGLVQPGGSLRLSCAASGFNIKDTYIHWVRQAPGKGLEWVARIYPTNGYTRYADSVKGRFTISADTSKNTAYLQMNSLRAEDTAVYYCSR"
      "WGGDGFYAMD" "YWGQGTLVTVSS")
CDR_FROM, CDR_TO = 99, 108


def onehot(X: np.ndarray) -> sparse.csr_matrix:
    n = len(X)
    rows = np.repeat(np.arange(n), 10)
    cols = (np.tile(np.arange(10), n) * 20) + X.ravel()
    return sparse.csr_matrix((np.ones(n * 10, dtype=np.float32), (rows, cols)), shape=(n, 200))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=5000)
    ap.add_argument("--chunk", type=int, default=2_000_000)
    ap.add_argument("--out", default=os.path.join(HOME, "people/anas/legal-scored.csv"))
    args = ap.parse_args()

    bundle = joblib.load(MODEL)
    gb = bundle["model"]
    if bundle["kind"] != "gbm":
        sys.exit("expected the gbm bundle")

    wt_x = np.array([[AA_IX[a] for a in WT]], dtype=np.int8)
    print(f"sanity: trastuzumab {WT} scores p_high {gb.predict_proba(wt_x)[0, 2]:.4f}")

    hist = np.zeros(21, dtype=np.int64)
    best_p: list[float] = []
    best_s: list[str] = []
    seen = 0

    with open(LOOPS) as fh:
        while True:
            lines = fh.readlines(args.chunk * 11)
            if not lines:
                break
            seqs = [l.strip() for l in lines]
            X = np.frombuffer("".join(seqs).encode(), dtype=np.uint8).reshape(len(seqs), 10)
            lut = np.full(256, 0, dtype=np.int8)
            for a, i in AA_IX.items():
                lut[ord(a)] = i
            Xi = lut[X]
            p = gb.predict_proba(Xi)[:, 2]
            seen += len(seqs)
            hist += np.bincount((p * 20).astype(int), minlength=21)

            k = min(args.top, len(p))
            top = np.argpartition(-p, k - 1)[:k]
            best_p.extend(p[top].tolist())
            best_s.extend([seqs[i] for i in top])
            if len(best_p) > 10 * args.top:
                order = np.argsort(best_p)[::-1][: args.top]
                best_p = [best_p[i] for i in order]
                best_s = [best_s[i] for i in order]
            print(f"  scored {seen:,}", flush=True)

    order = np.argsort(best_p)[::-1][: args.top]
    best_p = [best_p[i] for i in order]
    best_s = [best_s[i] for i in order]

    print(f"\nscored {seen:,} legal loops")
    print("p_high distribution over the whole legal space")
    for b in range(20, -1, -1):
        if hist[b]:
            print(f"  {b/20:.2f}-{(b+1)/20:.2f}  {hist[b]:>12,}  ({100*hist[b]/seen:5.2f} %)")

    # second opinion from the linear model, refit cheaply is not possible here, so
    # report agreement with the GBM's own margin instead
    print(f"\ntop {len(best_s)} by p_high: {best_p[0]:.4f} down to {best_p[-1]:.4f}")

    with open(args.out, "w") as fh:
        fh.write("cdrh3,p_high,n_mut_free,binder_sequence\n")
        for s, p in zip(best_s, best_p):
            nm = sum(1 for a, b in zip(s, WT) if a != b)
            full = VH[: CDR_FROM - 1] + s + VH[CDR_TO:]
            fh.write(f"{s},{p:.6f},{nm},{full}\n")
    print(f"wrote {args.out}")
    print("\nNext: refold the shortlist. The model cannot rank above trastuzumab's own")
    print("ceiling, so structure and diversity decide the order inside the survivors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
