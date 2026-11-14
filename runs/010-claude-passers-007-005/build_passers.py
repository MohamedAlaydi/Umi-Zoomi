#!/usr/bin/env python3
"""Refold batch for the generated passers of runs 007 and 005.

Why: runs 005 and 007 refolded only the best 10 or 12 designs by design score. Novelty
was never part of that choice, so most designs that pass the published novelty rule never
got a structure score, and the ones that did were folded against their own run's template,
so their numbers cannot sit next to the enumerated candidates.

This batch folds EVERY generated design that is IDEAL (4/4 contacts kept, D102 and M107
both changed), has no cysteine, and passes the published novelty rule (min distance >= 2 from all provided
CDRH3, identity to trastuzumab <= 70 %), under the same protocol as people/anas/build_refold.py
and runs 006 and 009: the run-004 template, chains A, C and D as in that run, Boltz-2,
seed 42, one diffusion sample. trastuzumab_wt and the three run-004 controls ride in the
same batch.

  python build_passers.py --run-dir ~/team14/runs/010-claude-passers-007-005
"""
from __future__ import annotations
import argparse, csv, glob, json, os, re, shutil, sys

HOME = os.path.expanduser("~/team14")
sys.path.insert(0, os.path.join(HOME, "scripts"))
sys.path.insert(0, os.path.join(HOME, "people", "anas"))
import novelty   # noqa: E402
import report    # noqa: E402
import build_refold as br   # noqa: E402

RUNS = [("007", "007-mohamed-anchored-diverse-k1"), ("005", "005-mohamed-anchored-n40")]
CONTROLS = [("trastuzumab_wt", br.WT), ("r004_cdrh3_4", "YWSLHYYAMD"),
            ("r004_cdrh3_3", "WASSSEYYFD"), ("r004_cdrh3_31", "WHSSYDYYFD")]


def heavy_cdrh3(path):
    txt = open(path).read()
    m = re.search(r";(EVQL[A-Z\s]+?)\n;", txt)
    if not m:
        raise SystemExit("no heavy chain in " + path)
    seq = re.sub(r"\s+", "", m.group(1))
    if len(seq) != 120 or seq[:98] + seq[108:] != br.VH_PRE + br.VH_POST:
        raise SystemExit("unexpected framework in " + path)
    return seq[98:108]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    run = os.path.expanduser(args.run_dir).rstrip("/")
    rel = "runs/" + os.path.basename(run)
    pool = novelty.load()

    cands, seen, skipped_cys = [], {}, []
    for tag, name in RUNS:
        base = os.path.join(br.DOCS, "runs", name)
        refolded = {r["query_id"] for r in csv.DictReader(open(base + "/prepared/selection.csv"))}
        paths = glob.glob(base + "/design/generation/inference_samples/*/*_generated.cif")
        paths.sort(key=lambda q: int(os.path.basename(os.path.dirname(q)).rsplit("_", 1)[1]))
        for p in paths:
            design = os.path.basename(os.path.dirname(p))
            idx = int(design.rsplit("_", 1)[1])
            cdr = heavy_cdrh3(p)
            dist, nearest = novelty.min_distance(cdr, pool)
            idt = novelty.identity_to_trastuzumab(cdr)
            verdict = report.hypothesis(cdr)[0]
            if "C" in cdr and dist >= 2 and idt <= 70.0 and verdict == "IDEAL":
                skipped_cys.append(f"{tag}:{design}:{cdr}")
            if "C" in cdr or not (dist >= 2 and idt <= 70.0 and verdict == "IDEAL"):
                continue
            if cdr in seen:
                seen[cdr]["also"] += f"{tag}:{design};"
                continue
            row = {"query_id": f"r{tag}_a{idx:02d}", "run": tag, "design": design, "cdrh3": cdr,
                   "min_dist": dist, "identity": round(idt),
                   "had_fold_before": design in refolded, "also": ""}
            seen[cdr] = row
            cands.append(row)

    chain_c, chain_d = br.load_chains_from(br.REF_RUN)
    holo = os.path.join(br.DOCS, rel, "prepared", "holo")
    os.makedirs(holo, exist_ok=True)
    shutil.copy(os.path.join(br.REF_RUN, "template.cif"), os.path.join(holo, "template.cif"))

    queries = [(c["query_id"], c["cdrh3"]) for c in cands] + CONTROLS
    out = {"queries": []}
    for qid, cdr in queries:
        out["queries"].append({"query_id": qid, "chains": [
            {"chain_id": "A", "sequence": br.VL, "msa_path": None},
            {"chain_id": "B", "sequence": br.VH_PRE + cdr + br.VH_POST, "msa_path": None},
            chain_c, chain_d]})
    json.dump(out, open(os.path.join(holo, "queries.json"), "w"))

    with open(os.path.join(run, "manifest.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["query_id", "cdrh3", "p_high", "n_mut", "source"])
        w.writeheader()
        for c in cands:
            src = f"gen{c['run']}-" + ("had-fold" if c["had_fold_before"] else "new")
            w.writerow({"query_id": c["query_id"], "cdrh3": c["cdrh3"], "p_high": "",
                        "n_mut": sum(a != b for a, b in zip(c["cdrh3"], br.WT)), "source": src})
        for qid, cdr in CONTROLS:
            w.writerow({"query_id": qid, "cdrh3": cdr, "p_high": "",
                        "n_mut": sum(a != b for a, b in zip(cdr, br.WT)), "source": "control"})
    with open(os.path.join(run, "candidates.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["query_id", "run", "design", "cdrh3", "min_dist",
                                           "identity", "had_fold_before", "also"])
        w.writeheader()
        w.writerows(cands)

    new = sum(1 for c in cands if not c["had_fold_before"])
    print(f"{len(cands)} generated passers ({new} never folded, {len(cands) - new} folded before "
          f"under another template) + {len(CONTROLS)} controls = {len(queries)} queries")
    for c in cands:
        print(f"  {c['query_id']:<10} {c['cdrh3']}  dist {c['min_dist']}  id {c['identity']:>3}%  "
              f"{'had fold' if c['had_fold_before'] else 'NEW':<8} {c['also']}")
    print(f"  skipped, unpaired cysteine (hard filter): {skipped_cys}")
    print(f"  run dir   {run}")
    print(f"  queries   {holo}/queries.json")
    print(f"REL={rel}")


if __name__ == "__main__":
    main()
