#!/usr/bin/env python3
"""Do the dumb rules still win inside the regime we are forced to design in?

score_final.py found that two one-line rules beat the FACS model on the SPR external
set: -mutation count (AUC 0.815) and -distance to the nearest FACS high binder (0.857)
against the model's 0.764. That is a real result and it has to be reported.

But the SPR set spans 1 to 10 mutations, and in that whole range "stay close to
trastuzumab" is the dominant signal, which is exactly what both rules encode. The
novelty filter forbids us from being close. So the fair question is whether the rules
still separate binders from non-binders among variants that are already >= 4 mutations
away, where every one of our candidates lives.

  py people/anas/fair_compare.py
"""
from __future__ import annotations

import csv
import io
import os
import zipfile

import joblib
import numpy as np
from scipy import sparse
from sklearn.metrics import roc_auc_score

HOME = os.path.expanduser("~/team14")
DATA = os.path.join(HOME, "data/her2-trastuzumab")
ANAS = os.path.join(HOME, "people/anas")
AA = "ACDEFGHIKLMNPQRSTVWY"
AA_IX = {a: i for i, a in enumerate(AA)}
WT = "WGGDGFYAMD"


def ordinal(seqs):
    return np.array([[AA_IX[a] for a in s] for s in seqs], dtype=np.int8)


def onehot(X):
    n = len(X)
    rows = np.repeat(np.arange(n), 10)
    cols = (np.tile(np.arange(10), n) * 20) + X.ravel()
    return sparse.csr_matrix((np.ones(n * 10, dtype=np.float32), (rows, cols)), shape=(n, 200))


def main() -> int:
    z = zipfile.ZipFile(os.path.join(DATA, "tz_her2_facs_3classes_524346.csv.zip"))
    name = [n for n in z.namelist() if not n.startswith("__MACOSX")][0]
    seqs, cls = [], []
    with z.open(name) as fh:
        for r in csv.DictReader(io.TextIOWrapper(fh)):
            c = r["cdrh3"]
            if len(c) == 10 and all(a in AA_IX for a in c):
                seqs.append(c)
                cls.append(r["binding_class"])
    seqs = np.array(seqs)
    cls = np.array(cls)
    high = ordinal(seqs[cls == "high"].tolist())
    in_facs = set(seqs.tolist())
    print(f"FACS high binders: {len(high):,}")

    spr = [r for r in csv.DictReader(open(os.path.join(DATA, "trastuzumab_her2_spr_all_768.csv")))
           if len(r["cdrh3"]) == 10 and all(a in AA_IX for a in r["cdrh3"])
           and r["cdrh3"] not in in_facs
           and r["binding_result"] in ("quantified_binding", "no_reportable_kd")]
    es = [r["cdrh3"] for r in spr]
    lab = np.array([r["binding_result"] == "quantified_binding" for r in spr], dtype=int)
    X = ordinal(es)

    gb = joblib.load(os.path.join(ANAS, "facs_model.joblib"))["model"]
    lr = joblib.load(os.path.join(ANAS, "facs_model_logreg.joblib"))["model"]
    p_gb = gb.predict_proba(X)[:, 2]
    p_lr = lr.predict_proba(onehot(X))[:, 2]
    n_mut = (X != ordinal([WT])[0]).sum(1)
    # distance to the nearest FACS high binder, in blocks to keep memory sane
    nn = np.empty(len(X), dtype=np.int16)
    for i in range(0, len(X), 64):
        blk = X[i:i + 64]
        d = (blk[:, None, :] != high[None, :, :]).sum(2)
        nn[i:i + 64] = d.min(1)

    scores = {
        "p_high gbm": p_gb,
        "p_high logreg": p_lr,
        "p_high mean": (p_gb + p_lr) / 2,
        "-mutation count": -n_mut.astype(float),
        "-nearest FACS high": -nn.astype(float),
    }

    for lo, label in [(0, "all mutational distances"), (4, "only >= 4 mutations, our regime"),
                      (5, "only >= 5 mutations")]:
        m = n_mut >= lo
        yy = lab[m]
        if yy.sum() in (0, yy.size):
            continue
        print(f"\n{label}: n={m.sum()}, {yy.sum()} binders, {len(yy)-yy.sum()} no fit")
        for k, v in scores.items():
            print(f"   AUC {roc_auc_score(yy, v[m]):.3f}   {k}")

    print("\ndistribution of nearest-FACS-high distance among SPR rows")
    for d in range(0, 8):
        m = nn == d
        if m.sum():
            print(f"   d={d}: n={m.sum():>4}  binder rate {lab[m].mean():.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
