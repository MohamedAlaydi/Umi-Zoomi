#!/usr/bin/env python3
"""Build the three Boltz-2 query sets for run 009 (multi-seed refold + calibration).

ONE common protocol for everything folded here:
  - template          runs/006-anas-enumerated-top40 prepared/holo/template.cif
                      (byte-identical to run 004's; sha256 719541a9bd7fb1cd...)
  - chains            A = trastuzumab VL (fixed), B = VH_PRE + CDRH3 + VH_POST,
                      C and D = HER2 taken verbatim from run 004's queries.json
                      -- exactly people/anas/build_refold.py's construction
  - container/flags   same as run 006 (see run_multiseed.sh)

Query sets
  A  queries_cand.json    every unique CDRH3 that has a structure in
                          runs/008-claude-first-pass/first_pass_candidates.csv
                          (60 unique loops over 66 rows, trastuzumab_wt included)
                          -> seeds 1,2,3,4,5
  B  queries_cand42.json  the subset that has no seed-42 fold under THIS template
                          (runs 001/004/005 rows) + 3 run-006 loops re-folded to
                          verify bit-level determinism
                          -> seed 42
  C  queries_calib.json   30 MEASURED SPR sequences, KD-stratified (see below)
                          -> seeds 42,1,2

Calibration sampling procedure (fixed, documented, not tuned):
  source   data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv
           (the HER2/trastuzumab SPR table; data/spr-supplementary is the
           Champloo nanobody set, a different construct, so it cannot be folded
           under this protocol and is not used)
  keep     10-mer CDRH3 only, so the folded construct is identical in length to
           every candidate; vh_sequence in that file is byte-equal to
           VH_PRE+cdrh3+VH_POST for all 740 of them (checked).
  WT_KD    median of the 8 wild-type replicate rows
  dedup    one row per unique CDRH3 (median KD if measured more than once);
           the wild-type CDRH3 itself is excluded (it is already in set A)
  strata   binder       quantified_binding and KD <= 2*WT_KD
           intermediate quantified_binding and 2*WT_KD < KD < 100 nM
           weak         5 x quantified_binding with KD >= 100 nM
                        + 5 x binding_result == no_reportable_kd
  draw     numpy.random.default_rng(20261114).choice, without replacement, from
           each stratum sorted lexicographically by CDRH3 (so the draw is
           reproducible regardless of file row order)
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import statistics
import sys

import numpy as np

HOME = os.path.expanduser("~/team14")
DOCS = os.path.join(HOME, "data/rfd4-proteina/docs")
RUN = os.path.join(HOME, "runs/009-claude-multiseed-refold")
REL = "runs/009-claude-multiseed-refold"
REF006 = os.path.join(HOME, "runs/006-anas-enumerated-top40/out/prepared/holo")
REF004 = os.path.join(HOME, "runs/004-mohamed-her2-novel-n40/out/prepared/holo")
FIRSTPASS = os.path.join(HOME, "runs/008-claude-first-pass/first_pass_candidates.csv")
SPR = os.path.join(HOME, "data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv")

VL = ("DIQMTQSPSSLSASVGDRVTITCRASQDVNTAVAWYQQKPGKAPKLLIYSASFLYSGVPSRFSGSRSGTDFTLTISS"
      "LQPEDFATYYCQQHYTTPPTFGQGTKVEIK")
VH_PRE = ("EVQLVESGGGLVQPGGSLRLSCAASGFNIKDTYIHWVRQAPGKGLEWVARIYPTNGYTRYADSVKGRFTISADTSKN"
          "TAYLQMNSLRAEDTAVYYCSR")
VH_POST = "YWGQGTLVTVSS"
WT = "WGGDGFYAMD"

RNG_SEED = 20261114
DETERMINISM_CHECK = ["anas_001", "anas_027", "trastuzumab_wt"]  # run-006 ids, seed 42 exists


def her2_chains() -> tuple[dict, dict]:
    q = json.load(open(os.path.join(REF004, "queries.json")))["queries"][0]
    by = {c["chain_id"]: c for c in q["chains"]}
    return by["C"], by["D"]


def query(qid: str, cdr: str, chain_c: dict, chain_d: dict) -> dict:
    return {"query_id": qid, "chains": [
        {"chain_id": "A", "sequence": VL, "msa_path": None},
        {"chain_id": "B", "sequence": VH_PRE + cdr + VH_POST, "msa_path": None},
        chain_c, chain_d,
    ]}


def pick_calibration() -> list[dict]:
    rows = [r for r in csv.DictReader(open(SPR)) if len(r["cdrh3"]) == 10]
    wt_kd = statistics.median(
        float(r["kd_nM"]) for r in rows
        if r["cdrh3"] == WT and r["binding_result"] == "quantified_binding")

    by_cdr: dict[str, list[dict]] = {}
    for r in rows:
        by_cdr.setdefault(r["cdrh3"], []).append(r)

    uniq = []
    for cdr, rs in by_cdr.items():
        if cdr == WT:
            continue
        q = [float(r["kd_nM"]) for r in rs if r["binding_result"] == "quantified_binding"]
        res = {"cdrh3": cdr, "n_spr_rows": len(rs),
               "binding_result": rs[0]["binding_result"] if len(set(
                   r["binding_result"] for r in rs)) == 1 else "mixed"}
        if q:
            res["kd_nM"] = statistics.median(q)
            res["binding_result"] = "quantified_binding"
        else:
            res["kd_nM"] = ""
        uniq.append(res)

    def has_kd(r):
        return r["kd_nM"] != ""

    binders = [r for r in uniq if has_kd(r) and r["kd_nM"] <= 2 * wt_kd]
    # "or the best available": only 9 unique non-WT loops sit at or under 2*WT_KD,
    # so the stratum is topped up to 10 with the next-best measured KD.
    topup_bar = 2 * wt_kd
    if len(binders) < 10:
        rest = sorted((r for r in uniq if has_kd(r) and r["kd_nM"] > 2 * wt_kd),
                      key=lambda r: r["kd_nM"])
        need = 10 - len(binders)
        binders = binders + rest[:need]
        topup_bar = binders[-1]["kd_nM"] if rest else topup_bar
        print(f"  binder stratum topped up with the {need} next-best measured KD; "
              f"effective binder bar {topup_bar:.4f} nM")
    binder_cdrs = {r["cdrh3"] for r in binders}
    inter = [r for r in uniq if has_kd(r) and r["cdrh3"] not in binder_cdrs
             and 2 * wt_kd < r["kd_nM"] < 100.0]
    weak_q = [r for r in uniq if has_kd(r) and r["kd_nM"] >= 100.0]
    nonbind = [r for r in uniq if not has_kd(r) and r["binding_result"] == "no_reportable_kd"]

    print(f"WT_KD (median of 8 replicates) = {wt_kd:.4f} nM; binder bar = {2*wt_kd:.4f} nM")
    print(f"unique non-WT 10-mers: {len(uniq)}  "
          f"binder {len(binders)}  intermediate {len(inter)}  "
          f"weak(KD>=100) {len(weak_q)}  no_reportable_kd {len(nonbind)}")

    rng = np.random.default_rng(RNG_SEED)

    def draw(pool, k, label):
        pool = sorted(pool, key=lambda r: r["cdrh3"])
        if len(pool) <= k:
            sel = pool
            print(f"  {label}: pool {len(pool)} <= {k}, taking all ({len(sel)})")
        else:
            idx = rng.choice(len(pool), size=k, replace=False)
            sel = [pool[i] for i in sorted(idx)]
            print(f"  {label}: drew {k} of {len(pool)}")
        for r in sel:
            r["stratum"] = label
        return sel

    sel = draw(binders, 10, "binder") + draw(inter, 10, "intermediate") \
        + draw(weak_q, 5, "weak_quantified") + draw(nonbind, 5, "non_binding")
    for i, r in enumerate(sel, 1):
        r["query_id"] = f"calib_{i:03d}"
        r["wt_kd_nM"] = f"{wt_kd:.6f}"
        r["binder_label"] = ("binder" if r["stratum"] == "binder"
                             else "non_binder" if r["stratum"] in
                             ("weak_quantified", "non_binding") else "intermediate")
    return sel


def main() -> int:
    holo = os.path.join(DOCS, REL, "prepared", "holo")
    os.makedirs(holo, exist_ok=True)
    shutil.copy(os.path.join(REF006, "template.cif"), os.path.join(holo, "template.cif"))
    chain_c, chain_d = her2_chains()

    fp = [r for r in csv.DictReader(open(FIRSTPASS)) if r["has_structure"] == "TRUE"]
    print(f"first-pass structured rows: {len(fp)}")

    # one query per unique CDRH3; query_id = the first candidate_id that carries it,
    # with the run-006 id preferred so the determinism check lines up with run 006.
    order = {"006": 0, "004": 1, "005": 2, "001": 3}
    by_cdr: dict[str, list[dict]] = {}
    for r in fp:
        by_cdr.setdefault(r["cdrh3"], []).append(r)
    cand = []
    for cdr in sorted(by_cdr):
        rs = sorted(by_cdr[cdr], key=lambda r: (order.get(r["run"], 9), r["query_id"]))
        cand.append({"query_id": rs[0]["query_id"], "cdrh3": cdr,
                     "rep_run": rs[0]["run"],
                     "candidate_ids": ";".join(r["candidate_id"] for r in rs),
                     "n_rows": len(rs)})
    assert len({c["query_id"] for c in cand}) == len(cand), "query_id collision"
    print(f"unique CDRH3 to fold: {len(cand)}  (WT present: "
          f"{any(c['cdrh3'] == WT for c in cand)})")

    # set B: seed 42 under THIS template is new for runs 001/004/005 loops
    s42 = [c for c in cand if c["rep_run"] != "006"]
    det = [c for c in cand if c["query_id"] in DETERMINISM_CHECK]
    s42 = s42 + [c for c in det if c not in s42]
    print(f"seed-42 set: {len(s42)} ({len(s42)-len(det)} new + {len(det)} determinism checks)")

    calib = pick_calibration()
    print(f"calibration set: {len(calib)}")
    cand_cdrs = {c["cdrh3"] for c in cand}
    overlap = [c["cdrh3"] for c in calib if c["cdrh3"] in cand_cdrs]
    print(f"calibration/candidate CDRH3 overlap: {len(overlap)}")

    for name, rows in [("queries_cand.json", cand),
                       ("queries_cand42.json", s42),
                       ("queries_calib.json", calib)]:
        obj = {"queries": [query(r["query_id"], r["cdrh3"], chain_c, chain_d) for r in rows]}
        with open(os.path.join(holo, name), "w") as fh:
            json.dump(obj, fh)
        print(f"wrote {holo}/{name}  ({len(obj['queries'])} queries)")

    with open(os.path.join(RUN, "manifest_candidates.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["query_id", "cdrh3", "rep_run",
                                           "candidate_ids", "n_rows"])
        w.writeheader()
        w.writerows(cand)
    cols = ["query_id", "cdrh3", "stratum", "binder_label", "kd_nM", "wt_kd_nM",
            "binding_result", "n_spr_rows"]
    with open(os.path.join(RUN, "manifest_calibration.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(calib)
    with open(os.path.join(RUN, "manifest_seed42.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["query_id", "cdrh3", "rep_run",
                                           "candidate_ids", "n_rows"])
        w.writeheader()
        w.writerows(s42)
    print(f"wrote manifests under {RUN}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
