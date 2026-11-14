"""Compare the same existing FACS classifier recipe across the two published splits."""
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from threadpoolctl import threadpool_limits

from assay_transfer import CLASSES, ROOT, ordinal, sha256


def evaluate(folder, estimator):
    files = {name: folder / (name + ".csv") for name in ["train", "val", "test"]}
    frames = {name: pd.read_csv(file) for name, file in files.items()}
    for col in ["seq", "cluster_centre"]:
        if col not in frames["train"]:
            continue
        sets = [set(frame[col]) for frame in frames.values()]
        if any(a & b for i,a in enumerate(sets) for b in sets[i+1:]):
            raise ValueError(f"Overlapping {col} across splits in {folder}")
    train, test = frames["train"], frames["test"]
    labels = {"low":0, "mid":1, "high":2}
    clf = clone(estimator)
    clf.fit(ordinal(train.seq), train["class"].map(labels).to_numpy())
    pred = clf.predict_proba(ordinal(test.seq))[:,CLASSES.index("high")]
    observed = (test["class"] == "high").to_numpy()
    if not np.array_equal(observed, test.label.to_numpy()):
        raise ValueError("High-class mapping disagrees with source labels")
    bins = []
    for i in range(10):
        m = (pred >= i/10) & ((pred < (i+1)/10) if i < 9 else (pred <= 1))
        if m.any():
            bins.append(dict(lower=i/10,n=int(m.sum()),mean_score=float(pred[m].mean()),
                             fraction_high=float(observed[m].mean())))
    return dict(file_sha256={n:sha256(f) for n,f in files.items()},
                n={s:len(f) for s,f in frames.items()}, test_positive=int(observed.sum()),
                cluster_counts=({s:int(f.cluster_centre.nunique()) for s,f in frames.items()}
                                if "cluster_centre" in train else None),
                auc=roc_auc_score(observed,pred), ap=average_precision_score(observed,pred),
                brier=brier_score_loss(observed,pred), prevalence=float(observed.mean()),
                reliability_bins=bins)


def main():
    source = ROOT / "people/anas/facs_model.joblib"
    bundle = joblib.load(source)
    if bundle["kind"] != "gbm":
        raise ValueError("The saved estimator recipe changed")
    base = ROOT / "data/zenodo-10831512-trastuzumab-ngs/splits/data/affinity_data/her2/her2_aff_large/processed/remove_overlap"
    with threadpool_limits(limits=2):
        result = {kind:evaluate(base/kind/"0.7_0.15_0.15",bundle["model"])
                  for kind in ["random_split", "clonotype_split"]}
    result["recipe_sha256"] = sha256(source)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
