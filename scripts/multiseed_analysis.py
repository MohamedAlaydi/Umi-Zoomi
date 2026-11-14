#!/usr/bin/env python3
"""Multi-seed Boltz-2 noise floor + calibration of structural metrics against SPR KD.

New script for run 009. It does NOT call people/anas/collect_refold.py; the
score collector below is written from scratch against the *_scores.json files so
that several output trees and several seeds can be pooled, and so that the
reused run-006 seed-42 folds are explicitly provenance-tagged.

What it computes, per (sequence, seed):
  from <name>_seed_<s>_sample_1_scores.json
      iptm            interface_predicted_tm_score
      plddt           average_predicted_local_distance_difference_test (complex)
      iface_min/mean  min / mean of the chain-B<->C and chain-B<->D interface ipTM,
                      each averaged over both matrix directions
                      (people/anas/collect_refold.py's recipe, reproduced here)
      ptm, pde, binder_ptm, ranking
  from <name>_seed_<s>_sample_1_model.cif (geometry, biotite Shrake-Rupley + cell list)
      bsa_fv_her2     buried surface area, Fv (chains A+B) against HER2 (C+D), A^2
      bsa_vh_her2     the same for the heavy chain alone against HER2, A^2
      n_iface_res_45  residues with a heavy-atom partner within 4.5 A across the
                      Fv/HER2 interface (both sides), plus the two one-sided counts
      n_contact_pairs antibody-residue x HER2-residue pairs within 4.5 A
      cdrh3_share     share of those pairs contributed by VH 99-108
      cdrh3_rmsd_1n8z backbone (N,CA,C,O) RMSD of VH 99-108 to 1N8Z after
                      superimposing the VH framework CAs (chain B minus 99-108)

Reference structure for the RMSD: trastuzumab_epitope/raw_1N8Z/provided_her2_fv_1n8z.cif,
the deposited-1N8Z crop that the survey verified atom-identical to raw_1N8Z/1n8z.cif
(RMSD 0.0 A over 2,584 atoms). It is used in preference to 1n8z.cif because the
deposited file numbers the heavy chain in Kabat with insertion codes (100A/100B/100C),
which makes residue identity ambiguous for an integer-keyed reader, while the crop
numbers chain B 1-120 exactly like the folded construct.

  py scripts/multiseed_analysis.py              full run
  py scripts/multiseed_analysis.py --no-geom    scores only (fast re-check)
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import os
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

HOME = os.path.expanduser("~/team14")
DOCS = os.path.join(HOME, "data/rfd4-proteina/docs")
RUN = os.path.join(HOME, "runs/009-claude-multiseed-refold")
REL009 = os.path.join(DOCS, "runs/009-claude-multiseed-refold")
RUN006 = os.path.join(HOME, "runs/006-anas-enumerated-top40/out/boltz2")
FIRSTPASS = os.path.join(HOME, "runs/008-claude-first-pass/first_pass_candidates.csv")
REF_CIF = os.path.expanduser(
    "~/trastuzumab_epitope/raw_1N8Z/provided_her2_fv_1n8z.cif")
GEOM_CACHE = os.path.join(RUN, "geometry_cache.json")

CAND_SEEDS = [1, 2, 3, 4, 5, 42]
CALIB_SEEDS = [1, 2, 42]
WT_QID = "trastuzumab_wt"
WT_CDRH3 = "WGGDGFYAMD"
CDRH3_RES = list(range(99, 109))
AB_CHAINS = ("A", "B")
HER2_CHAINS = ("C", "D")
CUTOFF = 4.5
SASA_POINTS = 200
RNG_SEED = 20261114
N_BOOT = 2000
NONINF_MARGIN = -0.03
BH_ALPHA = 0.10

# metrics summarised per sequence across seeds
SEED_METRICS = ["iface_min", "iface_mean", "iptm", "plddt", "bsa_fv_her2",
                "bsa_vh_her2", "n_iface_res_45", "n_contact_pairs",
                "cdrh3_share", "cdrh3_rmsd_1n8z"]
# the four the brief names for the mean/SD/min/max block
CORE4 = ["iface_min", "iface_mean", "iptm", "bsa_fv_her2"]
# the four calibration scorers named in the brief
CALIB_METRICS = ["iface_min", "iface_mean", "iptm", "bsa_fv_her2"]


# --------------------------------------------------------------------------
# score collection
# --------------------------------------------------------------------------
def pairwise(mat, i, j):
    """Mean of both directions; the chain-chain ipTM matrix is not symmetric."""
    return (mat[i][j] + mat[j][i]) / 2.0


def read_scores(path: str) -> dict:
    d = json.load(open(path))
    mat = d["chain_chain_interface_predicted_tm_score"]
    iface = [pairwise(mat, 1, 2), pairwise(mat, 1, 3)]
    return {
        "iptm": d["interface_predicted_tm_score"],
        "plddt": d["average_predicted_local_distance_difference_test"],
        "ptm": d["predicted_tm_score"],
        "pde": d["global_predicted_distance_error"],
        "binder_ptm": d["chain_predicted_tm_score"][1],
        "ranking": d["model_ranking_score"],
        "iface_min": min(iface),
        "iface_mean": sum(iface) / len(iface),
    }


def scan_tree(root: str, provenance: str) -> list[dict]:
    """Every <root>/<query_id>/seed_<n>/*_scores.json under one output tree."""
    out = []
    for sc in sorted(glob.glob(os.path.join(root, "*", "seed_*", "*_scores.json"))):
        seed = int(os.path.basename(os.path.dirname(sc)).split("_", 1)[1])
        qid = os.path.basename(os.path.dirname(os.path.dirname(sc)))
        cif = sc.replace("_scores.json", "_model.cif")
        out.append({"query_id": qid, "seed": seed, "scores_path": sc,
                    "cif_path": cif if os.path.exists(cif) else "",
                    "provenance": provenance, **read_scores(sc)})
    return out


def sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------
_REF = {}


def _load_ref():
    if "bb" in _REF:
        return _REF
    import biotite.structure.io.pdbx as pdbx
    arr = pdbx.get_structure(pdbx.CIFFile.read(REF_CIF), model=1)
    arr = arr[np.isin(arr.element, ["C", "N", "O", "S"])]
    b = arr[arr.chain_id == "B"]
    loop = np.isin(b.res_id, CDRH3_RES)
    fw = b[(~loop) & (b.atom_name == "CA")]
    bb = b[loop & np.isin(b.atom_name, ["N", "CA", "C", "O"])]
    _REF["fw"] = {int(r): c for r, c in zip(fw.res_id, fw.coord)}
    _REF["bb"] = {(int(r), str(a)): c for r, a, c in
                  zip(bb.res_id, bb.atom_name, bb.coord)}
    return _REF


def _kabsch(mob: np.ndarray, ref: np.ndarray):
    cm, cr = mob.mean(0), ref.mean(0)
    u, _, vt = np.linalg.svd((mob - cm).T @ (ref - cr))
    d = np.sign(np.linalg.det(vt.T @ u.T))
    rot = vt.T @ np.diag([1.0, 1.0, d]) @ u.T
    return rot, cr - rot @ cm


def geometry(cif_path: str) -> dict:
    """Interface descriptors for one Boltz-2 model.cif. Pure geometry."""
    import biotite.structure as struc
    import biotite.structure.io.pdbx as pdbx

    arr = pdbx.get_structure(pdbx.CIFFile.read(cif_path), model=1)
    arr = arr[np.isin(arr.element, ["C", "N", "O", "S"])]  # heavy atoms only

    ab = np.isin(arr.chain_id, AB_CHAINS)
    vh = arr.chain_id == "B"
    her2 = np.isin(arr.chain_id, HER2_CHAINS)

    def tot_sasa(mask):
        s = struc.sasa(arr[mask], probe_radius=1.4, point_number=SASA_POINTS)
        return float(np.nansum(s))

    s_cplx_fv = tot_sasa(ab | her2)
    bsa_fv = tot_sasa(ab) + tot_sasa(her2) - s_cplx_fv
    bsa_vh = tot_sasa(vh) + tot_sasa(her2) - tot_sasa(vh | her2)

    # residue-residue contacts across the Fv/HER2 interface
    a_at, t_at = arr[ab], arr[her2]
    cl = struc.CellList(t_at, cell_size=CUTOFF)
    pairs = set()
    ab_res, t_res = set(), set()
    for i in range(a_at.array_length()):
        idx = cl.get_atoms(a_at.coord[i], radius=CUTOFF)
        idx = idx[idx >= 0]
        if idx.size == 0:
            continue
        d = np.linalg.norm(t_at.coord[idx] - a_at.coord[i], axis=1)
        idx = idx[d <= CUTOFF]
        if idx.size == 0:
            continue
        ak = (str(a_at.chain_id[i]), int(a_at.res_id[i]))
        ab_res.add(ak)
        for j in idx:
            tk = (str(t_at.chain_id[j]), int(t_at.res_id[j]))
            t_res.add(tk)
            pairs.add((ak, tk))

    n_pairs = len(pairs)
    cdr = sum(1 for (ak, _) in pairs if ak[0] == "B" and ak[1] in CDRH3_RES)

    # CDRH3 backbone RMSD to 1N8Z after VH-framework CA superposition
    ref = _load_ref()
    b = arr[vh]
    fw_mask = (~np.isin(b.res_id, CDRH3_RES)) & (b.atom_name == "CA")
    mob_fw, ref_fw = [], []
    for r, c in zip(b.res_id[fw_mask], b.coord[fw_mask]):
        if int(r) in ref["fw"]:
            mob_fw.append(c)
            ref_fw.append(ref["fw"][int(r)])
    rmsd = float("nan")
    n_fw = len(mob_fw)
    if n_fw >= 3:
        rot, tr = _kabsch(np.asarray(mob_fw), np.asarray(ref_fw))
        loop = np.isin(b.res_id, CDRH3_RES) & np.isin(b.atom_name, ["N", "CA", "C", "O"])
        dd, n = 0.0, 0
        for r, a, c in zip(b.res_id[loop], b.atom_name[loop], b.coord[loop]):
            k = (int(r), str(a))
            if k in ref["bb"]:
                dd += float(np.sum((rot @ c + tr - ref["bb"][k]) ** 2))
                n += 1
        if n:
            rmsd = float(np.sqrt(dd / n))

    return {
        "bsa_fv_her2": bsa_fv,
        "bsa_vh_her2": bsa_vh,
        "n_iface_res_45": len(ab_res) + len(t_res),
        "n_iface_res_ab": len(ab_res),
        "n_iface_res_her2": len(t_res),
        "n_contact_pairs": n_pairs,
        "cdrh3_share": (cdr / n_pairs) if n_pairs else float("nan"),
        "n_fw_ca_superposed": n_fw,
        "cdrh3_rmsd_1n8z": rmsd,
    }


def crosscheck_contacts(cif_path: str) -> dict:
    """Recount the 4.5 A interface with scripts/contacts.py's own reader and grid.

    contacts.py has no SASA, which is why biotite does the Shrake-Rupley part, but
    its contact definition is the project's definition, so the biotite cell-list
    counts above are validated against it rather than merely asserted.
    """
    import math
    import contacts as C

    atoms = [a for a in C.read_atoms(cif_path) if a[3] != "H"]
    ab = [a for a in atoms if a[0] in AB_CHAINS]
    tg = [a for a in atoms if a[0] in HER2_CHAINS]
    grid = defaultdict(list)
    for a in tg:
        grid[(int(a[4] // CUTOFF), int(a[5] // CUTOFF), int(a[6] // CUTOFF))].append(a)
    pairs, ab_res, t_res = set(), set(), set()
    for a in ab:
        kx, ky, kz = int(a[4] // CUTOFF), int(a[5] // CUTOFF), int(a[6] // CUTOFF)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for b in grid.get((kx + dx, ky + dy, kz + dz), ()):
                        if math.dist(a[4:7], b[4:7]) <= CUTOFF:
                            ak, tk = (a[0], a[1]), (b[0], b[1])
                            ab_res.add(ak)
                            t_res.add(tk)
                            pairs.add((ak, tk))
    cdr = sum(1 for (ak, _) in pairs if ak[0] == "B" and ak[1] in CDRH3_RES)
    return {"n_iface_res_45": len(ab_res) + len(t_res),
            "n_contact_pairs": len(pairs),
            "cdrh3_share": (cdr / len(pairs)) if pairs else float("nan")}


def _geom_job(path):
    try:
        return path, geometry(path)
    except Exception as exc:                       # noqa: BLE001
        return path, {"geom_error": f"{type(exc).__name__}: {exc}"}


# --------------------------------------------------------------------------
# statistics
# --------------------------------------------------------------------------
def icc1(groups: list[list[float]]):
    """One-way random-effects ANOVA: between/within SD and ICC(1)."""
    groups = [np.asarray(g, float) for g in groups if len(g) >= 2]
    k = len(groups)
    if k < 2:
        return {"k_sequences": k, "n_per_sequence": float("nan"),
                "ms_between": float("nan"), "ms_within": float("nan"),
                "sd_between": float("nan"), "sd_within": float("nan"),
                "icc1": float("nan"), "grand_mean": float("nan")}
    ns = np.array([len(g) for g in groups])
    n = float(ns.mean())
    allx = np.concatenate(groups)
    grand = allx.mean()
    ms_b = sum(len(g) * (g.mean() - grand) ** 2 for g in groups) / (k - 1)
    ms_w = sum(((g - g.mean()) ** 2).sum() for g in groups) / (len(allx) - k)
    var_b = max(0.0, (ms_b - ms_w) / n)
    icc = (ms_b - ms_w) / (ms_b + (n - 1) * ms_w) if (ms_b + (n - 1) * ms_w) else float("nan")
    return {"k_sequences": k, "n_per_sequence": n, "ms_between": ms_b, "ms_within": ms_w,
            "sd_between": float(np.sqrt(var_b)), "sd_within": float(np.sqrt(ms_w)),
            "icc1": float(icc), "grand_mean": float(grand)}


def bh(pvals: np.ndarray) -> np.ndarray:
    p = np.asarray(pvals, float)
    m = len(p)
    o = np.argsort(p)
    q = np.empty(m)
    prev = 1.0
    for rank, i in enumerate(o[::-1]):
        k = m - rank
        prev = min(prev, p[i] * m / k)
        q[i] = prev
    return q


def spearman_boot(x, y, rng):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    n = len(x)
    if n < 4:
        return float("nan"), float("nan"), float("nan"), float("nan"), n
    rho, p = stats.spearmanr(x, y)
    boots = np.empty(N_BOOT)
    for b in range(N_BOOT):
        idx = rng.integers(0, n, n)
        if len(np.unique(x[idx])) < 3 or len(np.unique(y[idx])) < 3:
            boots[b] = np.nan
            continue
        boots[b] = stats.spearmanr(x[idx], y[idx]).statistic
    lo, hi = np.nanpercentile(boots, [2.5, 97.5])
    return float(rho), float(p), float(lo), float(hi), n


def auc(pos, neg):
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    pos, neg = pos[np.isfinite(pos)], neg[np.isfinite(neg)]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan"), 0, 0
    allv = np.concatenate([pos, neg])
    r = stats.rankdata(allv)
    u = r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2.0
    return float(u / (len(pos) * len(neg))), len(pos), len(neg)


def fmt(v, nd=4):
    if v is None or v == "":
        return ""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    return "" if not np.isfinite(f) else f"{f:.{nd}f}"


# --------------------------------------------------------------------------
def noninferiority_supported(lower_bound, margin=NONINF_MARGIN):
    """A lower confidence bound must clear the model-score margin.

    This is a statement about a computational score, never clinical binding
    noninferiority or thermal stability. An upper bound clearing the margin
    only means that noninferiority has not been ruled out.
    """
    return bool(np.isfinite(lower_bound) and lower_bound >= margin)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-geom", action="store_true")
    ap.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 4))
    args = ap.parse_args()

    report: list[str] = []

    def say(s=""):
        print(s)
        report.append(s)

    # ---------------- collect -------------------------------------------
    cand_man = list(csv.DictReader(open(os.path.join(RUN, "manifest_candidates.csv"))))
    calib_man = list(csv.DictReader(open(os.path.join(RUN, "manifest_calibration.csv"))))
    cand_qids = {r["query_id"] for r in cand_man}
    calib_qids = {r["query_id"] for r in calib_man}

    recs = []
    recs += scan_tree(os.path.join(REL009, "boltz2-cand-s1to5"), "009/cand-s1to5")
    recs += scan_tree(os.path.join(REL009, "boltz2-cand-s42"), "009/cand-s42")
    recs += scan_tree(os.path.join(REL009, "boltz2-timing"), "009/timing-batch-of-1")
    recs += scan_tree(os.path.join(REL009, "boltz2-calib"), "009/calib")
    recs += [r for r in scan_tree(RUN006, "006/reused-seed42")
             if r["query_id"] in cand_qids and r["seed"] == 42]

    # determinism: same (query, seed) seen in more than one tree
    dup = defaultdict(list)
    for r in recs:
        dup[(r["query_id"], r["seed"])].append(r)
    det_rows = []
    for key, rs in sorted(dup.items()):
        if len(rs) < 2:
            continue
        base = rs[0]
        for other in rs[1:]:
            same_scores = all(abs(base[k] - other[k]) == 0.0 for k in
                              ("iface_min", "iface_mean", "iptm", "plddt", "ptm",
                               "pde", "binder_ptm", "ranking"))
            cif_same = ""
            if base["cif_path"] and other["cif_path"]:
                cif_same = "identical" if sha(base["cif_path"]) == sha(other["cif_path"]) \
                    else "DIFFERS"
            det_rows.append({"query_id": key[0], "seed": key[1],
                             "a": base["provenance"], "b": other["provenance"],
                             "scores": "identical" if same_scores else "DIFFER",
                             "cif_sha256_16": cif_same,
                             "d_iface_min": other["iface_min"] - base["iface_min"]})

    # keep one record per (query, seed): prefer the 009 fold, then run 006
    prio = {"009/cand-s1to5": 0, "009/cand-s42": 1, "009/calib": 0,
            "006/reused-seed42": 2, "009/timing-batch-of-1": 3}
    keep = {}
    for r in recs:
        k = (r["query_id"], r["seed"])
        if k not in keep or prio[r["provenance"]] < prio[keep[k]["provenance"]]:
            keep[k] = r
    recs = sorted(keep.values(), key=lambda r: (r["query_id"], r["seed"]))
    say(f"collected {len(recs)} (sequence, seed) score records "
        f"from {len(set(r['provenance'] for r in recs))} output trees")

    # ---------------- geometry -------------------------------------------
    cache = {}
    if os.path.exists(GEOM_CACHE):
        cache = json.load(open(GEOM_CACHE))
    if not args.no_geom:
        todo = [r["cif_path"] for r in recs if r["cif_path"] and r["cif_path"] not in cache]
        say(f"geometry: {len(todo)} structures to process ({len(cache)} cached), "
            f"{args.workers} workers")
        if todo:
            _load_ref()
            with ProcessPoolExecutor(max_workers=args.workers) as ex:
                done = 0
                for path, g in ex.map(_geom_job, todo, chunksize=4):
                    cache[path] = g
                    done += 1
                    if done % 50 == 0:
                        print(f"  {done}/{len(todo)}", flush=True)
            json.dump(cache, open(GEOM_CACHE, "w"))
    for r in recs:
        r.update(cache.get(r["cif_path"], {}))
    nerr = sum(1 for r in recs if "geom_error" in r)
    if nerr:
        say(f"WARNING: geometry failed for {nerr} structures")

    # ---------------- cross-check the contact definition -----------------
    xcheck = []
    if not args.no_geom:
        probe = [r for r in recs if r["cif_path"] and "bsa_fv_her2" in r][:3]
        for r in probe:
            try:
                cc = crosscheck_contacts(r["cif_path"])
            except Exception as exc:                        # noqa: BLE001
                xcheck.append({"query_id": r["query_id"], "seed": r["seed"],
                               "note": f"{type(exc).__name__}: {exc}"})
                continue
            xcheck.append({
                "query_id": r["query_id"], "seed": r["seed"],
                "note": "agrees" if all(
                    (cc[k] == r[k]) if isinstance(cc[k], int)
                    else abs(cc[k] - r[k]) < 1e-9 for k in cc) else "DISAGREES",
                **{f"contacts_py_{k}": cc[k] for k in cc},
                **{f"biotite_{k}": r[k] for k in cc}})

    # ---------------- metrics csv ----------------------------------------
    cdr_of_cand = {r["query_id"]: r["cdrh3"] for r in cand_man}
    cdr_of_calib = {r["query_id"]: r["cdrh3"] for r in calib_man}
    for r in recs:
        r["set"] = "candidate" if r["query_id"] in cand_qids else (
            "calibration" if r["query_id"] in calib_qids else "other")
        r["cdrh3"] = cdr_of_cand.get(r["query_id"], cdr_of_calib.get(r["query_id"], ""))

    mcols = ["set", "query_id", "cdrh3", "seed", "provenance", "iface_min", "iface_mean",
             "iptm", "plddt", "ptm", "pde", "binder_ptm", "ranking", "bsa_fv_her2",
             "bsa_vh_her2", "n_iface_res_45", "n_iface_res_ab", "n_iface_res_her2",
             "n_contact_pairs", "cdrh3_share", "cdrh3_rmsd_1n8z", "n_fw_ca_superposed",
             "geom_error", "scores_path"]
    with open(os.path.join(RUN, "multiseed_metrics.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=mcols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(recs, key=lambda r: (r["set"], r["query_id"], r["seed"])):
            w.writerow({k: (fmt(r.get(k), 6) if isinstance(r.get(k), float)
                            else r.get(k, "")) for k in mcols})
    say(f"wrote multiseed_metrics.csv ({len(recs)} rows)")

    # ---------------- per-sequence summary -------------------------------
    cand = [r for r in recs if r["set"] == "candidate" and r["seed"] in CAND_SEEDS]
    by_q = defaultdict(dict)
    for r in cand:
        by_q[r["query_id"]][r["seed"]] = r
    wt = by_q.get(WT_QID, {})
    missing = {q: sorted(set(CAND_SEEDS) - set(s)) for q, s in by_q.items()
               if set(CAND_SEEDS) - set(s)}
    say(f"candidate sequences: {len(by_q)}; seeds per sequence "
        f"{sorted(set(len(s) for s in by_q.values()))}; incomplete: {len(missing)}")

    summ = []
    for r in cand_man:
        q = r["query_id"]
        seeds = by_q.get(q, {})
        row = {"query_id": q, "cdrh3": r["cdrh3"], "rep_run": r["rep_run"],
               "candidate_ids": r["candidate_ids"], "n_rows_in_first_pass": r["n_rows"],
               "n_seeds": len(seeds), "seeds": ";".join(str(s) for s in sorted(seeds))}
        for m in SEED_METRICS:
            v = np.array([seeds[s].get(m, np.nan) for s in sorted(seeds)], float)
            v = v[np.isfinite(v)]
            if len(v):
                row[f"{m}_mean"] = v.mean()
                row[f"{m}_sd"] = v.std(ddof=1) if len(v) > 1 else 0.0
                row[f"{m}_min"] = v.min()
                row[f"{m}_max"] = v.max()
            else:
                for suf in ("mean", "sd", "min", "max"):
                    row[f"{m}_{suf}"] = float("nan")
        # WT-paired delta on iface_min, per seed
        d = []
        for s in sorted(seeds):
            if s in wt:
                d.append(seeds[s]["iface_min"] - wt[s]["iface_min"])
        d = np.array(d, float)
        row["n_paired_seeds"] = len(d)
        if len(d) > 1:
            n = len(d)
            mean, sd = d.mean(), d.std(ddof=1)
            se = sd / np.sqrt(n)
            tcrit = stats.t.ppf(0.95, n - 1)
            row["delta_iface_min_mean"] = mean
            row["delta_iface_min_sd"] = sd
            row["delta_iface_min_se"] = se
            row["delta_lo95_onesided"] = mean - tcrit * se
            row["delta_hi95_onesided"] = mean + tcrit * se
            if se > 0:
                tstat = mean / se
                row["delta_t"] = tstat
                row["delta_p_onesided"] = float(stats.t.sf(tstat, n - 1))
            else:
                row["delta_t"] = float("nan")
                row["delta_p_onesided"] = 0.0 if mean > 0 else 1.0
        summ.append(row)

    # BH over the non-WT unique sequences (one test per CDRH3)
    tests = [r for r in summ if r["cdrh3"] != WT_CDRH3 and np.isfinite(
        r.get("delta_p_onesided", np.nan))]
    qs = bh(np.array([r["delta_p_onesided"] for r in tests]))
    for r, qv in zip(tests, qs):
        r["delta_q_bh_unique"] = float(qv)
    # literal "BH across the 66": the same tests expanded to the first-pass rows
    exp_p, exp_ref = [], []
    for r in tests:
        for _ in range(int(r["n_rows_in_first_pass"])):
            exp_p.append(r["delta_p_onesided"])
            exp_ref.append(r)
    qe = bh(np.array(exp_p))
    best = {}
    for r, qv in zip(exp_ref, qe):
        best[r["query_id"]] = min(best.get(r["query_id"], 1.0), float(qv))
    for r in tests:
        r["delta_q_bh_rows"] = best[r["query_id"]]

    # ---------------- labels ---------------------------------------------
    fp = list(csv.DictReader(open(FIRSTPASS)))
    fp_by_cdr = defaultdict(list)
    for r in fp:
        fp_by_cdr[r["cdrh3"]].append(r)

    def gates_ok(cdr: str) -> bool:
        rs = [r for r in fp_by_cdr.get(cdr, []) if r["has_structure"] == "TRUE"]
        if not rs:
            return False
        r = rs[0]
        try:
            ph = float(r["p_high"])
        except ValueError:
            return False
        return (r["novelty_margin"] == "TRUE" and r["has_cys"] == "FALSE"
                and r["liabilities_removed"] == "2" and r["grip_4of4"] == "TRUE"
                and ph >= 0.95)

    for r in summ:
        r["other_gates_pass"] = gates_ok(r["cdrh3"])
        lo = r.get("delta_lo95_onesided", float("nan"))
        hi = r.get("delta_hi95_onesided", float("nan"))
        qv = r.get("delta_q_bh_unique", float("nan"))
        lab = "NA_WT" if r["cdrh3"] == WT_CDRH3 else "INDETERMINATE"
        if r["cdrh3"] != WT_CDRH3 and np.isfinite(lo):
            if r["other_gates_pass"] and lo >= 0 and qv <= BH_ALPHA:
                lab = "PASS_ROBUST"
            elif r["other_gates_pass"] and noninferiority_supported(lo):
                lab = "NONINFERIOR"
            elif hi < 0:
                lab = "FAIL_ROBUST"
        r["label_v2"] = lab
        r["noninf_and_hi_below_zero"] = (lab == "NONINFERIOR" and np.isfinite(hi) and hi < 0)

    old_group_of = {}
    for r in summ:
        rs = [x for x in fp_by_cdr.get(r["cdrh3"], []) if x["has_structure"] == "TRUE"]
        old_group_of[r["query_id"]] = sorted({x["group"] for x in rs})

    scols = (["query_id", "cdrh3", "rep_run", "candidate_ids", "n_rows_in_first_pass",
              "n_seeds", "seeds"]
             + [f"{m}_{s}" for m in SEED_METRICS for s in ("mean", "sd", "min", "max")]
             + ["n_paired_seeds", "delta_iface_min_mean", "delta_iface_min_sd",
                "delta_iface_min_se", "delta_lo95_onesided", "delta_hi95_onesided",
                "delta_t", "delta_p_onesided", "delta_q_bh_unique", "delta_q_bh_rows",
                "other_gates_pass", "label_v2", "noninf_and_hi_below_zero"])
    with open(os.path.join(RUN, "multiseed_summary.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=scols, extrasaction="ignore")
        w.writeheader()
        def dkey(r):
            v = r.get("delta_iface_min_mean")
            return -v if isinstance(v, float) and np.isfinite(v) else 9.0

        for r in sorted(summ, key=dkey):
            w.writerow({k: (fmt(r.get(k), 6) if isinstance(r.get(k), float) else r.get(k, ""))
                        for k in scols})
    say(f"wrote multiseed_summary.csv ({len(summ)} sequences)")

    # ---------------- variance components --------------------------------
    say()
    say("## Variance components across seeds (one-way random effects, "
        f"{len(by_q)} sequences x {len(CAND_SEEDS)} seeds)")
    say()
    say("| metric | SD between sequences | SD within sequence (seed) | ICC(1) | "
        "MS_between | MS_within |")
    say("| --- | --- | --- | --- | --- | --- |")
    vc = {}
    for m in ["iface_min", "bsa_fv_her2", "iface_mean", "iptm"]:
        groups = []
        for q, seeds in by_q.items():
            g = [seeds[s].get(m, np.nan) for s in sorted(seeds)]
            g = [x for x in g if isinstance(x, (int, float)) and np.isfinite(x)]
            if len(g) >= 2:
                groups.append(g)
        vc[m] = icc1(groups)
        v = vc[m]
        say(f"| {m} | {v['sd_between']:.5g} | {v['sd_within']:.5g} | {v['icc1']:.4f} | "
            f"{v['ms_between']:.4g} | {v['ms_within']:.4g} |")

    # ---------------- rank stability -------------------------------------
    say()
    say("## Rank stability of iface_min across seeds")
    say()
    ids = [q for q in sorted(by_q) if len(by_q[q]) == len(CAND_SEEDS)]
    mat = np.array([[by_q[q][s]["iface_min"] for q in ids] for s in CAND_SEEDS])
    means = mat.mean(0)
    rhos = [stats.spearmanr(mat[i], means).statistic for i in range(len(CAND_SEEDS))]
    pair = [stats.spearmanr(mat[i], mat[j]).statistic
            for i in range(len(CAND_SEEDS)) for j in range(i + 1, len(CAND_SEEDS))]
    say(f"- {len(ids)} sequences with all {len(CAND_SEEDS)} seeds")
    say(f"- Spearman rho, single-seed ranking vs the {len(CAND_SEEDS)}-seed mean "
        f"ranking: median {np.median(rhos):.3f} (range {min(rhos):.3f}..{max(rhos):.3f})")
    say(f"- Spearman rho between two different single seeds: median "
        f"{np.median(pair):.3f} (range {min(pair):.3f}..{max(pair):.3f})")
    k = 8
    topmean = set(np.array(ids)[np.argsort(-means)[:k]])
    overlap = [len(topmean & set(np.array(ids)[np.argsort(-mat[i])[:k]]))
               for i in range(len(CAND_SEEDS))]
    say(f"- top-{k} overlap, single seed vs {len(CAND_SEEDS)}-seed mean: "
        f"{overlap} of {k}")
    old_strict = {r["query_id"] for r in summ
                  if "PASS_STRICT" in old_group_of.get(r["query_id"], [])}
    say(f"- of the {len(old_strict)} first-pass PASS_STRICT sequences, "
        f"{len(old_strict & topmean)} are in the top-{k} by {len(CAND_SEEDS)}-seed "
        f"mean iface_min")

    # ---------------- noise floor / MDD ----------------------------------
    sds = np.array([r["delta_iface_min_sd"] for r in summ
                    if np.isfinite(r.get("delta_iface_min_sd", np.nan))
                    and r["cdrh3"] != WT_CDRH3], float)
    npair = [r["n_paired_seeds"] for r in summ if r["n_paired_seeds"] > 1]
    n_eff = int(np.median(npair)) if npair else len(CAND_SEEDS)
    if len(sds) == 0:
        sds = np.array([float("nan")])
    pooled = float(np.sqrt(np.mean(sds ** 2)))
    df = n_eff - 1
    tcrit = stats.t.ppf(0.95, df)
    tpow = stats.t.ppf(0.80, df)
    mdd = (tcrit + tpow) * pooled / np.sqrt(n_eff)
    mdd_med = (tcrit + tpow) * float(np.median(sds)) / np.sqrt(n_eff)

    def mdd_exact(sd, n, power=0.80, alpha=0.05):
        """Exact one-sided paired-t MDD from the noncentral t distribution."""
        if not np.isfinite(sd) or sd <= 0:
            return float("nan")
        tc = stats.t.ppf(1 - alpha, n - 1)

        def f(d):
            return stats.nct.sf(tc, n - 1, d * np.sqrt(n) / sd) - power
        try:
            from scipy.optimize import brentq
            return float(brentq(f, 1e-9, 100 * sd))
        except Exception:                               # noqa: BLE001
            return float("nan")

    mdd_nct = mdd_exact(pooled, n_eff)
    mdd_nct_med = mdd_exact(float(np.median(sds)), n_eff)
    say()
    say("## Noise floor of the WT-paired delta on iface_min")
    say()
    say(f"- seeds per sequence: **{n_eff}** ({CAND_SEEDS})")
    say(f"- SD of the paired delta, pooled over {len(sds)} sequences: "
        f"**{pooled:.5f}**  (median {np.median(sds):.5f}, "
        f"min {sds.min():.5f}, max {sds.max():.5f})")
    say(f"- within-sequence seed SD of raw iface_min: **{vc['iface_min']['sd_within']:.5f}**; "
        f"between-sequence SD {vc['iface_min']['sd_between']:.5f}")
    say(f"- minimal detectable delta vs WT, one-sided alpha=0.05, 80% power, n={n_eff}:")
    say(f"    - exact (noncentral t): **{mdd_nct:.5f}** with the pooled SD, "
        f"{mdd_nct_med:.5f} with the median SD")
    say(f"    - normal/t approximation (t_0.95+t_0.80)*SD/sqrt(n): {mdd:.5f} pooled, "
        f"{mdd_med:.5f} median")
    say(f"- i.e. with {n_eff} seeds nothing smaller than about "
        f"**{mdd_nct:.3f} iface_min** can be called a real improvement.")

    say()
    say("## The in-batch wild type across seeds")
    say()
    say("| seed | iface_min | iface_mean | iptm | BSA Fv-HER2 (A^2) | "
        "CDRH3 RMSD to 1N8Z (A) |")
    say("| --- | --- | --- | --- | --- | --- |")
    for s in sorted(wt):
        r = wt[s]
        say(f"| {s} | {r['iface_min']:.4f} | {r['iface_mean']:.4f} | {r['iptm']:.3f} | "
            f"{fmt(r.get('bsa_fv_her2'), 1)} | {fmt(r.get('cdrh3_rmsd_1n8z'), 3)} |")
    wv = np.array([wt[s]["iface_min"] for s in sorted(wt)], float)
    if len(wv) > 1:
        say(f"| **SD / range** | {wv.std(ddof=1):.4f} / {wv.max()-wv.min():.4f} | | | | |")

    say()
    say("## Ten largest mean WT-paired deltas on iface_min")
    say()
    say("| fold query id | first-pass rows | other gates | mean delta | SD | "
        "lo95 (one-sided) | hi95 | p (one-sided) | q (BH) | v2 label |")
    say("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    top = sorted((r for r in summ if r["cdrh3"] != WT_CDRH3
                  and np.isfinite(r.get("delta_iface_min_mean", np.nan))),
                 key=lambda r: -r["delta_iface_min_mean"])[:10]
    for r in top:
        say(f"| {r['query_id']} | {r['n_rows_in_first_pass']} | "
            f"{'pass' if r['other_gates_pass'] else 'fail'} | "
            f"{r['delta_iface_min_mean']:+.4f} | {r['delta_iface_min_sd']:.4f} | "
            f"{r['delta_lo95_onesided']:+.4f} | {r['delta_hi95_onesided']:+.4f} | "
            f"{r['delta_p_onesided']:.3f} | {r.get('delta_q_bh_unique', float('nan')):.3f} "
            f"| {r['label_v2']} |")

    # ---------------- label groups + cross-tab ---------------------------
    old_of = old_group_of

    say()
    say("## Pre-registered v2 labels")
    say()
    from collections import Counter
    cnt = Counter(r["label_v2"] for r in summ)
    say("| label | unique CDRH3 | first-pass rows |")
    say("| --- | --- | --- |")
    rowcnt = Counter()
    for r in summ:
        rowcnt[r["label_v2"]] += int(r["n_rows_in_first_pass"])
    for lab in ["PASS_ROBUST", "NONINFERIOR", "FAIL_ROBUST", "INDETERMINATE", "NA_WT"]:
        if cnt.get(lab):
            say(f"| {lab} | {cnt[lab]} | {rowcnt[lab]} |")
    say(f"| **total** | {len(summ)} | {sum(rowcnt.values())} |")
    amb = sum(1 for r in summ if r["noninf_and_hi_below_zero"])
    say()
    say(f"Labels are assigned in the order they were pre-registered "
        f"(PASS_ROBUST, then NONINFERIOR, then FAIL_ROBUST). "
        f"{amb} sequences satisfy NONINFERIOR and also have an upper bound below 0, "
        f"so they would have been FAIL_ROBUST under the opposite precedence.")

    say()
    say("## Cross-tab, v2 label x first-pass group (unique CDRH3)")
    say()
    olabs = sorted({";".join(v) for v in old_of.values()})
    vlabs = [l for l in ["PASS_ROBUST", "NONINFERIOR", "FAIL_ROBUST",
                         "INDETERMINATE", "NA_WT"] if cnt.get(l)]
    say("| first-pass group | " + " | ".join(vlabs) + " | total |")
    say("| --- | " + " | ".join(["---"] * len(vlabs)) + " | --- |")
    for ol in olabs:
        cells = [sum(1 for r in summ if ";".join(old_of[r["query_id"]]) == ol
                     and r["label_v2"] == vl) for vl in vlabs]
        say(f"| {ol} | " + " | ".join(str(c) for c in cells) + f" | {sum(cells)} |")
    tot = [sum(1 for r in summ if r["label_v2"] == vl) for vl in vlabs]
    say("| **total** | " + " | ".join(str(c) for c in tot) + f" | {sum(tot)} |")

    # ---------------- first_pass_candidates_v2 ---------------------------
    new_cols = ["v2_n_seeds"] + [f"v2_{m}_{s}" for m in CORE4
                                 for s in ("mean", "sd", "min", "max")] + [
        "v2_bsa_vh_her2_mean", "v2_n_iface_res_45_mean", "v2_cdrh3_share_mean",
        "v2_cdrh3_rmsd_1n8z_mean", "v2_delta_iface_min_mean", "v2_delta_iface_min_sd",
        "v2_delta_iface_min_se", "v2_delta_lo95_onesided", "v2_delta_hi95_onesided",
        "v2_delta_p_onesided", "v2_delta_q_bh_unique", "v2_delta_q_bh_rows",
        "v2_other_gates_pass", "v2_label", "v2_fold_query_id"]
    s_by_cdr = {r["cdrh3"]: r for r in summ}
    with open(os.path.join(RUN, "first_pass_candidates_v2.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fp[0].keys()) + new_cols)
        w.writeheader()
        for r in fp:
            out = dict(r)
            s = s_by_cdr.get(r["cdrh3"]) if r["has_structure"] == "TRUE" else None
            for c in new_cols:
                out[c] = ""
            if s:
                out["v2_n_seeds"] = s["n_seeds"]
                out["v2_fold_query_id"] = s["query_id"]
                for m in CORE4:
                    for suf in ("mean", "sd", "min", "max"):
                        out[f"v2_{m}_{suf}"] = fmt(s.get(f"{m}_{suf}"), 6)
                for m in ["bsa_vh_her2", "n_iface_res_45", "cdrh3_share",
                          "cdrh3_rmsd_1n8z"]:
                    out[f"v2_{m}_mean"] = fmt(s.get(f"{m}_mean"), 6)
                for k in ["delta_iface_min_mean", "delta_iface_min_sd",
                          "delta_iface_min_se", "delta_lo95_onesided",
                          "delta_hi95_onesided", "delta_p_onesided",
                          "delta_q_bh_unique", "delta_q_bh_rows"]:
                    out[f"v2_{k}"] = fmt(s.get(k), 6)
                out["v2_other_gates_pass"] = s["other_gates_pass"]
                out["v2_label"] = s["label_v2"]
            w.writerow(out)
    say()
    say(f"wrote first_pass_candidates_v2.csv ({len(fp)} rows, "
        f"{len(fp[0])} + {len(new_cols)} columns)")

    # ---------------- calibration ----------------------------------------
    calib = [r for r in recs if r["set"] == "calibration" and r["seed"] in CALIB_SEEDS]
    cb_q = defaultdict(dict)
    for r in calib:
        cb_q[r["query_id"]][r["seed"]] = r
    crows = []
    for r in calib_man:
        q = r["query_id"]
        seeds = cb_q.get(q, {})
        row = {"query_id": q, "cdrh3": r["cdrh3"], "stratum": r["stratum"],
               "binder_label": r["binder_label"], "kd_nM": r["kd_nM"],
               "wt_kd_nM": r["wt_kd_nM"], "binding_result": r["binding_result"],
               "n_seeds": len(seeds), "seeds": ";".join(str(s) for s in sorted(seeds))}
        row["log10_kd"] = (np.log10(float(r["kd_nM"])) if r["kd_nM"] else float("nan"))
        for m in SEED_METRICS:
            v = np.array([seeds[s].get(m, np.nan) for s in sorted(seeds)], float)
            v = v[np.isfinite(v)]
            row[f"{m}_mean"] = v.mean() if len(v) else float("nan")
            row[f"{m}_sd"] = v.std(ddof=1) if len(v) > 1 else float("nan")
        crows.append(row)
    ccols = (["query_id", "cdrh3", "stratum", "binder_label", "kd_nM", "log10_kd",
              "wt_kd_nM", "binding_result", "n_seeds", "seeds"]
             + [f"{m}_{s}" for m in SEED_METRICS for s in ("mean", "sd")])
    with open(os.path.join(RUN, "calibration.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=ccols, extrasaction="ignore")
        w.writeheader()
        for r in crows:
            w.writerow({k: (fmt(r.get(k), 6) if isinstance(r.get(k), float)
                            else r.get(k, "")) for k in ccols})
    say(f"wrote calibration.csv ({len(crows)} sequences)")

    rng = np.random.default_rng(RNG_SEED)
    kd_rows = [r for r in crows if np.isfinite(r["log10_kd"])]
    pos = [r for r in crows if r["binder_label"] == "binder"]
    neg = [r for r in crows if r["binder_label"] == "non_binder"]
    say()
    say("## Calibration against MEASURED affinity")
    say()
    say(f"Spearman rho vs measured log10 KD over the {len(kd_rows)} calibration "
        f"sequences with a quantified KD; AUC over {len(pos)} binders "
        f"(KD <= 2x WT KD, or best available) vs {len(neg)} non-binders "
        f"(KD >= 100 nM or no_reportable_kd). Bootstrap: {N_BOOT} resamples, "
        f"rng seed {RNG_SEED}. A metric where higher = better binding should give "
        f"rho < 0 (lower KD) and AUC > 0.5.")
    say()
    say("| metric | n(KD) | Spearman rho | 95% CI (bootstrap) | p | CI excludes 0 | "
        "AUC binder vs non-binder |")
    say("| --- | --- | --- | --- | --- | --- | --- |")
    calib_stats = {}
    for m in CALIB_METRICS + ["plddt", "n_iface_res_45", "cdrh3_share",
                              "cdrh3_rmsd_1n8z"]:
        x = [r[f"{m}_mean"] for r in kd_rows]
        y = [r["log10_kd"] for r in kd_rows]
        rho, p, lo, hi, n = spearman_boot(x, y, rng)
        a, np_, nn = auc([r[f"{m}_mean"] for r in pos], [r[f"{m}_mean"] for r in neg])
        excl = "yes" if np.isfinite(lo) and (lo > 0 or hi < 0) else "no"
        calib_stats[m] = dict(rho=rho, lo=lo, hi=hi, p=p, auc=a, n=n, excludes=excl)
        say(f"| {m} | {n} | {rho:+.3f} | [{lo:+.3f}, {hi:+.3f}] | {p:.3g} | {excl} | "
            f"{a:.3f} |")

    # ---------------- determinism ----------------------------------------
    say()
    say("## Determinism check")
    say()
    if det_rows:
        say("| query | seed | tree A | tree B | score fields | model.cif sha256(16) | "
            "d iface_min |")
        say("| --- | --- | --- | --- | --- | --- | --- |")
        for d in det_rows:
            say(f"| {d['query_id']} | {d['seed']} | {d['a']} | {d['b']} | {d['scores']} "
                f"| {d['cif_sha256_16']} | {d['d_iface_min']:+.1e} |")
    else:
        say("no (query, seed) pair was folded twice")

    if xcheck:
        say()
        say("## Contact definition cross-check")
        say()
        say("The 4.5 A interface counts are produced by a biotite cell list; they are "
            "re-derived here with `scripts/contacts.py`'s own `read_atoms` and grid, "
            "which is the project's contact definition. SASA (and therefore BSA) has "
            "no equivalent in `contacts.py`, so Shrake-Rupley comes from biotite.")
        say()
        say("| query | seed | verdict | contacts.py res/pairs/CDRH3 share | "
            "biotite res/pairs/CDRH3 share |")
        say("| --- | --- | --- | --- | --- |")
        for x in xcheck:
            if "contacts_py_n_contact_pairs" not in x:
                say(f"| {x['query_id']} | {x['seed']} | {x['note']} | - | - |")
                continue
            say(f"| {x['query_id']} | {x['seed']} | {x['note']} | "
                f"{x['contacts_py_n_iface_res_45']}/"
                f"{x['contacts_py_n_contact_pairs']}/"
                f"{x['contacts_py_cdrh3_share']:.4f} | "
                f"{x['biotite_n_iface_res_45']}/{x['biotite_n_contact_pairs']}/"
                f"{x['biotite_cdrh3_share']:.4f} |")

    say()
    say("## Sequence-model reference, quoted not recomputed")
    say()
    say("No model was fitted, re-fitted or modified anywhere in this run; Boltz-2 was "
        "used only as an inference executable. For a sequence-side yardstick the "
        "project's existing numbers stand: `people/anas/facs_model_report.txt` reports "
        "the FACS `p_high` model at external-SPR AUC 0.764 (quantified vs no-fit) and "
        "Spearman -0.430 vs log10 KD on unseen sequences. Those are not recomputed "
        "here because the 30 calibration loops are drawn from the same SPR/FACS pool "
        "the model was fitted on, so any p_high computed for them would be "
        "leakage-contaminated.")

    import datetime
    head = [
        "# Multi-seed Boltz-2 noise floor and calibration of structural metrics",
        "",
        f"Run 009. Generated by `scripts/multiseed_analysis.py` on "
        f"{datetime.datetime.now().astimezone().isoformat(timespec='seconds')}  ",
        f"Interpreter: `{sys.executable}` (Python {sys.version.split()[0]})  ",
        "Container: `quay.io/apheris/oslo-hackathon:apheris-boltz-v1.3.0-boltz2`, "
        "`python -m apheris_boltz.cli predict`, flags identical to run 006 "
        "(`--num-diffusion-samples 1 --write-detailed-scores true "
        "--query-failures skip`, recycling 3, sampling 200), template = run 006's "
        "`prepared/holo/template.cif` (= run 004's, byte-identical).  ",
        f"Candidate seeds {CAND_SEEDS}; calibration seeds {sorted(CALIB_SEEDS)}.  ",
        "Geometry: biotite Shrake-Rupley SASA "
        f"({SASA_POINTS} points, probe 1.4 A) and a {CUTOFF} A heavy-atom cell list; "
        f"CDRH3 RMSD reference `{REF_CIF}`.",
        "",
        "Tables: `multiseed_metrics.csv` (sequence x seed), `multiseed_summary.csv` "
        "(per sequence), `first_pass_candidates_v2.csv` (step-2 table + v2 columns; "
        "step 2's own file is untouched), `calibration.csv`, `analysis_stats.json`.",
        "",
    ]
    with open(os.path.join(RUN, "multiseed_summary.md"), "w") as fh:
        fh.write("\n".join(head + report) + "\n")
    json.dump({"variance_components": vc,
               "noise_floor": {"n_seeds": n_eff, "sd_delta_pooled": pooled,
                               "sd_delta_median": float(np.median(sds)),
                               "mdd_80pct_power_nct": float(mdd_nct),
                               "mdd_80pct_power_approx": float(mdd)},
               "labels": dict(cnt), "calibration": calib_stats,
               "determinism": det_rows},
              open(os.path.join(RUN, "analysis_stats.json"), "w"), indent=2, default=str)
    say()
    say(f"wrote multiseed_summary.md and analysis_stats.json under {RUN}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
