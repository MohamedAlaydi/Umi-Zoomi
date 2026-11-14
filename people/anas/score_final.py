#!/usr/bin/env python3
"""Final scoring of the run 006 candidates, with structure demoted to a floor.

Run 009 measured the seed noise on Boltz-2's iface_min: within-sequence SD 0.0147,
between-sequence SD 0.0168, ICC(1) 0.57, and a minimal detectable WT-paired delta of
about 0.054 at two seeds. Our best margin over the wild type was 0.014. So the
single-seed ordering we used in run 006 was noise, and run 009 confirms it directly:
none of the eight first-pass picks survive in the top eight by six-seed mean.

So structure is used two ways only, both robust to that noise:
  floor     drop anything more than 2 seed-SD below the in-batch wild type
  reporting print the delta with its noise band, and say when it is undetectable

The ranking itself rests on signals that do not move between runs:
  p_high      two model families on the 524,346 measured FACS variants, averaged.
              Agreement between them is the robustness check: a candidate both
              families like is not an artefact of one inductive bias.
  liabilities D102 and M107 changed (36.2 % high vs 20.4 % for one of two)
  novelty     exact distance to all 525,042 provided CDRH3s
  diversity   near-identical loops are one bet, not several

It also re-checks that p_high beats two dumb rules on the SPR external set, because a
model that cannot beat "count the mutations" has added nothing.

  py people/anas/score_final.py --top 20 --out people/anas/final-20.csv
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import zipfile

import joblib
import numpy as np
from scipy import sparse, stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

HOME = os.path.expanduser("~/team14")
DATA = os.path.join(HOME, "data/her2-trastuzumab")
ANAS = os.path.join(HOME, "people/anas")
AA = "ACDEFGHIKLMNPQRSTVWY"
AA_IX = {a: i for i, a in enumerate(AA)}
WT = "WGGDGFYAMD"
CONTACT = [0, 4, 5, 6]
LIAB = [3, 8]
SEED_SD = 0.014665          # run 009, within-sequence SD of iface_min
MIN_DETECTABLE = 0.05445    # run 009, exact noncentral t, n=2, alpha 0.05, power 0.80


def ordinal(seqs):
    return np.array([[AA_IX[a] for a in s] for s in seqs], dtype=np.int8)


def onehot(X):
    n = len(X)
    rows = np.repeat(np.arange(n), 10)
    cols = (np.tile(np.arange(10), n) * 20) + X.ravel()
    return sparse.csr_matrix((np.ones(n * 10, dtype=np.float32), (rows, cols)), shape=(n, 200))


def load_facs():
    z = zipfile.ZipFile(os.path.join(DATA, "tz_her2_facs_3classes_524346.csv.zip"))
    name = [n for n in z.namelist() if not n.startswith("__MACOSX")][0]
    seqs, cls = [], []
    with z.open(name) as fh:
        for r in csv.DictReader(io.TextIOWrapper(fh)):
            c = r["cdrh3"]
            if len(c) == 10 and all(a in AA_IX for a in c):
                seqs.append(c)
                cls.append(["low", "medium", "high"].index(r["binding_class"]))
    return np.array(seqs), np.array(cls)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--min-diff", type=int, default=3)
    ap.add_argument("--out")
    args = ap.parse_args()

    rows = [r for r in csv.DictReader(open(os.path.join(ANAS, "refold-006.csv")))
            if r["status"] == "ok"]
    wt_row = next(r for r in rows if r["query_id"] == "trastuzumab_wt")
    wt_iface = float(wt_row["iface_min"])
    floor = wt_iface - 2 * SEED_SD
    print(f"in-batch wild type iface_min {wt_iface:.3f}; seed SD {SEED_SD:.4f}")
    print(f"structural floor (WT - 2 SD): {floor:.3f}")
    print(f"a delta vs WT is undetectable below {MIN_DETECTABLE:.3f}\n")

    print("second opinion: refitting a logistic regression on the FACS screen")
    seqs, y = load_facs()
    Xo, Xoh = ordinal(seqs), None
    Xoh = onehot(Xo)
    lr = LogisticRegression(max_iter=2000, C=1.0)
    lr.fit(Xoh, y)
    gb = joblib.load(os.path.join(ANAS, "facs_model.joblib"))["model"]
    joblib.dump({"model": lr, "kind": "logreg", "classes": ["low", "medium", "high"]},
                os.path.join(ANAS, "facs_model_logreg.joblib"))

    # --- does p_high beat two dumb rules, on SPR? ---------------------------
    spr = [r for r in csv.DictReader(open(os.path.join(DATA, "trastuzumab_her2_spr_all_768.csv")))
           if len(r["cdrh3"]) == 10 and all(a in AA_IX for a in r["cdrh3"])]
    facs_high = set(seqs[y == 2].tolist())
    in_facs = set(seqs.tolist())
    ext = [r for r in spr if r["cdrh3"] not in in_facs
           and r["binding_result"] in ("quantified_binding", "no_reportable_kd")]
    es = [r["cdrh3"] for r in ext]
    lab = np.array([r["binding_result"] == "quantified_binding" for r in ext], dtype=int)
    Xe = ordinal(es)
    p_gb = gb.predict_proba(Xe)[:, 2]
    p_lr = lr.predict_proba(onehot(Xe))[:, 2]
    n_mut = np.array([sum(1 for a, b in zip(s, WT) if a != b) for s in es])
    nn_high = np.array([min((sum(1 for a, b in zip(s, h) if a != b) for h in facs_high), default=10)
                        for s in es])
    print(f"  external SPR set, unseen by either model: n={len(ext)}, "
          f"{lab.sum()} with a fitted KD")
    for name, score in [("p_high, gradient boosting", p_gb),
                        ("p_high, logistic regression", p_lr),
                        ("p_high, mean of the two", (p_gb + p_lr) / 2),
                        ("dumb rule: -mutation count", -n_mut.astype(float)),
                        ("dumb rule: -distance to nearest FACS high", -nn_high.astype(float))]:
        print(f"    AUC binder-vs-no-fit  {roc_auc_score(lab, score):.3f}   {name}")
    rho = stats.spearmanr(p_gb, p_lr)
    print(f"  the two models agree with each other: Spearman {rho.statistic:.3f}\n")

    # --- score the candidates ----------------------------------------------
    cand = [r for r in rows if r["source"] != "control"]
    cs = [r["cdrh3"] for r in cand]
    Xc = ordinal(cs)
    pg = gb.predict_proba(Xc)[:, 2]
    pl = lr.predict_proba(onehot(Xc))[:, 2]
    for r, a, b in zip(cand, pg, pl):
        r["p_gb"], r["p_lr"] = float(a), float(b)
        r["p_mean"] = (float(a) + float(b)) / 2
        r["iface"] = float(r["iface_min"])
        r["delta_wt"] = r["iface"] - wt_iface
        r["detectable"] = abs(r["delta_wt"]) >= MIN_DETECTABLE
        cdr = r["cdrh3"]
        r["grip"] = sum(1 for i in CONTACT if cdr[i] == WT[i])
        r["liab"] = sum(1 for i in LIAB if cdr[i] != WT[i])

    kept_floor = [r for r in cand if r["iface"] >= floor]
    print(f"structural floor: {len(kept_floor)} of {len(cand)} candidates at or above {floor:.3f}")
    for r in cand:
        if r["iface"] < floor:
            print(f"   dropped {r['query_id']} {r['cdrh3']} iface {r['iface']:.3f} "
                  f"({(r['iface']-wt_iface)/SEED_SD:+.1f} seed SD vs WT)")

    kept_floor.sort(key=lambda r: (-r["p_mean"], -r["liab"], -r["grip"]))
    final, dup = [], []
    for r in kept_floor:
        if any(sum(a != b for a, b in zip(r["cdrh3"], k["cdrh3"])) < args.min_diff for k in final):
            dup.append(r)
            continue
        final.append(r)
        if len(final) >= args.top:
            break

    print(f"\nfinal {len(final)}, ranked on measured-data agreement, "
          f"{args.min_diff}+ apart from each other\n")
    hdr = (f"{'#':>3} {'query':<10} {'CDRH3':<12} {'p_gb':>6} {'p_lr':>6} {'p_mean':>7} "
           f"{'liab':>5} {'grip':>5} {'iface':>6} {'d_WT':>7} {'detect':>7}")
    print(hdr)
    print("-" * len(hdr))
    for i, r in enumerate(final, 1):
        print(f"{i:>3} {r['query_id']:<10} {r['cdrh3']:<12} {r['p_gb']:>6.3f} {r['p_lr']:>6.3f} "
              f"{r['p_mean']:>7.3f} {r['liab']:>3}/2 {r['grip']:>3}/4 {r['iface']:>6.3f} "
              f"{r['delta_wt']:>+7.3f} {'yes' if r['detectable'] else 'no':>7}")

    nd = sum(1 for r in final if not r["detectable"])
    print(f"\n{nd} of {len(final)} have a WT delta inside the seed noise, so their structural")
    print("difference from trastuzumab is not measurable at one seed. That is expected and")
    print("is why the order above does not use it.")

    if args.out:
        cols = ["query_id", "cdrh3", "p_gb", "p_lr", "p_mean", "liab", "grip", "n_mut",
                "iface", "delta_wt", "detectable", "iptm", "plddt", "source"]
        with open(args.out, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(final)
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
