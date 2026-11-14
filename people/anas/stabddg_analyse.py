#!/usr/bin/env python3
"""Check StaB-ddG against the measured controls, then read the candidates.

The batch carried eight variants with measured SPR affinities spanning 0.023 to 886 nM.
If predicted binding ddG does not track log2(KD / KD_wt) on those, the predictions on
our 20 candidates carry no information and we say so.

Sign convention is read off the controls rather than assumed.

  py people/anas/stabddg_analyse.py scores.csv
"""
from __future__ import annotations

import csv
import math
import os
import sys

import numpy as np
from scipy import stats

ANAS = os.path.expanduser("~/team14/people/anas")
WT_KD = 0.152


def main() -> int:
    scores_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ANAS, "stabddg_scores.csv")
    sc = {r["variant_id"]: r for r in csv.DictReader(open(scores_path))}
    man = list(csv.DictReader(open(os.path.join(ANAS, "stabddg_manifest.csv"))))
    print(f"{len(sc)} scored variants, {len(man)} in the manifest")

    for r in man:
        s = sc.get(r["id"])
        r["ddg"] = float(s["binding_ddg_kcal_mol"]) if s else float("nan")
        r["se"] = float(s["mc_standard_error_kcal_mol"]) if s else float("nan")

    ctrl = [r for r in man if r["role"] == "control"]
    ctrl.sort(key=lambda r: float(r["kd_nM"]))
    print("\nCONTROLS: does the prediction track the measurement?\n")
    print(f"{'id':<8} {'CDRH3':<12} {'KD nM':>10} {'log2 vs wt':>11} {'ddG':>8} {'+/- SE':>8}")
    print("-" * 62)
    for r in ctrl:
        print(f"{r['id']:<8} {r['cdrh3']:<12} {float(r['kd_nM']):>10.3f} "
              f"{float(r['log2_vs_wt']):>11.2f} {r['ddg']:>8.3f} {r['se']:>8.3f}")

    x = np.array([float(r["log2_vs_wt"]) for r in ctrl])
    y = np.array([r["ddg"] for r in ctrl])
    pr = stats.pearsonr(x, y)
    sr = stats.spearmanr(x, y)
    print(f"\n  Pearson  r={pr.statistic:+.3f}  p={pr.pvalue:.3f}")
    print(f"  Spearman rho={sr.statistic:+.3f}  p={sr.pvalue:.3f}")
    print("  (positive = predicted ddG rises as measured affinity worsens, the expected sign)")

    med_se = float(np.median([r["se"] for r in man]))
    print(f"\n  median Monte Carlo SE across the batch: {med_se:.3f} kcal/mol")
    print(f"  spread of control ddG: {y.min():+.3f} to {y.max():+.3f}, "
          f"range {y.max()-y.min():.3f}")
    if y.max() - y.min() < 3 * med_se:
        print("  the controls span less than 3 SE, so the tool cannot separate a 6000-fold")
        print("  affinity range here. Treat candidate ddG as uninformative.")

    cand = [r for r in man if r["role"] == "candidate"]
    cand.sort(key=lambda r: r["ddg"])
    print(f"\nCANDIDATES, best predicted binding first ({len(cand)})\n")
    print(f"{'#':>3} {'id':<8} {'CDRH3':<12} {'ddG':>8} {'+/- SE':>8} {'|ddG|>2SE':>10} {'p_high':>7}")
    print("-" * 62)
    for i, r in enumerate(cand, 1):
        sig = "yes" if abs(r["ddg"]) > 2 * r["se"] else "no"
        print(f"{i:>3} {r['id']:<8} {r['cdrh3']:<12} {r['ddg']:>8.3f} {r['se']:>8.3f} "
              f"{sig:>10} {float(r['p_high']):>7.3f}")

    better = [r for r in cand if r["ddg"] < 0]
    sigbet = [r for r in better if abs(r["ddg"]) > 2 * r["se"]]
    print(f"\n  predicted better than trastuzumab: {len(better)} of {len(cand)}")
    print(f"  and beyond twice their own Monte Carlo error: {len(sigbet)}")
    for r in sigbet:
        print(f"     {r['id']} {r['cdrh3']} ddG {r['ddg']:+.3f} +/- {r['se']:.3f}")

    with open(os.path.join(ANAS, "stabddg-joined.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "cdrh3", "role", "ddg", "se", "p_high",
                                           "nn_high", "kd_nM", "log2_vs_wt"],
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(ctrl + cand)
    print(f"\nwrote {ANAS}/stabddg-joined.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
