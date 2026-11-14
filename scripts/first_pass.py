#!/usr/bin/env python3
"""Build the unified first-pass candidate table and summary for the HER2 binder work.

Every candidate the project has produced so far lives in a different file with a
different set of columns, and the pass/fail reason that rank.py computes is printed
and then thrown away. This script puts all of them in one table, one row per
candidate, with every gate evaluated by the *same* code, and writes the group labels
that were pre-registered by the planner before anyone looked at the results.

Interpreter
-----------
The team venv, which has numpy/pandas/scikit-learn/joblib:

    /home/hackathon/team14/.venv/bin/python  (Python 3.12.3)
    == `~/team14/scripts/py`

scikit-learn is required because the FACS p_high model is a pickled
HistGradientBoostingClassifier. The analysis venv in trastuzumab_epitope
(.venv_num) will NOT do: it has no scikit-learn.

Reused logic, not re-derived
----------------------------
  scripts/novelty.py      load(), min_distance(), identity_to_trastuzumab()
  scripts/report.py       CDRH3_FROM/TO, WILD_TYPE, CONTACT, LIABILITY, hypothesis()
  people/anas/rank.py     MIN_DIST, MAX_IDENTITY, p_high()  (the facs_model.joblib wrapper)
  people/anas/collect_refold.py  the interface-ipTM recipe is reimplemented in
                          iface_from_scores() below, 8 lines, because that module does
                          its work inside main() and writes into run directories. The
                          numbers are checked against people/anas/refold-006.csv.

Candidate sources
-----------------
  run 001  her2-baseline            scored-boltz2/refold_metrics.csv    2 rows  free-loop
  run 004  004-mohamed-her2-novel   scored-boltz2/refold_metrics.csv   10 rows  free-loop
  run 005  005-mohamed-anchored     scored-boltz2/refold_metrics.csv   10 rows  anchored
  run 006  006-anas-enumerated      manifest.csv + boltz2/*/seed_*     44 rows  enumerated (40) + control (4)
  legal    people/anas/legal-scored.csv                              5000 rows  legal-scored

Run 007 (007-mohamed-anchored-diverse-k1) is excluded: it was still on the GPU when
this ran and has no manifest, no refold_metrics.csv and no boltz2 output.

Pre-registered group labels  (DO NOT TUNE -- report the sensitivity grid instead)
--------------------------------------------------------------------------------
  PASS_STRICT  novelty_margin AND both liabilities removed AND grip_4of4
               AND p_high >= 0.95 AND iface_min >= WT iface_min
  PASS_SOFT    as PASS_STRICT but iface_min >= WT iface_min - 0.03
  PASS_SEQ     novelty_margin AND both liabilities removed AND grip_4of4
               AND p_high >= 0.95, for rows with no structure
  FAIL_<gate>  first gate that fails, in the order
               novelty_official, novelty_margin, cys, liability, grip, p_high, iface

Usage
-----
  py scripts/first_pass.py --out-dir runs/008-claude-first-pass
  py scripts/first_pass.py --out-dir /tmp/x --legal-limit 200   # fast smoke test

The script only ever writes inside --out-dir. It touches no run directory, no GPU
and no network.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict

import numpy as np

HOME = os.path.expanduser("~/team14")
sys.path.insert(0, os.path.join(HOME, "scripts"))
sys.path.insert(0, os.path.join(HOME, "people", "anas"))

import novelty  # noqa: E402
import rank  # noqa: E402  (brings MIN_DIST, MAX_IDENTITY, p_high)
import report  # noqa: E402

DOCS_RUNS = os.path.join(HOME, "data/rfd4-proteina/docs/runs")
EPITOPE = os.path.expanduser("~/trastuzumab_epitope")

# Chain order in every queries.json of every run: A VL(107), B VH(120), C(92), D(17).
# Verified identical for runs 001/004/005/006, so index 1 is the binder heavy chain
# and 2,3 are the two HER2 fragments -- the same convention collect_refold.py uses.
BINDER, TARGETS = 1, (2, 3)

# Pre-registered thresholds.
P_HIGH_GATE = 0.95
IFACE_SOFT_MARGIN = 0.03
GATE_ORDER = ["novelty_official", "novelty_margin", "cys", "liability", "grip", "p_high", "iface"]

# Sensitivity grid, also pre-registered.
GRID_P_HIGH = [0.90, 0.95, 0.99]
GRID_IFACE = [-0.05, -0.03, 0.0, +0.02]
GRID_DIST = [2, 3]

NAN = float("nan")

SOURCES = [
    # (run label, generator, kind, path bits)
    ("001", "free-loop", "metrics", "her2-baseline"),
    ("004", "free-loop", "metrics", "004-mohamed-her2-novel-n40"),
    ("005", "anchored", "metrics", "005-mohamed-anchored-n40"),
    ("006", "enumerated", "manifest", "006-anas-enumerated-top40"),
    ("legal-scored", "legal-scored", "legal", None),
]

# Each run's Boltz-2 structural template is built from one of that run's own generated
# designs (the mmCIF data block is named data_<some design>_template), so it is NOT a
# shared constant across runs. build_refold.py copies run 004's template verbatim, which
# is why runs 004 and 006 produce bit-identical scores for a shared sequence and why the
# other two runs do not. Filled in by load_templates().
TEMPLATE_SHA: dict[str, str] = {}


# --------------------------------------------------------------------------- helpers

def sha256(path: str, limit: int | None = None) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
            if limit and h.block_size and fh.tell() > limit:
                break
    return h.hexdigest()


def num(v) -> float:
    try:
        f = float(v)
        return f
    except (TypeError, ValueError):
        return NAN


def fin(v) -> bool:
    return isinstance(v, float) and v == v and not math.isinf(v)


def pairwise(mat, i, j) -> float:
    """Mean of both matrix directions; the chain-chain ipTM matrix is not symmetric."""
    return (mat[i][j] + mat[j][i]) / 2.0


def iface_from_scores(path: str) -> dict:
    """Binder-to-target interface numbers out of a Boltz-2 scores.json."""
    d = json.load(open(path))
    mat = d["chain_chain_interface_predicted_tm_score"]
    iface = [pairwise(mat, BINDER, t) for t in TARGETS]
    return {
        "iface_min": min(iface),
        "iface_mean": sum(iface) / len(iface),
        "iptm": d["interface_predicted_tm_score"],
        "ptm": d["predicted_tm_score"],
        "plddt": d["average_predicted_local_distance_difference_test"],
        "pde": d["global_predicted_distance_error"],
        "binder_ptm": d["chain_predicted_tm_score"][BINDER],
        "ranking": d["model_ranking_score"],
    }


def find_seed_dirs(run_dir: str, qid: str) -> list[str]:
    base = os.path.join(run_dir, "boltz2", qid)
    if not os.path.isdir(base):
        return []
    return sorted(os.path.join(base, d) for d in os.listdir(base) if d.startswith("seed_"))


def seed_scores(seed_dir: str) -> str | None:
    hits = sorted(f for f in os.listdir(seed_dir) if f.endswith("_scores.json"))
    return os.path.join(seed_dir, hits[0]) if hits else None


def seed_cif(seed_dir: str) -> str:
    hits = sorted(f for f in os.listdir(seed_dir) if f.endswith("_model.cif"))
    return os.path.join(seed_dir, hits[0]) if hits else ""


def load_templates() -> None:
    """Hash each run's Boltz-2 template so comparability across runs is visible."""
    for run, _gen, kind, slug in SOURCES:
        if kind == "legal":
            continue
        p = os.path.join(DOCS_RUNS, slug, "prepared", "holo", "template.cif")
        TEMPLATE_SHA[run] = sha256(p)[:16] if os.path.exists(p) else ""


def stats(vals: list[float]) -> dict:
    v = [x for x in vals if fin(x)]
    if not v:
        return dict(n=0, mean=NAN, sd=NAN, min=NAN, median=NAN, max=NAN)
    return dict(n=len(v), mean=statistics.fmean(v),
                sd=statistics.stdev(v) if len(v) > 1 else 0.0,
                min=min(v), median=statistics.median(v), max=max(v))


def fmt(x, nd=3) -> str:
    if not fin(x):
        return "-"
    return f"{x:.{nd}f}"


# ------------------------------------------------------------------- row collection

def collect_metrics_run(run, generator, slug, limit=None) -> list[dict]:
    """Runs 001/004/005: refold_metrics.csv carries the sequence and the RMSD-based
    columns; iface_* has to come from the Boltz-2 scores.json next door."""
    out_dir = os.path.join(DOCS_RUNS, slug)
    path = os.path.join(out_dir, "scored-boltz2", "refold_metrics.csv")
    rows = []
    for r in csv.DictReader(open(path, newline="", encoding="utf-8")):
        seq = (r.get("binder_sequence") or "").strip()
        if not seq:
            continue
        qid = r.get("query_id", "")
        rec = {
            "run": run, "generator": generator, "query_id": qid,
            "cdrh3": seq[report.CDRH3_FROM - 1:report.CDRH3_TO],
            "binder_sequence": seq,
            "min_ipae": num(r.get("min_ipae")),
            "binder_plddt": num(r.get("binder_plddt")),
            "backbone_rmsd": num(r.get("backbone_rmsd")),
            "boltz_seed": r.get("seed", ""),
            "source_tag": "refold_metrics",
            "stored_p_high": NAN,
        }
        seeds = find_seed_dirs(out_dir, qid)
        rec.update(attach_structure(seeds))
        # refold_metrics also carries iptm/ptm/plddt; keep the scores.json ones but
        # remember the csv values so the two can be cross-checked.
        rec["csv_iptm"] = num(r.get("iptm"))
        rec["csv_plddt"] = num(r.get("plddt"))
        rows.append(rec)
        if limit and len(rows) >= limit:
            break
    return rows


def collect_manifest_run(run, slug, limit=None) -> list[dict]:
    """Run 006: the manifest is the candidate list; all metrics come from scores.json.
    There is no refold_metrics.csv, so min_ipae and binder_plddt are unavailable (the
    PAE npz was not kept and the detailed_scores are cbor, with no cbor reader here)."""
    run_dir = os.path.join(HOME, "runs", slug)
    out_dir = os.path.join(DOCS_RUNS, slug)
    rows = []
    for r in csv.DictReader(open(os.path.join(run_dir, "manifest.csv"), newline="", encoding="utf-8")):
        qid = r["query_id"]
        gen = "control" if r.get("source") == "control" else "enumerated"
        rec = {
            "run": run, "generator": gen, "query_id": qid,
            "cdrh3": r["cdrh3"].strip().upper(), "binder_sequence": "",
            "min_ipae": NAN, "binder_plddt": NAN, "backbone_rmsd": NAN,
            "boltz_seed": "", "source_tag": "manifest+scores.json",
            "stored_p_high": num(r.get("p_high")),
            "csv_iptm": NAN, "csv_plddt": NAN,
        }
        seeds = find_seed_dirs(out_dir, qid)
        rec.update(attach_structure(seeds))
        if seeds:
            rec["boltz_seed"] = os.path.basename(seeds[0]).replace("seed_", "")
        rows.append(rec)
        if limit and len(rows) >= limit:
            break
    return rows


def collect_legal(limit=None) -> list[dict]:
    """people/anas/legal-scored.csv: the top 5,000 enumerated loops by FACS p_high.
    Sequence only, no structure."""
    path = os.path.join(HOME, "people/anas/legal-scored.csv")
    rows = []
    for i, r in enumerate(csv.DictReader(open(path, newline="", encoding="utf-8")), 1):
        rows.append({
            "run": "legal-scored", "generator": "legal-scored",
            "query_id": f"legal_{i:05d}",
            "cdrh3": r["cdrh3"].strip().upper(),
            "binder_sequence": (r.get("binder_sequence") or "").strip(),
            "min_ipae": NAN, "binder_plddt": NAN, "backbone_rmsd": NAN,
            "boltz_seed": "", "source_tag": "legal-scored",
            "stored_p_high": num(r.get("p_high")),
            "csv_iptm": NAN, "csv_plddt": NAN,
            "n_seeds": 0, "structure_path": "",
            "iface_min": NAN, "iface_mean": NAN, "iptm": NAN, "ptm": NAN,
            "plddt": NAN, "pde": NAN, "binder_ptm": NAN, "ranking": NAN,
            "seed_iface_min_sd": NAN, "seed_iface_mean_sd": NAN,
        })
        if limit and len(rows) >= limit:
            break
    return rows


def attach_structure(seed_dirs: list[str]) -> dict:
    """Read every seed of one candidate. Boltz-2 was run with one seed and one
    diffusion sample throughout, but this handles more and reports the seed-to-seed SD
    so a noise floor can be set if replicates are ever produced."""
    base = {"n_seeds": len(seed_dirs), "structure_path": "",
            "iface_min": NAN, "iface_mean": NAN, "iptm": NAN, "ptm": NAN,
            "plddt": NAN, "pde": NAN, "binder_ptm": NAN, "ranking": NAN,
            "seed_iface_min_sd": NAN, "seed_iface_mean_sd": NAN}
    if not seed_dirs:
        return base
    per_seed = []
    for sd in seed_dirs:
        sj = seed_scores(sd)
        if sj:
            per_seed.append((sd, iface_from_scores(sj)))
    if not per_seed:
        return base
    # best seed = highest ranking score, the quantity Boltz-2 itself ranks on
    best_dir, best = max(per_seed, key=lambda t: t[1]["ranking"])
    base.update(best)
    base["structure_path"] = seed_cif(best_dir)
    base["n_seeds"] = len(per_seed)
    if len(per_seed) > 1:
        base["seed_iface_min_sd"] = statistics.stdev([s["iface_min"] for _, s in per_seed])
        base["seed_iface_mean_sd"] = statistics.stdev([s["iface_mean"] for _, s in per_seed])
    return base


# ------------------------------------------------------------------------- the gates

def score_row(rec: dict, pool) -> None:
    """Fill every sequence-derived gate. Identical arithmetic to rank.py / report.py."""
    cdr = rec["cdrh3"]
    dist, nearest = novelty.min_distance(cdr, pool)
    idt = novelty.identity_to_trastuzumab(cdr)

    rec["dist_min_provided"] = dist
    rec["nearest_provided"] = nearest
    rec["pct_identity_to_trastuzumab"] = idt
    rec["n_mut_vs_WT"] = sum(1 for a, b in zip(cdr, report.WILD_TYPE) if a != b)

    rec["novelty_official"] = bool(dist >= 2 and idt <= 70.0)
    rec["novelty_margin"] = bool(dist >= rank.MIN_DIST and idt <= rank.MAX_IDENTITY)
    rec["has_cys"] = "C" in cdr

    # liabilities: report.LIABILITY = {102: "D", 107: "M"}
    rec["liab_D102_removed"] = cdr[102 - report.CDRH3_FROM] != "D"
    rec["liab_M107_removed"] = cdr[107 - report.CDRH3_FROM] != "M"
    rec["liabilities_removed"] = int(rec["liab_D102_removed"]) + int(rec["liab_M107_removed"])

    kept = [p for p, aa in sorted(report.CONTACT.items()) if cdr[p - report.CDRH3_FROM] == aa]
    lost = [f"{report.CONTACT[p]}{p}->{cdr[p - report.CDRH3_FROM]}"
            for p in sorted(report.CONTACT) if cdr[p - report.CDRH3_FROM] != report.CONTACT[p]]
    rec["grip_4of4"] = len(kept) == 4
    rec["anchors_kept"] = ";".join(f"{report.CONTACT[p]}{p}" for p in kept)
    rec["anchors_lost"] = ";".join(lost)
    rec["grip_verdict"], _ = report.hypothesis(cdr)

    # rank.py's reject string, verbatim logic (rank.py lines 113-119). It is built in
    # memory there and never written to a file; this is the column that was missing.
    reject = []
    if dist < 2 or idt > 70.0:
        reject.append("official")
    if dist < rank.MIN_DIST or idt > rank.MAX_IDENTITY:
        reject.append("margin")
    if "C" in cdr:
        reject.append("Cys")
    rec["reject_reason"] = ",".join(reject)


def label_row(rec: dict, wt_inbatch: dict, wt_external: float) -> None:
    """Apply the pre-registered hierarchy. Two labels are produced:
       group              uses the in-batch WT when the run has one, else the run-006
                          WT as an external reference (wt_ref says which)
       group_strict_wtref refuses to judge the interface gate without an in-batch WT
    """
    wt_b = wt_inbatch.get(rec["run"], NAN)
    rec["template_sha"] = TEMPLATE_SHA.get(rec["run"], "")
    if fin(wt_b):
        rec["wt_ref"] = "in-batch"
    elif fin(rec["iface_min"]):
        # The external reference is the run-006 WT. It is only a like-for-like
        # comparison when the run shares run 006's Boltz-2 template.
        rec["wt_ref"] = ("external-same-template"
                         if TEMPLATE_SHA.get(rec["run"]) == TEMPLATE_SHA.get("006")
                         else "external-diff-template")
    else:
        rec["wt_ref"] = "none"
    rec["iface_min_minus_WT_batch"] = (rec["iface_min"] - wt_b) if (fin(wt_b) and fin(rec["iface_min"])) else NAN
    rec["iface_min_minus_WT_extref"] = (rec["iface_min"] - wt_external) if fin(rec["iface_min"]) else NAN

    seq_gates = (rec["novelty_margin"] and not rec["has_cys"]
                 and rec["liabilities_removed"] == 2 and rec["grip_4of4"]
                 and fin(rec["p_high"]) and rec["p_high"] >= P_HIGH_GATE)
    rec["pass_seq_gates"] = seq_gates

    def first_failure(ref: float) -> str | None:
        if not rec["novelty_official"]:
            return "novelty_official"
        if not rec["novelty_margin"]:
            return "novelty_margin"
        if rec["has_cys"]:
            return "cys"
        if rec["liabilities_removed"] != 2:
            return "liability"
        if not rec["grip_4of4"]:
            return "grip"
        if not (fin(rec["p_high"]) and rec["p_high"] >= P_HIGH_GATE):
            return "p_high"
        if fin(rec["iface_min"]) and fin(ref) and rec["iface_min"] < ref - IFACE_SOFT_MARGIN:
            return "iface"
        return None

    def decide(ref: float) -> str:
        bad = first_failure(ref)
        if bad:
            return "FAIL_" + bad
        if not fin(rec["iface_min"]):
            return "PASS_SEQ"            # no structure: sequence-only verdict
        if not fin(ref):
            return "PASS_SEQ"            # structure but no usable WT reference
        if rec["iface_min"] >= ref:
            return "PASS_STRICT"
        return "PASS_SOFT"               # within the 0.03 band, else first_failure fired

    ref_primary = wt_b if fin(wt_b) else (wt_external if fin(rec["iface_min"]) else NAN)
    rec["group"] = decide(ref_primary)
    if fin(rec["iface_min"]) and not fin(wt_b):
        rec["group_strict_wtref"] = ("NA_no_inbatch_WT" if first_failure(NAN) is None
                                     else "FAIL_" + first_failure(NAN))
    else:
        rec["group_strict_wtref"] = rec["group"]


# ------------------------------------------------------------------------- reporting

CSV_COLS = [
    "candidate_id", "run", "generator", "query_id", "cdrh3",
    "n_mut_vs_WT", "dist_min_provided", "nearest_provided", "pct_identity_to_trastuzumab",
    "novelty_official", "novelty_margin", "has_cys",
    "liab_D102_removed", "liab_M107_removed", "liabilities_removed",
    "grip_4of4", "anchors_kept", "anchors_lost", "grip_verdict",
    "p_high", "stored_p_high",
    "iface_min", "iface_mean", "iface_min_minus_WT_batch", "iface_min_minus_WT_extref", "wt_ref",
    "binder_plddt", "plddt", "min_ipae", "iptm", "ptm", "pde", "binder_ptm", "ranking",
    "backbone_rmsd", "n_seeds", "seed_iface_min_sd", "seed_iface_mean_sd",
    "structure_path", "has_structure", "boltz_seed", "template_sha",
    "pass_seq_gates", "reject_reason", "group", "group_strict_wtref",
    "cdrh3_n_rows_in_table", "is_exact_dup", "source_tag",
]

METRIC_COLS = ["p_high", "iface_min", "iface_mean", "binder_plddt", "min_ipae",
               "n_mut_vs_WT", "dist_min_provided", "pct_identity_to_trastuzumab",
               "iface_min_minus_WT_batch", "iface_min_minus_WT_extref"]


def write_csv(rows: list[dict], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            out = {}
            for c in CSV_COLS:
                v = r.get(c, "")
                if isinstance(v, bool):
                    v = "TRUE" if v else "FALSE"
                elif isinstance(v, float):
                    v = "" if not fin(v) else f"{v:.6g}"
                out[c] = v
            w.writerow(out)


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join("---" for _ in headers) + " |"]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out)


def funnel(rows: list[dict]) -> list[list[str]]:
    """Cumulative funnel: generated -> each gate in order -> shortlisted."""
    groups = defaultdict(list)
    for r in rows:
        groups[r["run"]].append(r)
    order = ["001", "004", "005", "006", "legal-scored"]
    out = []
    for key in [k for k in order if k in groups] + ["ALL"]:
        sub = rows if key == "ALL" else groups[key]
        n0 = len(sub)
        s = [r for r in sub if r["novelty_official"]]
        n1 = len(s)
        s = [r for r in s if r["novelty_margin"]]
        n2 = len(s)
        s = [r for r in s if not r["has_cys"]]
        n3 = len(s)
        s = [r for r in s if r["liabilities_removed"] == 2]
        n4 = len(s)
        s = [r for r in s if r["grip_4of4"]]
        n5 = len(s)
        s = [r for r in s if fin(r["p_high"]) and r["p_high"] >= P_HIGH_GATE]
        n6 = len(s)
        strict = sum(1 for r in s if r["group"] == "PASS_STRICT")
        soft = sum(1 for r in s if r["group"] == "PASS_SOFT")
        seqp = sum(1 for r in s if r["group"] == "PASS_SEQ")
        out.append([key, n0, n1, n2, n3, n4, n5, n6, strict, soft, seqp, strict + soft + seqp])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", required=True,
                    help="directory for first_pass_candidates.csv and first_pass_summary.md")
    ap.add_argument("--legal-limit", type=int, default=0,
                    help="only read the first N rows of legal-scored.csv (smoke tests)")
    ap.add_argument("--skip-legal", action="store_true", help="omit legal-scored.csv entirely")
    args = ap.parse_args()

    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    print(f"interpreter      {sys.executable}")
    print(f"out-dir          {out_dir}")
    print(f"novelty margin   dist >= {rank.MIN_DIST}, identity <= {rank.MAX_IDENTITY:.0f} % "
          f"(official: dist >= 2, identity <= 70 %)")
    print(f"p_high gate      {P_HIGH_GATE}   iface soft margin {IFACE_SOFT_MARGIN}\n")

    load_templates()
    print("Boltz-2 template sha256 per run: "
          + ", ".join(f"{k} {v[:12]}" for k, v in sorted(TEMPLATE_SHA.items())))
    print("  (runs sharing a sha share a template and are directly comparable)\n")

    # ---- collect
    rows: list[dict] = []
    for run, gen, kind, slug in SOURCES:
        if kind == "metrics":
            got = collect_metrics_run(run, gen, slug)
        elif kind == "manifest":
            got = collect_manifest_run(run, slug)
        else:
            if args.skip_legal:
                continue
            got = collect_legal(args.legal_limit or None)
        print(f"  {run:<13} {len(got):>5} rows")
        rows.extend(got)
    print(f"  {'TOTAL':<13} {len(rows):>5} rows\n")

    for r in rows:
        r["candidate_id"] = f"{r['run']}:{r['query_id']}"
        r["has_structure"] = fin(r["iface_min"])

    # ---- sequence gates, cached by CDRH3 (the same loop appears in several sources)
    pool = novelty.load()
    provided = sum(a.shape[0] for a in pool.values())
    print(f"provided CDRH3 pool: {provided:,} unique")
    cache: dict[str, dict] = {}
    for i, r in enumerate(rows, 1):
        cdr = r["cdrh3"]
        if cdr not in cache:
            probe = {"cdrh3": cdr}
            score_row(probe, pool)
            cache[cdr] = probe
        r.update({k: v for k, v in cache[cdr].items() if k != "cdrh3"})
        if i % 1000 == 0:
            print(f"  novelty {i}/{len(rows)} ({len(cache)} distinct loops)")
    print(f"  novelty done, {len(cache)} distinct loops evaluated\n")

    # ---- p_high, one model load for everything, via rank.py's own wrapper
    ph = rank.p_high([r["cdrh3"] for r in rows])
    for r, p in zip(rows, ph):
        r["p_high"] = float(p)
    drift = [abs(r["p_high"] - r["stored_p_high"]) for r in rows if fin(r["stored_p_high"])]
    print(f"p_high recomputed for {len(rows)} rows; cross-checked against "
          f"{len(drift)} stored values, max |diff| {max(drift) if drift else 0:.2e}\n")

    # ---- duplicates
    counts = Counter(r["cdrh3"] for r in rows)
    for r in rows:
        r["cdrh3_n_rows_in_table"] = counts[r["cdrh3"]]
        r["is_exact_dup"] = counts[r["cdrh3"]] > 1

    # ---- WT references
    wt_inbatch: dict[str, float] = {}
    for r in rows:
        if r["query_id"] == "trastuzumab_wt" and fin(r["iface_min"]):
            wt_inbatch[r["run"]] = r["iface_min"]
    wt_external = wt_inbatch.get("006", NAN)
    print("in-batch trastuzumab_wt iface_min: "
          + (", ".join(f"run {k} {v:.4f}" for k, v in sorted(wt_inbatch.items())) or "none"))
    print(f"external reference (run 006 WT): {fmt(wt_external, 4)}\n")

    for r in rows:
        label_row(r, wt_inbatch, wt_external)

    rows.sort(key=lambda r: (["001", "004", "005", "006", "legal-scored"].index(r["run"]),
                             r["query_id"]))

    csv_path = os.path.join(out_dir, "first_pass_candidates.csv")
    write_csv(rows, csv_path)
    print(f"wrote {csv_path}  ({len(rows)} rows, {len(CSV_COLS)} columns)")

    md_path = os.path.join(out_dir, "first_pass_summary.md")
    validation = write_summary(rows, md_path, wt_inbatch, wt_external, provided, drift, args)
    print(f"wrote {md_path}")

    print("\nvalidation against the read-only survey")
    bad = 0
    for name, exp, got in validation:
        ok = "ok" if exp == got else "MISMATCH"
        if exp != got:
            bad += 1
        print(f"  {name:<52} expected {exp:>5}  got {got:>5}  {ok}")
    print(f"\n{len(validation) - bad}/{len(validation)} survey counts reproduced")

    print("\nReminder, unchanged: confidence is not affinity. 21 measured non-binders in the")
    print("Champloo set score AF3 ipTM >= 0.7, and p_high is capped by the wild type at")
    print("0.998, so neither column can carry an affinity claim.")
    return 0


def write_summary(rows, path, wt_inbatch, wt_external, provided, drift, args) -> list[tuple]:
    structured = [r for r in rows if r["has_structure"]]
    L = []
    A = L.append

    A("# First-pass candidate table — HER2 binder optimisation\n")
    A(f"Generated by `scripts/first_pass.py` on {os.popen('date -Iseconds').read().strip()}  ")
    A(f"Interpreter: `{sys.executable}` (Python "
      f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro})  ")
    A(f"Table: `first_pass_candidates.csv`, {len(rows)} rows, {len(CSV_COLS)} columns, "
      f"{len(structured)} with a Boltz-2 structure\n")
    A("Analysis only: no GPU, no network, nothing written outside this run directory.\n")

    # ---------------------------------------------------------------- (a) measured inputs
    A("## (a) The provided measured inputs\n")
    A("Reused verbatim from existing outputs — `trastuzumab_epitope/data/"
      "workspace_variant_data_inventory.json`, `cdrh3_spr_summary.csv` and "
      "`cdrh3_position_summary.csv`. Nothing here was recomputed.\n")
    A("**FACS, 524,346 variants** (`tz_her2_facs_3classes_524346.csv.zip`), every CDRH3 "
      "10 aa at VH 99–108, edit distance 1–10 from WT, VL invariant, WT itself absent:\n")
    A(md_table(["binding_class", "n", "share"],
               [["high", "172,149", "32.83 %"],
                ["medium", "190,011", "36.24 %"],
                ["low", "162,186", "30.93 %"],
                ["**total**", "**524,346**", "100 %"]]))
    A("")
    A("Label balance is close to even (32.8 / 36.2 / 30.9 %), so `p_high` is not fighting "
      "a rare-class problem; its ceiling problem is that the wild type itself scores 0.998.\n")
    A("**SPR, 768 rows** (`trastuzumab_her2_spr_all_768.csv`), 754 unique CDRH3, "
      "lengths 9/10/16 = 20/740/8:\n")
    A(md_table(["quantity", "value"],
               [["rows with a quantified KD", "190 of 768"],
                ["`binding_result` split",
                 "quantified_binding 190, no_reportable_kd 460, inconclusive 104, not_reported 14"],
                ["KD range (quantified)", "0.02344 – 13,863.2 nM"],
                ["KD median (quantified)", "66.0271 nM"],
                ["**WT KD, row 1**", "**0.152 nM**"],
                ["WT replicates", "8, KD 0.02852 / 0.03787 / 0.07916 / 0.1230 / 0.1460 / 0.1520 / 0.1650 / 0.1780 nM"],
                ["WT median (n=8)", "0.1345 nM, 6.2× spread min→max"],
                ["best measured variant", "WGSQGFYAYD (G101S;D102Q;M107Y) KD 0.02344 nM, 5.7× better than the WT median"]]))
    A("")
    A("The WT was measured eight times across a 6.2-fold range. An improvement claim has "
      "to beat that spread, not the single 0.152 nM figure.\n")
    A("**Per-position tolerance** (`cdrh3_position_summary.csv`, adjusted log-odds of "
      "`binding_class == high` on the FACS table). Three of the six positions the design "
      "track treats as free are statistically intolerant:\n")
    A(md_table(["pos", "Kabat", "wt", "label", "OR_high", "top enriched", "top depleted"],
               [["W99", "H95", "W", "moderate", "0.902", "N +0.44", "I −1.92"],
                ["G100", "H96", "G", "**intolerant**", "0.436", "A +0.31", "K −2.57"],
                ["G101", "H97", "G", "**intolerant**", "0.404", "A +1.20", "H −2.08"],
                ["D102", "H98", "D", "tolerant", "1.191", "G +1.58", "Y −1.10"],
                ["G103", "H99", "G", "**intolerant**", "0.992 (q=0.17)", "R +1.93", "K −2.13"],
                ["F104", "H100", "F", "moderate", "0.578", "G +0.88", "E −1.99"],
                ["Y105", "H100A", "Y", "moderate", "0.962", "W +0.83", "I −0.73"],
                ["A106", "H100B", "A", "moderate", "0.535", "S +0.89", "L −1.86"],
                ["M107", "H100C", "M", "moderate", "0.704", "T +0.61", "D −1.70"],
                ["D108", "H101", "D", "**intolerant**", "0.221", "N −0.54", "S −2.89"]]))
    A("")
    A(f"Novelty pool: **{provided:,}** unique provided CDRH3 "
      f"(len9 20 / len10 525,042 / len16 1), from `provided_cdrh3.npz`.\n")

    # ------------------------------------------------------------------- (b) funnel
    A("## (b) Funnel\n")
    A("Cumulative: every column is the subset that survived all gates to its left. "
      "Gate order is the pre-registered one. `PASS_*` columns are the final labels.\n")
    A(md_table(["run", "generated", "novelty_official", "novelty_margin", "no_Cys",
                "liab 2/2", "grip 4/4", f"p_high≥{P_HIGH_GATE}",
                "PASS_STRICT", "PASS_SOFT", "PASS_SEQ", "shortlisted"],
               [[str(x) for x in r] for r in funnel(rows)]))
    A("")
    A("Read the `ALL` row with care: the same CDRH3 can appear in more than one source "
      "(see the duplicate caveat), so `ALL` is a row count, not a count of distinct loops.")
    uniq = len({r["cdrh3"] for r in rows})
    uniq_pass = len({r["cdrh3"] for r in rows if r["group"].startswith("PASS")})
    A(f"Distinct CDRH3 in the table: **{uniq:,}**; distinct CDRH3 in any PASS group: "
      f"**{uniq_pass:,}**.\n")

    A("### Group sizes per run\n")
    labels = sorted({r["group"] for r in rows})
    grid = []
    for key in ["001", "004", "005", "006", "legal-scored"]:
        sub = [r for r in rows if r["run"] == key]
        if not sub:
            continue
        c = Counter(r["group"] for r in sub)
        grid.append([key, len(sub)] + [c.get(l, 0) for l in labels])
    c = Counter(r["group"] for r in rows)
    grid.append(["**ALL**", len(rows)] + [c.get(l, 0) for l in labels])
    A(md_table(["run", "n"] + labels, [[str(x) for x in r] for r in grid]))
    A("")
    A("### Group sizes per generator\n")
    grid = []
    for key in ["free-loop", "anchored", "enumerated", "control", "legal-scored"]:
        sub = [r for r in rows if r["generator"] == key]
        if not sub:
            continue
        c = Counter(r["group"] for r in sub)
        grid.append([key, len(sub)] + [c.get(l, 0) for l in labels])
    A(md_table(["generator", "n"] + labels, [[str(x) for x in r] for r in grid]))
    A("")

    # ------------------------------------------------------------- (c) distributions
    A("## (c) Metric distributions by group\n")
    A("`iface_min_minus_WT_batch` is populated only for run 006, the one batch with an "
      "in-batch `trastuzumab_wt`; `iface_min_minus_WT_extref` uses the run-006 WT "
      "(`iface_min` " + fmt(wt_external, 4) + ") for every structured row.\n")
    buckets = [("PASS_STRICT", lambda r: r["group"] == "PASS_STRICT"),
               ("PASS_SOFT", lambda r: r["group"] == "PASS_SOFT"),
               ("PASS_SEQ", lambda r: r["group"] == "PASS_SEQ"),
               ("FAIL (any)", lambda r: r["group"].startswith("FAIL"))]
    for metric in METRIC_COLS:
        grid = []
        for name, pred in buckets:
            s = stats([r[metric] for r in rows if pred(r)])
            grid.append([name, s["n"], fmt(s["mean"], 4), fmt(s["sd"], 4),
                         fmt(s["min"], 4), fmt(s["median"], 4), fmt(s["max"], 4)])
        A(f"**{metric}**\n")
        A(md_table(["group", "n", "mean", "SD", "min", "median", "max"],
                   [[str(x) for x in r] for r in grid]))
        A("")
    A("Same table restricted to the structured rows only (runs 001/004/005/006, "
      f"n={len(structured)}), which removes the 5,000 legal-scored rows that otherwise "
      "dominate every PASS_SEQ cell:\n")
    for metric in ["p_high", "iface_min", "iface_mean", "binder_plddt", "min_ipae",
                   "n_mut_vs_WT", "dist_min_provided", "pct_identity_to_trastuzumab"]:
        grid = []
        for name, pred in buckets:
            s = stats([r[metric] for r in structured if pred(r)])
            if s["n"] == 0:
                continue
            grid.append([name, s["n"], fmt(s["mean"], 4), fmt(s["sd"], 4),
                         fmt(s["min"], 4), fmt(s["median"], 4), fmt(s["max"], 4)])
        A(f"**{metric}** (structured only)\n")
        A(md_table(["group", "n", "mean", "SD", "min", "median", "max"],
                   [[str(x) for x in r] for r in grid]))
        A("")

    # ------------------------------------------------- (d) per-position residue counts
    A("## (d) Per-position CDRH3 residue counts, PASS vs FAIL\n")
    A("Positions are VH seq_index 99–108. Contact anchors 99/103/104/105 and liabilities "
      "D102/M107 are marked. `PASS` = any PASS_* group.\n")
    for scope, sub in [("all rows", rows), ("structured rows only", structured)]:
        A(f"### {scope} (n={len(sub)})\n")
        p = [r for r in sub if r["group"].startswith("PASS")]
        f = [r for r in sub if r["group"].startswith("FAIL")]
        grid = []
        for i in range(10):
            pos = 99 + i
            tag = ""
            if pos in report.CONTACT:
                tag = " (anchor)"
            if pos in report.LIABILITY:
                tag = " (liability)"
            cp = Counter(r["cdrh3"][i] for r in p)
            cf = Counter(r["cdrh3"][i] for r in f)
            grid.append([f"{report.WILD_TYPE[i]}{pos}{tag}",
                         len(p),
                         " ".join(f"{a}:{n}" for a, n in cp.most_common()) or "-",
                         len(f),
                         " ".join(f"{a}:{n}" for a, n in cf.most_common()) or "-"])
        A(md_table(["position", "n PASS", "PASS residues", "n FAIL", "FAIL residues"],
                   [[str(x) for x in r] for r in grid]))
        A("")

    # ------------------------------------------------------------ (e) sensitivity grid
    A("## (e) Sensitivity grid\n")
    A("Pre-registered, reported instead of tuning the thresholds. `dist≥2` is paired with "
      "the official identity rule (≤70 %) and `dist≥3` with the internal margin (≤60 %), "
      "because those are the two rule sets the project actually uses. Cells count rows "
      "passing novelty + no-Cys + liabilities 2/2 + grip 4/4 + the stated `p_high` + "
      "`iface_min ≥ WT + margin`; only structured rows can satisfy the interface term, so "
      "each cell is out of "
      f"{len(structured)} structured rows.\n")
    for d in GRID_DIST:
        maxid = 70.0 if d == 2 else 60.0
        A(f"**dist ≥ {d}, identity ≤ {maxid:.0f} %**\n")
        grid = []
        for pt in GRID_P_HIGH:
            row = [f"p_high ≥ {pt:.2f}"]
            for m in GRID_IFACE:
                n = 0
                for r in structured:
                    if r["dist_min_provided"] < d or r["pct_identity_to_trastuzumab"] > maxid:
                        continue
                    if r["has_cys"] or r["liabilities_removed"] != 2 or not r["grip_4of4"]:
                        continue
                    if not (fin(r["p_high"]) and r["p_high"] >= pt):
                        continue
                    ref = (wt_inbatch.get(r["run"]) if fin(wt_inbatch.get(r["run"], NAN))
                           else wt_external)
                    if not (fin(ref) and r["iface_min"] >= ref + m):
                        continue
                    n += 1
                row.append(str(n))
            grid.append(row)
        A(md_table(["", "iface −0.05", "iface −0.03", "iface +0.00", "iface +0.02"],
                   [[str(x) for x in r] for r in grid]))
        A("")
    A("Sequence-only counts (no interface term), which is what the 5,000 legal-scored "
      "rows can be judged on:\n")
    grid = []
    for d in GRID_DIST:
        maxid = 70.0 if d == 2 else 60.0
        row = [f"dist ≥ {d}, id ≤ {maxid:.0f} %"]
        for pt in GRID_P_HIGH:
            n = sum(1 for r in rows
                    if r["dist_min_provided"] >= d and r["pct_identity_to_trastuzumab"] <= maxid
                    and not r["has_cys"] and r["liabilities_removed"] == 2 and r["grip_4of4"]
                    and fin(r["p_high"]) and r["p_high"] >= pt)
            row.append(str(n))
        grid.append(row)
    A(md_table(["novelty rule"] + [f"p_high ≥ {p:.2f}" for p in GRID_P_HIGH],
               [[str(x) for x in r] for r in grid]))
    A("")

    # --------------------------------------------------------------------- seed noise
    A("## Seed and replicate noise\n")
    multi = [r for r in rows if r.get("n_seeds", 0) > 1]
    A(f"**Candidates with more than one Boltz-2 seed: {len(multi)}.** Every run was "
      "submitted with `--num-diffusion-samples 1` and a single seed, and on disk every "
      "`boltz2/<qid>/` holds exactly one `seed_42/` with one `sample_1` triple. So the "
      "seed-to-seed SD of `iface_min` / `iface_mean` **cannot be computed from existing "
      "data**: there are no replicates at a second seed anywhere in the project.\n")
    A("What *can* be measured is the replicate SD for the same CDRH3 folded more than "
      "once at the same seed. Those pseudo-replicates split cleanly by whether the two "
      "runs shared a Boltz-2 template:\n")
    xb = defaultdict(list)
    for r in structured:
        xb[r["cdrh3"]].append(r)
    reps = {k: v for k, v in xb.items() if len(v) > 1}
    grid = []
    for k, v in sorted(reps.items()):
        same_run = len({x["run"] for x in v}) == 1
        same_tpl = len({x["template_sha"] for x in v}) == 1
        kind = ("within-batch" if same_run else "cross-batch")
        grid.append([kind, "yes" if same_tpl else "**no**",
                     ", ".join(sorted(f"{x['run']}:{x['query_id']}" for x in v)),
                     fmt(statistics.stdev([x["iface_min"] for x in v]), 6),
                     fmt(statistics.stdev([x["iface_mean"] for x in v]), 6),
                     fmt(max(x["iface_min"] for x in v) - min(x["iface_min"] for x in v), 6)])
    if grid:
        A(md_table(["kind", "same template", "rows (same CDRH3, same seed 42)",
                    "SD iface_min", "SD iface_mean", "range iface_min"],
                   [[str(x) for x in r] for r in grid]))
        A("")
    A("Two distinct numbers come out of that table, and they must not be conflated:\n")
    A("- **Same seed, same template → SD exactly 0.000000.** Boltz-2 is bit-reproducible: "
      "the three run-004 designs re-folded as run-006 controls reproduce run 004 to every "
      "printed digit on all eight score fields, and run 005's triplicated loop gives three "
      "identical rows. Batch composition (10 queries vs 44) changes nothing.\n")
    A("- **Same seed, different template → SD ≈ 0.0018, range 0.0025 on `iface_min`** "
      "(the single sequence shared by runs 001 and 004: `iface_min` 0.9355 vs 0.9330, "
      "`iptm` 0.965 vs 0.967, `plddt` 97.102 vs 97.132). n = 1 sequence, so this is an "
      "order of magnitude, not an estimate.\n")
    A("**Recommended noise floor, stated honestly:** the replicate floor is 0, the "
      "template-swap floor is ~0.003 on `iface_min`, and the seed floor is **unknown**. "
      "Since the whole run-006 shortlist is spread over about 0.14 of `iface_min` and the "
      "8 candidates \"above WT\" beat it by 0.003–0.014, the margins that decide the "
      "shortlist are the same size as the one perturbation that has been measured. Until a "
      "second seed is run, do not treat an `iface_min` gap under ~0.01 as real. Getting "
      "the number is one short GPU job: re-fold ~10 run-006 candidates plus the WT at a "
      "second seed in one batch with the same template. Not done here (no GPU).\n")

    # ---------------------------------------------------------------------- validation
    A("## Validation against the read-only survey\n")
    r004 = [r for r in rows if r["run"] == "004"]
    r005 = [r for r in rows if r["run"] == "005"]
    r006c = [r for r in rows if r["run"] == "006" and r["generator"] == "enumerated"]
    wt006 = wt_inbatch.get("006", NAN)
    best_gen = max([r["iface_min"] for r in rows
                    if r["run"] == "006" and r["query_id"].startswith("r004")] or [NAN])
    validation = [
        ("run 004 novelty_official pass", 10, sum(1 for r in r004 if r["novelty_official"])),
        ("run 004 novelty_margin pass", 9, sum(1 for r in r004 if r["novelty_margin"])),
        ("run 004 grip 4/4", 0, sum(1 for r in r004 if r["grip_4of4"])),
        ("run 005 novelty_official pass", 1, sum(1 for r in r005 if r["novelty_official"])),
        ("run 005 novelty_margin pass", 0, sum(1 for r in r005 if r["novelty_margin"])),
        ("run 005 grip 4/4", 10, sum(1 for r in r005 if r["grip_4of4"])),
        ("run 006 candidates above WT iface_min 0.901", 8,
         sum(1 for r in r006c if fin(r["iface_min"]) and r["iface_min"] > wt006)),
        ("run 006 candidates above r004 best iface_min 0.933", 0,
         sum(1 for r in r006c if fin(r["iface_min"]) and r["iface_min"] > best_gen)),
    ]
    A(md_table(["survey claim", "expected", "reproduced", "verdict"],
               [[n, e, g, "ok" if e == g else "**MISMATCH**"] for n, e, g in validation]))
    A("")
    A(f"Reference values used: run-006 in-batch `trastuzumab_wt` `iface_min` "
      f"**{fmt(wt006, 4)}** (survey said 0.901), best run-004 generator control "
      f"`iface_min` **{fmt(best_gen, 4)}** (survey said 0.933).")
    if drift:
        A(f"`p_high` was recomputed for all {len(rows)} rows with `rank.p_high` and agrees "
          f"with the {len(drift)} values stored in `manifest.csv` / `legal-scored.csv` to "
          f"max |diff| **{max(drift):.2e}**.")
    A("")

    # ----------------------------------------------------------------------- caveats
    A("## (f) Caveats and handling recommendations\n")
    A("**1. Generator is confounded with every sequence gate, almost perfectly.** "
      "Run 004 (free loop) is 10/10 novelty-official and 0/10 grip. Run 005 (anchored) is "
      "10/10 grip and 1/10 novelty-official. Run 006 (enumerated) is 40/40 on both, by "
      "construction — the enumeration *filtered on these very gates* before folding. Any "
      "\"what do the passing candidates have in common\" analysis over the pooled table "
      "recovers the generator setting, not biology. Stratify by run, or stay inside one "
      "run. The per-position tables in (d) are reported for both scopes for exactly this "
      "reason and neither should be read as an enrichment analysis.\n")
    A("**2. Run 006 has near-zero variance on everything except the interface.** "
      "All 40 enumerated candidates are novelty-legal, Cys-free, 4/4 grip, 2/2 liabilities, "
      "`p_high` in a 0.0056-wide band, `n_mut` 4–6. There is nothing to regress a pass/fail "
      "flag against inside that batch; `iface_min` is the only discriminator, and it spans "
      "roughly 0.77–0.92. Treat run 006 as a ranking problem on one noisy column, not a "
      "classification problem.\n")
    A("**3. Exact duplicates.** "
      f"{sum(1 for r in rows if r['is_exact_dup'])} rows share a CDRH3 with another row "
      f"({len(rows) - uniq} rows are redundant). Three separate causes, all benign but all "
      "capable of inflating a count: (i) run 005 generated one loop three times in one "
      "batch; (ii) three run-004 designs were deliberately re-folded as run-006 controls; "
      "(iii) all 40 run-006 candidates are also rows of `legal-scored.csv`, which is where "
      "they were drawn from. Deduplicate on `cdrh3` before quoting any overall total — the "
      "`ALL` funnel row and the `cdrh3_n_rows_in_table` / `is_exact_dup` columns are there "
      "to make this visible.\n")
    A("**4. Threshold conflicts between the project's own files.** Four live "
      "disagreements, all preserved rather than silently resolved:\n")
    A(md_table(["rule", "README.md", "notes/DECISIONS.md", "scripts/novelty.py",
                "people/anas/rank.py", "people/anas/feasible.py", "this table"],
               [["min distance to provided", "≥ 2", "≥ 3", "≥ 2 (hard)", "≥ 3 (`MIN_DIST`)",
                 "≥ 3", "both, as `novelty_official` and `novelty_margin`"],
                ["max identity to trastuzumab", "≤ 70 %", "≤ 60 %", "≤ 70 % (hard)",
                 "≤ 60 % (`MAX_IDENTITY`)", "≤ 60 %", "both"],
                ["cysteine", "—", "—", "soft warning `ok, check C`", "hard reject",
                 "excluded from the space", "`has_cys` column + `FAIL_cys` gate"],
                ["min pairwise diff", "—", "—", "—", "2 (`--min-diff`)",
                 "3 (`build_refold.py`)", "not applied; diversity is a selection step, "
                 "not a gate"]]))
    A("")
    A("`report.py` prints `REJECTED` on the **official** rule only, so a design that "
      "`run.log` shows as `ok` can still be dropped by `rank.py`. Run 004's "
      "`her2_cdrh3_26` (dist 2) and run 005's `her2_anchored_14` (dist 2, 60 %) are exactly "
      "those cases, and they are the two rows where `novelty_official` is TRUE and "
      "`novelty_margin` is FALSE. A reader of `README.md` alone gets the looser bar.\n")
    A("**5. Seeds: the survey conflates two different seeds — corrected here.** "
      "`design/config.json` gives the **RFD4 generation** seed: 1 for runs 001/004/005, "
      "2 for run 007. `boltz2/config.json` gives the **Boltz-2 refold** seed, and it is "
      "**42 for every run, 001 through 006**, confirmed three ways: the config files, the "
      "`seed_42/` directory names, and the `seed` column of every `refold_metrics.csv`. "
      "So the structural numbers are *not* separated by seed, and the survey's \"seeds "
      "differ between tracks, 1 vs 42\" caveat does not apply to anything structural. "
      "Chain layout is also identical everywhere (A 107 / B 120 / C 92 / D 17) as is "
      "`num_diffusion_samples 1`.\n")
    A("**5b. What *does* break cross-run comparability is the template, not the seed.** "
      "Each run's `prepared/holo/template.cif` is built from one of that run's own "
      "generated designs — the mmCIF data block is literally named "
      "`data_her2_cdrh3_3_template` in run 001 and `data_her2_cdrh3_21_template` in run "
      "004 — so it is a per-run artifact, not a shared constant:\n")
    A(md_table(["run", "template sha256 (16)", "comparable to run 006?"],
               [[run, TEMPLATE_SHA.get(run, "-") or "-",
                 "**yes, byte-identical**" if TEMPLATE_SHA.get(run) == TEMPLATE_SHA.get("006")
                 else "no, different template"]
                for run in ["001", "004", "005", "006"]]))
    A("")
    A("`build_refold.py` copies run 004's template verbatim (`shutil.copy` from "
      "`REF_RUN`), so **runs 004 and 006 share a byte-identical template** and their "
      "numbers are directly comparable — proven, not assumed: the three `r004_*` controls "
      "reproduce their run-004 values exactly. Runs 001 and 005 each used a different "
      "template and are **not** strictly comparable to the run-006 wild type. The "
      "`wt_ref` column records this distinction as `in-batch` / "
      "`external-same-template` / `external-diff-template`, so the 10 run-004 rows "
      "borrowing the run-006 WT are flagged differently from the 12 rows of runs 001 and "
      "005 that borrow it across a template change. Trust the external comparison for "
      "run 004; treat it as indicative only for runs 001 and 005.\n")
    A("**6. `min_ipae` and `binder_plddt` do not exist for run 006.** Those two columns "
      "come from the organisers' `refold-score`, which needs an RFD4 design folder; the "
      "enumerated candidates have none, which is why `collect_refold.py` was written "
      "against Boltz-2's own `scores.json` instead. The PAE `.npz` files were not kept and "
      "the `detailed_scores.cbor.gz` cannot be opened (no `cbor2` in either venv, and no "
      "network to add one). So run-006 rows have `min_ipae` and `binder_plddt` empty, and "
      "the complex-average `plddt` column is the only pLDDT comparable across all four "
      "runs. Do not rank across runs on `binder_plddt`.\n")
    A("**7. The interface gate needs an in-batch wild type, and only run 006 has one.** "
      "Runs 001/004/005 were submitted without a `trastuzumab_wt` arm, so "
      "`iface_min_minus_WT_batch` is empty for all 22 of their rows and the primary `group` "
      "label falls back to the run-006 WT with `wt_ref = external`. The "
      "`group_strict_wtref` column refuses that substitution and marks those rows "
      "`NA_no_inbatch_WT` instead, so both readings are on the table. Quote the strict "
      "column if the audience is the submission; quote the primary column for internal "
      "ranking.\n")
    A("**8. Neither `p_high` nor `iface_min` is an affinity measurement.** `p_high` is "
      "capped by the wild type at 0.998, so it cannot express \"better than trastuzumab\" "
      "and is a sieve, not an oracle. `iface_min` is folding confidence: 21 measured "
      "non-binders in the Champloo set score AF3 ipTM ≥ 0.7. The pre-registered PASS "
      "groups are therefore \"worth spending a measurement on\", not \"predicted to bind "
      "better\".\n")
    A("**9. Three of the six mutated positions are measured-intolerant.** G100 (OR 0.436), "
      "G101 (0.404) and D108 (0.221) all lose binding when mutated in the FACS data, and "
      "the enumerated shortlist mutates 4–6 of the six free positions. The design "
      "hypothesis treats all six as free because they make no HER2 contact; the measured "
      "data disagrees. A cheap follow-up that needs no GPU: re-rank the PASS set by how "
      "many intolerant positions it leaves at wild type.\n")
    A("**10. Run 007 is excluded.** `007-mohamed-anchored-diverse-k1` was still running on "
      "the GPU when this table was built (its `run.log` ends at \"Dataset "
      "inference-dataset: 1 examples\", no `manifest.csv`, no `refold_metrics.csv`, no "
      "`boltz2/` output). Re-run this script once it lands; it will pick the run up "
      "automatically only if a `manifest.csv` or `scored-boltz2/refold_metrics.csv` "
      "appears, which means `SOURCES` at the top of the script needs one line added.\n")
    A("**11. `F104` is a marginal anchor.** `interface_residues.csv` puts it in tier C: one "
      "atom contact at 4.5 Å, none at 4.0 Å, 6.2 Å² buried. It is weighted equally with "
      "W99/G103/Y105 in `grip_4of4` here, because that is what `report.py` and the anchored "
      "YAML do, but a `grip_3of4_no_F104` variant of the gate would free a position for "
      "almost no interface cost. Not applied — it would be tuning a pre-registered gate.\n")

    A("## Column notes\n")
    A(md_table(["column", "meaning"],
               [["`candidate_id`", "`<run>:<query_id>`, unique across the table"],
                ["`reject_reason`", "the `rank.py` in-memory reject string "
                 "(`official` / `margin` / `Cys`), identical logic, persisted for the first time"],
                ["`novelty_official`", "`dist ≥ 2 and identity ≤ 70 %`"],
                ["`novelty_margin`", f"`dist ≥ {rank.MIN_DIST} and identity ≤ "
                 f"{rank.MAX_IDENTITY:.0f} %`"],
                ["`grip_4of4`", "all of W99/G103/F104/Y105 kept; `anchors_lost` names the losses"],
                ["`p_high`", "recomputed for every row with `rank.p_high` "
                 "(`facs_model.joblib`); `stored_p_high` is the value already in the source file"],
                ["`iface_min` / `iface_mean`", "min and mean of the chain-B-to-chain-C and "
                 "chain-B-to-chain-D interface ipTM, each averaged over both matrix "
                 "directions — `collect_refold.py`'s recipe"],
                ["`wt_ref`", "which wild-type reference the `group` label used"],
                ["`group_strict_wtref`", "`group` with no external-WT substitution"],
                ["`structure_path`", "best-seed `*_model.cif`; best = highest "
                 "`model_ranking_score`, and there is only ever one seed"],
                ["`n_seeds`", "Boltz-2 seeds found on disk for this candidate (always 1)"]]))
    A("")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    return validation


if __name__ == "__main__":
    sys.exit(main())
