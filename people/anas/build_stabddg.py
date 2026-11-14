#!/usr/bin/env python3
"""Build the StaB-ddG parameters for our 20 candidates plus measured controls.

StaB-ddG predicts the change in binding free energy for named point mutations across
two partner sides. Our designs are 4 to 6 point mutations of trastuzumab's CDRH3
against HER2, so this is the one tool we have that speaks to criterion 1 directly:
better or worse binding than the drug, not "does it look like a binder".

The batch carries controls with measured SPR affinities, spanning the range, so the
tool can be checked before it is believed. If predicted ddG does not track the
measured log ratio on those, the predictions on our candidates mean nothing either.

  py people/anas/build_stabddg.py --out /tmp/stabddg_params.json
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os

HOME = os.path.expanduser("~/team14")
DATA = os.path.join(HOME, "data/her2-trastuzumab")
ANAS = os.path.join(HOME, "people/anas")
WT = "WGGDGFYAMD"
CDR_FROM = 99
WT_KD = 0.152   # the judged baseline, row 1 of the SPR table


def mutations(cdr: str) -> list[dict]:
    return [{"chain": "B", "residue_number": CDR_FROM + i, "insertion_code": "",
             "wild_type": WT[i], "mutant": cdr[i]}
            for i in range(len(WT)) if cdr[i] != WT[i]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/stabddg_params.json")
    ap.add_argument("--controls", type=int, default=8)
    args = ap.parse_args()

    cand = list(csv.DictReader(open(os.path.join(ANAS, "boundary-20.csv"))))
    print(f"candidates: {len(cand)}")

    # measured controls, spread over the affinity range, excluding the wild type itself
    spr = [r for r in csv.DictReader(open(os.path.join(DATA, "trastuzumab_her2_spr_all_768.csv")))
           if r["kd_nM"] and len(r["cdrh3"]) == 10 and r["cdrh3"] != WT]
    spr.sort(key=lambda r: float(r["kd_nM"]))
    picks = []
    n = len(spr)
    for frac in [0.0, 0.01, 0.05, 0.2, 0.4, 0.6, 0.8, 0.99][:args.controls]:
        r = spr[min(int(frac * n), n - 1)]
        if r["cdrh3"] not in [p["cdrh3"] for p in picks]:
            picks.append(r)
    print(f"controls: {len(picks)} measured variants, KD "
          f"{float(picks[0]['kd_nM']):.3f} to {float(picks[-1]['kd_nM']):.1f} nM")

    variants, manifest = [], []
    for i, r in enumerate(cand, 1):
        vid = f"cand{i:02d}"
        variants.append({"id": vid, "mutations": mutations(r["cdrh3"])})
        manifest.append({"id": vid, "cdrh3": r["cdrh3"], "role": "candidate",
                         "p_high": r["p_high"], "nn_high": r["nn_high"], "kd_nM": ""})
    for i, r in enumerate(picks, 1):
        vid = f"ctrl{i:02d}"
        variants.append({"id": vid, "mutations": mutations(r["cdrh3"])})
        manifest.append({"id": vid, "cdrh3": r["cdrh3"], "role": "control",
                         "p_high": "", "nn_high": "",
                         "kd_nM": r["kd_nM"],
                         "log2_vs_wt": f"{math.log2(float(r['kd_nM']) / WT_KD):.3f}"})

    for v in variants:
        assert v["mutations"], f"{v['id']} has no mutations"
        assert len({m['residue_number'] for m in v['mutations']}) == len(v['mutations'])
    assert len({v["id"] for v in variants}) == len(variants)

    params = {
        "pdb_file": "complex.pdb",
        "partner_a": ["A", "B"],      # the Fv
        "partner_b": ["C", "D"],      # HER2 domain IV
        "variants": variants,
    }
    json.dump(params, open(args.out, "w"), indent=1)
    with open(os.path.join(ANAS, "stabddg_manifest.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "cdrh3", "role", "p_high", "nn_high",
                                           "kd_nM", "log2_vs_wt"], extrasaction="ignore")
        w.writeheader()
        w.writerows(manifest)

    print(f"\n{len(variants)} variants, {sum(len(v['mutations']) for v in variants)} mutations total")
    print(f"  partner_a {params['partner_a']} (Fv), partner_b {params['partner_b']} (HER2)")
    print(f"wrote {args.out} and {ANAS}/stabddg_manifest.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
