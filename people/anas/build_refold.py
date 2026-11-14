#!/usr/bin/env python3
"""Build a Boltz-2 refold job for the enumerated shortlist, with controls.

The candidates came from feasible.py + score_legal.py, not from RFD4, so there is no
design folder and refold-score's RMSD-to-design columns do not apply. We read Boltz-2's
own scores instead and rank on the binder-to-target interface ipTM and pLDDT.

Two controls go in the same batch, which run 001 and 004 did not have:
  trastuzumab_wt   the wild-type CDRH3, the baseline every design is judged against
  r004_*           the best designs the generator produced, so ours are compared
                   against the generator on the same model, same batch, same seed

  py people/anas/build_refold.py --n 40 --label enumerated-top40
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys

HOME = os.path.expanduser("~/team14")
DOCS = os.path.join(HOME, "data/rfd4-proteina/docs")
SCORED = os.path.join(HOME, "people/anas/legal-scored.csv")
REF_RUN = os.path.join(HOME, "runs/004-mohamed-her2-novel-n40/out/prepared/holo")

VL = ("DIQMTQSPSSLSASVGDRVTITCRASQDVNTAVAWYQQKPGKAPKLLIYSASFLYSGVPSRFSGSRSGTDFTLTISS"
      "LQPEDFATYYCQQHYTTPPTFGQGTKVEIK")
VH_PRE = "EVQLVESGGGLVQPGGSLRLSCAASGFNIKDTYIHWVRQAPGKGLEWVARIYPTNGYTRYADSVKGRFTISADTSKNTAYLQMNSLRAEDTAVYYCSR"
VH_POST = "YWGQGTLVTVSS"
WT = "WGGDGFYAMD"


def load_chains_from(path: str) -> tuple[dict, dict]:
    """Take HER2 chains C and D verbatim from a prepared queries.json."""
    q = json.load(open(os.path.join(path, "queries.json")))["queries"][0]
    by_id = {c["chain_id"]: c for c in q["chains"]}
    return by_id["C"], by_id["D"]


def diverse(rows: list[dict], n: int, min_diff: int) -> list[dict]:
    kept: list[dict] = []
    for r in rows:
        if all(sum(a != b for a, b in zip(r["cdrh3"], k["cdrh3"])) >= min_diff for k in kept):
            kept.append(r)
            if len(kept) >= n:
                break
    return kept


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--min-diff", type=int, default=3)
    ap.add_argument("--label", default="enumerated-top40")
    ap.add_argument("--who", default="anas")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(SCORED)))
    print(f"shortlist in: {len(rows)} scored candidates, p_high "
          f"{rows[0]['p_high']} down to {rows[-1]['p_high']}")

    picked = diverse(rows, args.n, args.min_diff)
    print(f"picked {len(picked)} with pairwise CDRH3 difference >= {args.min_diff}")

    chain_c, chain_d = load_chains_from(REF_RUN)

    # controls: the wild type, and the generator's three best from run 004 by p_high
    controls = [("trastuzumab_wt", WT)]
    for qid, cdr in [("r004_cdrh3_4", "YWSLHYYAMD"),
                     ("r004_cdrh3_3", "WASSSEYYFD"),
                     ("r004_cdrh3_31", "WHSSYDYYFD")]:
        controls.append((qid, cdr))

    queries = []
    manifest = []
    for i, r in enumerate(picked, 1):
        qid = f"anas_{i:03d}"
        queries.append((qid, r["cdrh3"]))
        manifest.append({"query_id": qid, "cdrh3": r["cdrh3"], "p_high": r["p_high"],
                         "n_mut": r["n_mut_free"], "source": "enumerated+facs_model"})
    for qid, cdr in controls:
        queries.append((qid, cdr))
        manifest.append({"query_id": qid, "cdrh3": cdr, "p_high": "",
                         "n_mut": sum(1 for a, b in zip(cdr, WT) if a != b),
                         "source": "control"})

    run = subprocess.run([os.path.join(HOME, "scripts/newrun"), args.who, args.label],
                         capture_output=True, text=True, check=True).stdout.strip()
    rel = "runs/" + os.path.basename(run)
    holo = os.path.join(DOCS, rel, "prepared", "holo")
    os.makedirs(holo, exist_ok=True)
    shutil.copy(os.path.join(REF_RUN, "template.cif"), os.path.join(holo, "template.cif"))

    out = {"queries": []}
    for qid, cdr in queries:
        out["queries"].append({"query_id": qid, "chains": [
            {"chain_id": "A", "sequence": VL, "msa_path": None},
            {"chain_id": "B", "sequence": VH_PRE + cdr + VH_POST, "msa_path": None},
            chain_c, chain_d,
        ]})
    json.dump(out, open(os.path.join(holo, "queries.json"), "w"))

    with open(os.path.join(run, "manifest.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["query_id", "cdrh3", "p_high", "n_mut", "source"])
        w.writeheader()
        w.writerows(manifest)

    print(f"\n{len(out['queries'])} queries ({len(picked)} candidates + {len(controls)} controls)")
    print(f"  run dir   {run}")
    print(f"  queries   {holo}/queries.json")
    print(f"  manifest  {run}/manifest.csv")
    print(f"\nREL={rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
