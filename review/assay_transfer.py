"""Audit the frozen FACS score against measured SPR and two fixed comparators.

Run with the repository's Python environment. All inputs are read-only. Results
go to stdout so the caller can pick a new destination for every reproduction.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from zipfile import ZipFile

import joblib
import numpy as np
import pandas as pd
from biotite.sequence.align import SubstitutionMatrix
from scipy.stats import rankdata
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "people/anas"))
from facs_model import CLASSES, WT, onehot, ordinal

FITTED = "quantified_binding"
NO_FIT = "no_reportable_kd"
SCORES = ["facs", "blosum62", "identity"]
SEED = 14112026


def sha256(path):
    with open(path, "rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def blosum_scores(sequences, parent=WT):
    matrix = SubstitutionMatrix.std_protein_matrix()
    if any(len(s) != len(parent) for s in sequences):
        raise ValueError("Position-wise BLOSUM62 requires equal-length aligned loops")
    return [int(sum(matrix.get_score(a, b) for a, b in zip(s, parent))) for s in sequences]


def spr_population(records, facs_sequences):
    ref = records.iloc[0]
    if ref.cdrh3 != WT or ref.vh_sequence[98:108] != WT or ref.binding_result != FITTED:
        raise ValueError("Unexpected SPR reference row")
    if not set(records.binding_result) <= {FITTED, NO_FIT, "inconclusive", "not_reported"}:
        raise ValueError("Unrecognised SPR outcome")
    if not (records.kd_nM.notna() == (records.binding_result == FITTED)).all():
        raise ValueError("KD and outcome labels disagree")
    if (records.kd_nM.dropna() <= 0).any():
        raise ValueError("KD must be positive")
    frame = records[records.cdrh3.str.len() == len(WT)].copy()
    compatible = ((frame.vl_sequence == ref.vl_sequence)
                  & (frame.vh_sequence == ref.vh_sequence[:98] + frame.cdrh3 + ref.vh_sequence[108:]))
    if not compatible.all():
        raise ValueError("Unexpected antibody background among SPR ten-mers")
    frame = frame[~frame.cdrh3.isin(facs_sequences)]
    wt_rows = frame.loc[frame.cdrh3 == WT, "kd_nM"]
    variants = frame[frame.cdrh3 != WT]
    groups = variants.groupby("cdrh3", sort=True)
    if (groups.binding_result.nunique() != 1).any():
        raise ValueError("Conflicting replicate outcomes require adjudication")
    sample = groups.agg(kd=("kd_nM", "median"), outcome=("binding_result", "first")).reset_index()
    counts = dict(input_rows=len(records), ten_mer_rows=int(compatible.sum()),
                  all_ten_mer_unseen_rows=len(frame), unique_variants=len(sample),
                  raw_outcomes=records.binding_result.value_counts().to_dict(),
                  variant_outcomes=sample.outcome.value_counts().to_dict(),
                  wt_n=len(wt_rows), wt_values_nM=wt_rows.tolist(),
                  wt_median_nM=float(wt_rows.median()), wt_range_ratio=float(wt_rows.max()/wt_rows.min()))
    return sample, counts


def auc_positive_first(scores, n_positive):
    # Each column is a different score for exactly the same constructs.
    ranks = rankdata(scores, axis=0)
    return (ranks[:n_positive].sum(axis=0) - n_positive * (n_positive + 1) / 2) / (
        n_positive * (len(scores) - n_positive))


def comparison(frame, draws, rng, score_names=SCORES):
    cases = frame[frame.outcome == FITTED]
    nonfits = frame[frame.outcome == NO_FIT]
    result = dict(total=len(frame), fitted=len(cases), no_fit=len(nonfits),
                  other=len(frame)-len(cases)-len(nonfits))
    if min(len(cases), len(nonfits)) == 0:
        result["auc_estimable"] = False
        return result
    positive = cases[score_names].to_numpy()
    negative = nonfits[score_names].to_numpy()
    def auc(p, n):
        return auc_positive_first(np.vstack((p, n)), len(p))
    point = auc(positive, negative)
    bootstrap = []
    for _ in range(draws):
        i = rng.integers(len(positive), size=len(positive))
        j = rng.integers(len(negative), size=len(negative))
        bootstrap.append(auc(positive[i], negative[j]))
    boot = np.asarray(bootstrap)
    def estimate(value, replicates):
        return dict(value=float(value), ci95=np.quantile(replicates, [.025, .975]).tolist())
    result["auc"] = {name:estimate(point[i], boot[:, i]) for i, name in enumerate(score_names)}
    result["delta_auc_blosum_minus_facs"] = estimate(point[1]-point[0], boot[:,1]-boot[:,0])
    result["delta_auc_blosum_minus_identity"] = estimate(point[1]-point[2], boot[:,1]-boot[:,2])
    if len(score_names) > 3:
        result["delta_auc_blosum_minus"] = {name:estimate(point[1]-point[i],boot[:,1]-boot[:,i])
                                           for i,name in enumerate(score_names[3:],3)}
    # Rank affinity among quantified constructs only. Negative rho is favorable.
    kd = np.log10(cases.kd.to_numpy())
    def rhos(scores, y):
        ranks = rankdata(scores, axis=0)
        return [np.corrcoef(ranks[:, j], rankdata(y))[0,1] for j in range(scores.shape[1])]
    if len(cases) >= 10 and len(np.unique(kd)) > 1:
        rho = rhos(positive, kd)
        samples = []
        for _ in range(draws):
            i = rng.integers(len(kd), size=len(kd))
            samples.append(rhos(positive[i], kd[i]))
        arr = np.array(samples)
        result["rho_log_kd"] = {name:estimate(rho[i], arr[:,i]) for i,name in enumerate(score_names)}
    # Conditional concordance weights each positive/no-fit pair with the same
    # mutation count equally. These pairs share constructs and are dependent.
    frame = frame[frame.outcome.isin([FITTED, NO_FIT])]
    weighted = np.zeros(len(score_names))
    pairs = 0
    for _, group in frame.groupby("distance"):
        p = group[group.outcome == FITTED][score_names].to_numpy()
        n = group[group.outcome == NO_FIT][score_names].to_numpy()
        count = len(p) * len(n)
        if count:
            weighted += auc(p,n) * count
            pairs += count
    result["matched_pairs"] = pairs
    result["same_distance_auc"] = dict(zip(score_names, (weighted/pairs).tolist())) if pairs else {}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", type=int, default=2000)
    args = parser.parse_args()
    if args.bootstrap < 2:
        parser.error("Need at least two bootstrap samples")
    data = ROOT / "data/her2-trastuzumab"
    spr = data / "trastuzumab_her2_spr_all_768.csv"
    archive = data / "tz_her2_facs_3classes_524346.csv.zip"
    model = ROOT / "people/anas/facs_model.joblib"
    with ZipFile(archive) as z:
        member, = [n for n in z.namelist() if n.endswith(".csv") and "__MACOSX" not in n]
        with z.open(member) as handle:
            facs_sequences = set(pd.read_csv(handle, usecols=["cdrh3"]).cdrh3)
    sample, counts = spr_population(pd.read_csv(spr), facs_sequences)
    # This is the pre-existing model artifact from the team repository.
    bundle = joblib.load(model)
    if bundle["classes"] != CLASSES or bundle["kind"] not in {"gbm", "logreg"}:
        raise ValueError("Unrecognised classifier or classes")
    x = ordinal(sample.cdrh3) if bundle["kind"] == "gbm" else onehot(sample.cdrh3)
    with threadpool_limits(limits=2):
        sample["facs"] = bundle["model"].predict_proba(x)[:, CLASSES.index("high")]
    sample["blosum62"] = blosum_scores(sample.cdrh3)
    sample["identity"] = sample.cdrh3.map(lambda s: sum(a == b for a,b in zip(s, WT)))
    sample["distance"] = len(WT) - sample.identity
    anchored = sample.cdrh3.map(lambda s: all(s[i] == WT[i] for i in [0,4,5,6]))
    changes = sample.cdrh3.map(lambda s: all(s[i] != WT[i] for i in [3,8]))
    same_regime = anchored & changes & ~sample.cdrh3.str.contains("C") & sample.distance.between(4,6)
    rng = np.random.default_rng(SEED)
    report = dict(inputs={str(p.relative_to(ROOT)):sha256(p) for p in (spr, archive, model)},
                  model=bundle["kind"], n_facs=len(facs_sequences), counts=counts,
                  bootstrap=dict(draws=args.bootstrap, seed=SEED, unit="unique construct"),
                  all_variants=comparison(sample, args.bootstrap, rng),
                  distance_4_to_6=comparison(sample[sample.distance.between(4,6)], args.bootstrap, rng),
                  panel_sequence_constraints=comparison(sample[same_regime], args.bootstrap, rng))
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
