#!/usr/bin/env python3
"""Rank a run's refolded designs, measured data first.

report.py prints every number. This picks an order and says why, in the order the
team agreed after testing the design hypothesis against the 524,346 measured FACS
variants:

  1. hard gate   novelty, Cys, and our own margin. A rejected design is worth nothing.
  2. p_high      the FACS model (people/anas/facs_model.py). Measured signal, and the
                 only one that covers the >=4-mutation regime novelty forces us into.
                 External check on SPR, sequences the model never saw: AUC 0.764 for
                 binder-vs-no-fit, Spearman -0.43 against log10 KD.
  3. liabilities D102 and M107 both changed. Among grip-kept novelty-passing variants,
                 2/2 changed is 36.2 % high against 20.4 % for 1/2.
  4. min_ipae    structure confidence, last, because 21 measured non-binders in the
                 Champloo set score AF3 ipTM >= 0.7.
  5. diversity   near-identical loops are one bet, not several.

Grip (keeping W99/G103/F104/Y105) is reported but is NOT a gate: in the
novelty-passing regime it is worth 2.8 percentage points of P(high), so it breaks
ties rather than deciding them.

Usage
  py people/anas/rank.py                       the newest run
  py people/anas/rank.py 004                   that run
  py people/anas/rank.py --csv path/to/refold_metrics.csv
  py people/anas/rank.py 004 --top 10 --out people/anas/ranked-004.csv
"""
from __future__ import annotations

import argparse
import csv
import glob
import os
import sys

import joblib
import numpy as np

sys.path.insert(0, os.path.expanduser("~/team14/scripts"))
import novelty  # noqa: E402
import report  # noqa: E402

RUNS = os.path.expanduser("~/team14/runs")
MODEL = os.path.expanduser("~/team14/people/anas/facs_model.joblib")
AA = "ACDEFGHIKLMNPQRSTVWY"
AA_IX = {a: i for i, a in enumerate(AA)}

# Our own margin, stricter than the published limits (distance >= 2, identity <= 70 %).
# The task PDF says "under 70 %" and the slides say "at most 70 %"; a design on the
# line is a coin flip, and a rejected design scores nothing.
MIN_DIST = 3
MAX_IDENTITY = 60.0


def find_csv(which: str | None) -> str:
    pat = f"{RUNS}/*{which}*/out/scored-*/refold_metrics.csv" if which else f"{RUNS}/*/out/scored-*/refold_metrics.csv"
    hits = sorted(glob.glob(pat), key=os.path.getmtime, reverse=True)
    if not hits:
        sys.exit(f"no refold_metrics.csv found for {which or 'any run'}")
    return hits[0]


def p_high(seqs: list[str]) -> np.ndarray:
    if not os.path.exists(MODEL):
        print("  ! no facs_model.joblib; run people/anas/facs_model.py first", file=sys.stderr)
        return np.full(len(seqs), np.nan)
    bundle = joblib.load(MODEL)
    model, kind = bundle["model"], bundle["kind"]
    ok = [i for i, s in enumerate(seqs) if len(s) == 10 and all(a in AA_IX for a in s)]
    out = np.full(len(seqs), np.nan)
    if not ok:
        return out
    X = np.array([[AA_IX[a] for a in seqs[i]] for i in ok], dtype=np.int8)
    if kind == "logreg":
        from scipy import sparse
        n = len(ok)
        rows = np.repeat(np.arange(n), 10)
        cols = (np.tile(np.arange(10), n) * 20) + X.ravel()
        X = sparse.csr_matrix((np.ones(n * 10, dtype=np.float32), (rows, cols)), shape=(n, 200))
    out[ok] = model.predict_proba(X)[:, 2]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run", nargs="?", help="run name or fragment, e.g. 004")
    ap.add_argument("--csv", help="a refold_metrics.csv instead of a run")
    ap.add_argument("--top", type=int, default=0, help="keep at most this many after diversity")
    ap.add_argument("--out", help="write the ranked table here as csv")
    ap.add_argument("--min-diff", type=int, default=2, help="CDRH3 differences required between keepers")
    args = ap.parse_args()

    path = args.csv or find_csv(args.run)
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
    if not rows:
        sys.exit("no rows")
    print(f"{len(rows)} refolded design(s) from {path}\n")

    pool = novelty.load()
    provided = sum(a.shape[0] for a in pool.values())

    cand = []
    for r in rows:
        seq = (r.get("binder_sequence") or "").strip()
        if not seq:
            continue
        cdr = seq[report.CDRH3_FROM - 1:report.CDRH3_TO]
        dist, nearest = novelty.min_distance(cdr, pool)
        idt = novelty.identity_to_trastuzumab(cdr)
        verdict, detail = report.hypothesis(cdr)

        reject = []
        if dist < 2 or idt > 70.0:
            reject.append("official")
        if dist < MIN_DIST or idt > MAX_IDENTITY:
            reject.append("margin")
        if "C" in cdr:
            reject.append("Cys")

        def num(col):
            try:
                return float(r.get(col, ""))
            except (TypeError, ValueError):
                return float("nan")

        cand.append({
            "query_id": r.get("query_id", ""),
            "design": r.get("design", ""),
            "cdrh3": cdr, "sequence": seq,
            "min_dist": dist, "identity_tz": idt, "nearest_provided": nearest,
            "grip": verdict, "detail": detail,
            "liabilities_fixed": sum(1 for p, aa in report.LIABILITY.items()
                                     if cdr[p - report.CDRH3_FROM] != aa),
            "min_ipae": num("min_ipae"), "iptm": num("iptm"),
            "binder_plddt": num("binder_plddt"),
            "reject": ",".join(reject),
            "model": r.get("model", ""), "seed": r.get("seed", ""),
        })

    for c, p in zip(cand, p_high([c["cdrh3"] for c in cand])):
        c["p_high"] = p

    passing = [c for c in cand if not c["reject"]]
    print(f"gate: {len(passing)} of {len(cand)} pass novelty with our margin "
          f"(distance >= {MIN_DIST}, identity <= {MAX_IDENTITY:.0f} %, no Cys; "
          f"checked against {provided:,} provided CDRH3)")
    for c in cand:
        if c["reject"]:
            print(f"   out: {c['query_id']:<16} {c['cdrh3']}  dist {c['min_dist']} "
                  f"id {c['identity_tz']:.0f} %  [{c['reject']}]")

    passing.sort(key=lambda c: (
        -(c["p_high"] if c["p_high"] == c["p_high"] else -1),
        -c["liabilities_fixed"],
        c["min_ipae"] if c["min_ipae"] == c["min_ipae"] else 9e9,
    ))

    kept, dropped = [], []
    for c in passing:
        near = next((k for k in kept if sum(a != b for a, b in zip(c["cdrh3"], k["cdrh3"])) < args.min_diff), None)
        if near:
            dropped.append((c, near))
            continue
        kept.append(c)
        if args.top and len(kept) >= args.top:
            break

    print(f"\nranked, after dropping loops within {args.min_diff} of a better one")
    hdr = (f"{'#':>2} {'query':<16} {'CDRH3':<12} {'p_high':>7} {'liab':>5} "
           f"{'min_ipae':>9} {'iptm':>6} {'plddt':>7} {'dist':>5} {'%idTz':>6} grip")
    print(hdr)
    print("-" * len(hdr))
    for i, c in enumerate(kept, 1):
        ph = f"{c['p_high']:.3f}" if c["p_high"] == c["p_high"] else "-"
        print(f"{i:>2} {c['query_id']:<16} {c['cdrh3']:<12} {ph:>7} {c['liabilities_fixed']:>3}/2 "
              f"{c['min_ipae']:>9.3f} {c['iptm']:>6.3f} {c['binder_plddt']:>7.2f} "
              f"{c['min_dist']:>5} {c['identity_tz']:>5.0f}% {c['grip']}")
    for c, near in dropped:
        print(f"   dup: {c['query_id']:<16} {c['cdrh3']}  within {args.min_diff} of {near['cdrh3']}")

    if args.out:
        cols = ["query_id", "design", "cdrh3", "p_high", "liabilities_fixed", "grip",
                "min_dist", "identity_tz", "min_ipae", "iptm", "binder_plddt",
                "model", "seed", "sequence", "detail"]
        with open(args.out, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(kept)
        print(f"\nwrote {args.out}")

    print("\nreminder for SCORES.md: the wild type was measured eight times, "
          "0.0285 to 0.178 nM. Claim an improvement only against that spread.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
