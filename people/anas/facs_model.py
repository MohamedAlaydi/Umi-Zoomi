#!/usr/bin/env python3
"""Train a CDRH3 binding-class model on the FACS screen and test it against SPR.

The FACS screen (524,346 variants, three classes) is the only measured signal that
covers the mutational regime the novelty filter forces us into. The SPR table is the
only signal in nanomolar. They overlap in 37 sequences, so the other ~717 SPR rows
are an external test set measured on a different assay.

  py people/anas/facs_model.py            train, evaluate, write the report
  py people/anas/facs_model.py --quick    1/10 of the FACS rows, for a smoke test

Writes people/anas/facs_model.joblib and prints every number it claims.
"""
import argparse
import csv
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse, stats
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

DATA = Path.home() / "team14" / "data" / "her2-trastuzumab"
OUT = Path.home() / "team14" / "people" / "anas"
WT = "WGGDGFYAMD"
AA = "ACDEFGHIKLMNPQRSTVWY"
AA_IX = {a: i for i, a in enumerate(AA)}
CLASSES = ["low", "medium", "high"]
CONTACT = [0, 4, 5, 6]   # W99 G103 F104 Y105, the residues that touch HER2
LIAB = [3, 8]            # D102 isomerisation, M107 oxidation


def load_facs(quick=False):
    z = zipfile.ZipFile(DATA / "tz_her2_facs_3classes_524346.csv.zip")
    name = [n for n in z.namelist() if not n.startswith("__MACOSX")][0]
    seqs, cls, dist = [], [], []
    with z.open(name) as fh:
        for i, r in enumerate(csv.DictReader(io.TextIOWrapper(fh))):
            if quick and i % 10:
                continue
            c = r["cdrh3"]
            if len(c) != 10 or any(a not in AA_IX for a in c):
                continue
            seqs.append(c)
            cls.append(CLASSES.index(r["binding_class"]))
            dist.append(int(r["edit_distance"]))
    return np.array(seqs), np.array(cls), np.array(dist, dtype=np.int8)


def load_spr():
    rows = list(csv.DictReader(open(DATA / "trastuzumab_her2_spr_all_768.csv")))
    keep = [r for r in rows if len(r["cdrh3"]) == 10 and all(a in AA_IX for a in r["cdrh3"])]
    return pd.DataFrame({
        "cdrh3": [r["cdrh3"] for r in keep],
        "kd_nM": [float(r["kd_nM"]) if r["kd_nM"] else np.nan for r in keep],
        "result": [r["binding_result"] for r in keep],
    })


def ordinal(seqs):
    """10 integer features, one per position: the amino acid at that position."""
    return np.array([[AA_IX[a] for a in s] for s in seqs], dtype=np.int8)


def onehot(seqs):
    """Sparse 200-column one-hot, position x amino acid."""
    n = len(seqs)
    rows = np.repeat(np.arange(n), 10)
    cols = (np.tile(np.arange(10), n) * 20) + ordinal(seqs).ravel()
    return sparse.csr_matrix((np.ones(n * 10, dtype=np.float32), (rows, cols)), shape=(n, 200))


def report_by_distance(y, p_high, dist, label):
    print(f"\n  {label}: high-vs-rest AUC by edit distance")
    print("  dist      n     AUC")
    for d in sorted(set(dist.tolist())):
        m = dist == d
        yy = (y[m] == 2).astype(int)
        if yy.sum() in (0, yy.size) or m.sum() < 200:
            continue
        print(f"  {d:>4} {m.sum():>7}   {roc_auc_score(yy, p_high[m]):.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)

    print("loading the FACS screen")
    seqs, y, dist = load_facs(args.quick)
    print(f"  {len(seqs)} ten-mers, classes {dict(zip(CLASSES, np.bincount(y)))}")

    spr = load_spr()
    in_facs = set(seqs.tolist())
    spr["seen_in_facs"] = spr.cdrh3.isin(in_facs)
    print(f"  SPR rows usable: {len(spr)}, of which {int(spr.seen_in_facs.sum())} also in FACS")

    # Hold out sequences, not rows: every CDRH3 here is unique, so a plain split is safe.
    idx = np.arange(len(seqs))
    tr, te = train_test_split(idx, test_size=0.15, random_state=0, stratify=y)

    results = {}
    print("\nfitting multinomial logistic regression on one-hot positions")
    Xoh = onehot(seqs)
    lr = LogisticRegression(max_iter=2000, C=1.0, n_jobs=-1)
    lr.fit(Xoh[tr], y[tr])
    p_lr = lr.predict_proba(Xoh[te])
    results["logreg"] = {
        "accuracy": float((p_lr.argmax(1) == y[te]).mean()),
        "macro_f1": float(f1_score(y[te], p_lr.argmax(1), average="macro")),
        "auc_high": float(roc_auc_score((y[te] == 2).astype(int), p_lr[:, 2])),
    }
    print("  " + json.dumps(results["logreg"]))

    print("\nfitting gradient boosting on positions as categoricals")
    Xo = ordinal(seqs)
    gb = HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.1,
        categorical_features=list(range(10)), random_state=0,
    )
    gb.fit(Xo[tr], y[tr])
    p_gb = gb.predict_proba(Xo[te])
    results["gbm"] = {
        "accuracy": float((p_gb.argmax(1) == y[te]).mean()),
        "macro_f1": float(f1_score(y[te], p_gb.argmax(1), average="macro")),
        "auc_high": float(roc_auc_score((y[te] == 2).astype(int), p_gb[:, 2])),
    }
    print("  " + json.dumps(results["gbm"]))

    best, p_best = ("gbm", p_gb) if results["gbm"]["auc_high"] >= results["logreg"]["auc_high"] else ("logreg", p_lr)
    print(f"\n  better on held-out FACS: {best}")
    report_by_distance(y[te], p_best[:, 2], dist[te], best)

    # ---- external test: SPR, a different assay -------------------------------
    print("\n" + "=" * 62)
    print("EXTERNAL TEST: SPR, measured in nM on a different assay")
    print("=" * 62)
    predict = (lambda s: gb.predict_proba(ordinal(s))) if best == "gbm" else (lambda s: lr.predict_proba(onehot(s)))
    spr["p_high"] = predict(spr.cdrh3.values)[:, 2]

    for subset, frame in [("all SPR", spr), ("SPR unseen in FACS", spr[~spr.seen_in_facs])]:
        fitted = frame.dropna(subset=["kd_nM"])
        binder = frame[frame.result.isin(["quantified_binding", "no_reportable_kd"])]
        yb = (binder.result == "quantified_binding").astype(int)
        rho = stats.spearmanr(fitted.p_high, np.log10(fitted.kd_nM))
        print(f"\n  {subset}: n={len(frame)}, with fitted KD={len(fitted)}")
        print(f"    Spearman p_high vs log10 KD : rho={rho.statistic:+.3f}  p={rho.pvalue:.2e}")
        print("    (negative rho is the good direction: higher p_high, lower KD)")
        if 0 < yb.sum() < len(yb):
            print(f"    AUC quantified-vs-no-fit    : {roc_auc_score(yb, binder.p_high):.3f}  (n={len(yb)})")

    # ---- the wild type, measured eight times --------------------------------
    wt = spr[spr.cdrh3 == WT]
    print(f"\n  wild type {WT}: {len(wt)} replicate measurements")
    print(f"    KD range {wt.kd_nM.min():.4f} to {wt.kd_nM.max():.4f} nM  ({wt.kd_nM.max()/wt.kd_nM.min():.1f}-fold)")
    print(f"    model p_high {wt.p_high.iloc[0]:.3f}")
    print("    A design must beat this spread, not the single 0.152 nM figure.")

    import joblib
    joblib.dump({"model": gb if best == "gbm" else lr, "kind": best, "classes": CLASSES}, OUT / "facs_model.joblib")
    (OUT / "facs_model_metrics.json").write_text(json.dumps(results, indent=2))
    print(f"\nwrote {OUT/'facs_model.joblib'} and facs_model_metrics.json")


if __name__ == "__main__":
    sys.exit(main())
