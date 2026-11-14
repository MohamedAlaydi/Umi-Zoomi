#!/usr/bin/env python3
"""Collect Boltz-2 scores for a refold run and rank against the wild-type control.

refold-score needs an RFD4 design folder, which enumerated candidates do not have, so
we read Boltz-2's own scores.json instead. The numbers that matter are the interfaces
between the heavy chain (B) and the two HER2 chains (C, D): that is the binder docking
onto the target, as opposed to the Fv simply folding, which it will do regardless.

Everything is reported relative to trastuzumab_wt, which is in the same batch, through
the same model, at the same seed. Run 001 and 004 had no such arm, so their ipTM 0.96
could not be called good or bad.

  py people/anas/collect_refold.py 006
  py people/anas/collect_refold.py 006 --out people/anas/refold-006.csv
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys

HOME = os.path.expanduser("~/team14")
BINDER, TARGETS = 1, (2, 3)   # chain order in queries.json: A VL, B VH, C and D HER2


def pairwise(mat, i, j):
    """Mean of both directions, the matrix is not symmetric."""
    return (mat[i][j] + mat[j][i]) / 2.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run", help="run name or fragment, e.g. 006")
    ap.add_argument("--out")
    args = ap.parse_args()

    hits = sorted(glob.glob(f"{HOME}/runs/*{args.run}*"))
    if not hits:
        sys.exit(f"no run matching {args.run}")
    run = hits[0]
    manifest = {r["query_id"]: r for r in csv.DictReader(open(os.path.join(run, "manifest.csv")))}

    rows = []
    for qid, meta in manifest.items():
        sc = glob.glob(f"{run}/out/boltz2/{qid}/seed_*/*_scores.json")
        if not sc:
            rows.append({**meta, "status": "missing"})
            continue
        d = json.load(open(sc[0]))
        mat = d["chain_chain_interface_predicted_tm_score"]
        iface = [pairwise(mat, BINDER, t) for t in TARGETS]
        rows.append({
            **meta, "status": "ok",
            "iptm": d["interface_predicted_tm_score"],
            "ptm": d["predicted_tm_score"],
            "plddt": d["average_predicted_local_distance_difference_test"],
            "pde": d["global_predicted_distance_error"],
            "iface_min": min(iface),
            "iface_mean": sum(iface) / len(iface),
            "binder_ptm": d["chain_predicted_tm_score"][BINDER],
            "ranking": d["model_ranking_score"],
        })

    ok = [r for r in rows if r["status"] == "ok"]
    if not ok:
        sys.exit("no scores found; is the run finished?")
    wt = next((r for r in ok if r["query_id"] == "trastuzumab_wt"), None)

    ok.sort(key=lambda r: -r["iface_min"])

    print(f"{len(ok)} of {len(rows)} queries scored, from {run}\n")
    if wt:
        print(f"control trastuzumab_wt: iface_min {wt['iface_min']:.3f}  "
              f"iface_mean {wt['iface_mean']:.3f}  iptm {wt['iptm']:.3f}  plddt {wt['plddt']:.2f}")
        print("Anything below the control on iface_min is not a candidate, whatever its p_high.\n")

    hdr = (f"{'#':>3} {'query':<16} {'CDRH3':<12} {'p_high':>7} {'mut':>4} "
           f"{'iface_min':>10} {'iface_mean':>11} {'iptm':>6} {'plddt':>7} {'source':<22}")
    print(hdr)
    print("-" * len(hdr))
    for i, r in enumerate(ok, 1):
        mark = "  <-- control" if r["source"] == "control" else ""
        ph = f"{float(r['p_high']):.3f}" if r["p_high"] else "-"
        beats = ""
        if wt and r["source"] != "control":
            beats = " +" if r["iface_min"] > wt["iface_min"] else " -"
        print(f"{i:>3} {r['query_id']:<16} {r['cdrh3']:<12} {ph:>7} {r['n_mut']:>4} "
              f"{r['iface_min']:>10.3f} {r['iface_mean']:>11.3f} {r['iptm']:>6.3f} "
              f"{r['plddt']:>7.2f} {r['source']:<22}{beats}{mark}")

    if wt:
        cand = [r for r in ok if r["source"] != "control"]
        above = [r for r in cand if r["iface_min"] > wt["iface_min"]]
        print(f"\n{len(above)} of {len(cand)} candidates above the wild-type control on iface_min")
        gen = [r for r in ok if r["source"] == "control" and r["query_id"].startswith("r004")]
        if gen:
            best_gen = max(g["iface_min"] for g in gen)
            print(f"best run-004 generator design: iface_min {best_gen:.3f}; "
                  f"{sum(1 for r in cand if r['iface_min'] > best_gen)} of {len(cand)} ours beat it")

    if args.out:
        cols = ["query_id", "cdrh3", "p_high", "n_mut", "source", "iface_min", "iface_mean",
                "iptm", "ptm", "plddt", "pde", "binder_ptm", "ranking", "status"]
        with open(args.out, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(ok + [r for r in rows if r["status"] != "ok"])
        print(f"\nwrote {args.out}")

    print("\nStill true: confidence is not affinity. 21 measured non-binders in the Champloo")
    print("set score AF3 ipTM >= 0.7, so this ranks plausibility, not binding strength.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
