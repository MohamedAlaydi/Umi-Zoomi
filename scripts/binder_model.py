#!/usr/bin/env python3
"""Train a binder classifier on MEASURED HER2 binding, then score our designs.

Why this exists: every other signal we have is a model's confidence in its own
geometry. This one is trained on what was actually measured in a FACS screen of
trastuzumab CDRH3 variants, so it is an independent opinion. It knows nothing
about structure, and structure prediction knows nothing about it, which is the
point of having both.

Data: data/zenodo-10831512-trastuzumab-ngs/splits/.../random_split/
      seq (the 10-residue CDRH3), label (1 = binder), edit_distance from
      trastuzumab. Splits are the organisers', not ours, and overlap is already
      removed.

Usage
  py scripts/binder_model.py                       train, report, score our runs
  py scripts/binder_model.py --curve               also fit the smaller splits
  py scripts/binder_model.py --score WASSSEYYFD …  score sequences you name
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = os.path.expanduser("~/team14")
SPLITS = os.path.join(
    ROOT, "data/zenodo-10831512-trastuzumab-ngs/splits/data/affinity_data/"
    "her2/mason_et_al/processed/remove_overlap/random_split")
MAIN = "0.7_0.15_0.15"
CURVE = ["train70_val15", "train140_val30", "train280_val60", "train560_val120",
         "train1120_val240", "train2240_val480", "train4480_val960"]

AA = "ACDEFGHIKLMNPQRSTVWY"
IDX = {a: i for i, a in enumerate(AA)}

WILD_TYPE = "WGGDGFYAMD"
CONTACT = {99: "W", 103: "G", 104: "F", 105: "Y"}
FIRST = 99


def read(split: str, part: str):
    path = os.path.join(SPLITS, split, f"{part}.csv")
    seqs, labels = [], []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            s = (row.get("seq") or "").strip().upper()
            if not s:
                continue
            seqs.append(s)
            labels.append(int(row["label"]))
    return seqs, np.array(labels)


def encode(seqs):
    """One-hot, 10 positions x 20 amino acids. Simple on purpose: with 24k rows
    and a fixed length, anything fancier mostly buys variance."""
    n = len(seqs)
    L = len(seqs[0])
    X = np.zeros((n, L * len(AA)), dtype=np.float32)
    for i, s in enumerate(seqs):
        for p, a in enumerate(s):
            j = IDX.get(a)
            if j is not None:
                X[i, p * len(AA) + j] = 1.0
    return X


def fit(split=MAIN, quiet=False):
    tr_s, tr_y = read(split, "train")
    va_s, va_y = read(split, "val")
    te_s, te_y = read(split, "test")
    Xtr, Xva, Xte = encode(tr_s), encode(va_s), encode(te_s)

    models = {
        "logistic": LogisticRegression(max_iter=2000, C=1.0),
        "boosted": HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.1, random_state=0),
    }
    scored = {}
    for name, m in models.items():
        m.fit(Xtr, tr_y)
        va = roc_auc_score(va_y, m.predict_proba(Xva)[:, 1])
        te = roc_auc_score(te_y, m.predict_proba(Xte)[:, 1])
        ap = average_precision_score(te_y, m.predict_proba(Xte)[:, 1])
        scored[name] = (m, va, te, ap)
        if not quiet:
            print(f"  {name:<10} val AUC {va:.3f}   test AUC {te:.3f}   "
                  f"test AP {ap:.3f}")

    best = max(scored, key=lambda k: scored[k][1])
    if not quiet:
        print(f"  picked {best} on validation, {len(tr_s):,} training rows, "
              f"{100*tr_y.mean():.0f}% binders")
    return scored[best][0], scored[best][2]


def curve():
    print("\nlearning curve, test AUC by training size")
    print(f"  {'split':<20} {'rows':>7}  test AUC")
    for split in CURVE + [MAIN]:
        try:
            tr_s, _ = read(split, "train")
            _, te = fit(split, quiet=True)
            print(f"  {split:<20} {len(tr_s):>7,}  {te:.3f}")
        except FileNotFoundError:
            print(f"  {split:<20} missing")


def cdrh3_note(cdr: str) -> str:
    if len(cdr) != len(WILD_TYPE):
        return ""
    kept = sum(1 for p, a in CONTACT.items() if cdr[p - FIRST] == a)
    return f"{kept}/4 contacts"


def score(model, seqs, label=""):
    good = [s for s in seqs if len(s) == len(WILD_TYPE)
            and all(c in IDX for c in s)]
    if not good:
        return
    p = model.predict_proba(encode(good))[:, 1]
    order = np.argsort(-p)
    print(f"\npredicted probability of binding{label}")
    print(f"  {'CDRH3':<14} {'P(bind)':>8}  structure check")
    for i in order:
        print(f"  {good[i]:<14} {p[i]:>8.3f}  {cdrh3_note(good[i])}")


def our_designs():
    """Pull every CDRH3 our runs have produced, from the refold metrics."""
    import glob
    seqs = []
    pattern = os.path.join(ROOT, "data/rfd4-proteina/docs/runs/*/scored-*/refold_metrics.csv")
    for path in glob.glob(pattern):
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                s = (row.get("binder_sequence") or "").strip()
                if len(s) >= 108:
                    seqs.append(s[98:108])
    return sorted(set(seqs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--curve", action="store_true")
    ap.add_argument("--score", nargs="*", default=None)
    a = ap.parse_args()

    if not os.path.isdir(SPLITS):
        sys.exit(f"splits not found at {SPLITS}")

    print(f"training on measured FACS binding, split {MAIN}")
    model, test_auc = fit()

    print(f"\nsanity: trastuzumab itself")
    score(model, [WILD_TYPE], " (wild type)")

    if a.score:
        score(model, [s.strip().upper() for s in a.score], " (you asked for these)")
    else:
        ours = our_designs()
        if ours:
            score(model, ours, f" ({len(ours)} designs from our runs)")
        else:
            print("\nno designs found yet in runs/*/scored-*/refold_metrics.csv")

    if a.curve:
        curve()

    print("\nThis is a prediction from measured data, not a measurement. "
          "Use it as a second opinion alongside the structure scores, "
          "never on its own.")


if __name__ == "__main__":
    main()
