"""Test the team's later ranker and nearest FACS-high comparator on the same SPR cohort."""
import json
import sys
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from scipy.stats import binomtest

from assay_transfer import CLASSES, ROOT, SCORES, SEED, WT, blosum_scores, comparison, onehot, ordinal, sha256, spr_population
from structure_checks import rows, unique_rows


def nearest_high(loops, high):
    distances = []
    for query in ordinal(loops):
        mismatches = (high != query).sum(axis=1,dtype=np.int8)
        distances.append(int(mismatches.min()))
    return distances


def distance_outcomes(sample):
    groups = {}
    for distance, frame in sample.groupby(-sample.minus_nearest_FACS_high):
        outcomes = frame.outcome.value_counts().to_dict()
        fitted = outcomes.get("quantified_binding",0)
        known = fitted + outcomes.get("no_reportable_kd",0)
        result = dict(outcomes=outcomes,assessable=known)
        if known:
            interval = binomtest(fitted,known).proportion_ci(confidence_level=.95,method="wilson")
            result.update(fitted_fraction=fitted/known,descriptive_wilson_ci95=[interval.low,interval.high])
        groups[str(int(distance))] = result
    return groups


def team_seed_snapshot(folder):
    data = pd.read_csv(folder/"multiseed_metrics.csv")
    summary = pd.read_csv(folder/"multiseed_summary.csv")
    calibration = pd.read_csv(folder/"calibration.csv")
    candidates = data[data["set"] == "candidate"]
    if candidates.duplicated(["query_id","seed"]).any():
        raise ValueError("Duplicate sequence-seed pair")
    grouped = candidates.groupby("query_id").iface_min
    by_seq = grouped.agg(["size","var"])
    multiple = by_seq[by_seq["size"]>=2]
    pooled = np.sqrt(((multiple["size"]-1)*multiple["var"]).sum()/(multiple["size"]-1).sum())
    counts = dict(Counter(int(x) for x in by_seq["size"]))
    if Counter(summary.n_seeds)!=counts:
        raise ValueError("Seed summary disagrees with individual records")
    return dict(n_queries=len(by_seq),n_records=len(candidates),coverage=counts,
                repeated=len(multiple),within_sequence_sd=float(pooled),
                calibration_with_at_least_one_seed=int((calibration.n_seeds>0).sum()),
                calibration_planned=len(calibration),wt_seeds=sorted(candidates.loc[candidates.query_id=="trastuzumab_wt","seed"].tolist()))


def main():
    base = ROOT/"data/her2-trastuzumab"
    archive, spr = base/"tz_her2_facs_3classes_524346.csv.zip", base/"trastuzumab_her2_spr_all_768.csv"
    team = ROOT/"people/anas"
    gb_path, lr_path, rank_path = team/"facs_model.joblib",team/"facs_model_logreg.joblib",team/"final-20.csv"
    with ZipFile(archive) as z:
        member, = [n for n in z.namelist() if n.endswith(".csv") and "__MACOSX" not in n]
        with z.open(member) as handle:
            facs = pd.read_csv(handle,usecols=["cdrh3","binding_class"])
    high = ordinal(facs.loc[facs.binding_class=="high","cdrh3"])
    sample, counts = spr_population(pd.read_csv(spr),set(facs.cdrh3))
    gb, lr = joblib.load(gb_path),joblib.load(lr_path)
    if gb["classes"] != CLASSES or lr["classes"] != CLASSES or lr["kind"] != "logreg":
        raise ValueError("Unexpected model classes or recipe")
    def score(loops):
        with threadpool_limits(limits=2):
            pg = gb["model"].predict_proba(ordinal(loops))[:,2]
            pl = lr["model"].predict_proba(onehot(loops))[:,2]
        return dict(facs=pg,logistic=pl,model_mean=(pg+pl)/2,blosum62=blosum_scores(loops),
                    identity=[sum(a==b for a,b in zip(s,WT)) for s in loops],
                    minus_nearest_FACS_high=[-d for d in nearest_high(loops,high)])
    sample = sample.assign(**score(sample.cdrh3))
    sample["distance"] = len(WT)-sample.identity
    metrics = SCORES + ["logistic","model_mean","minus_nearest_FACS_high"]
    rng = np.random.default_rng(SEED)
    out = dict(all=comparison(sample,2000,rng,metrics),
               distance_4_to_6=comparison(sample[sample.distance.between(4,6)],2000,rng,metrics),
               all_by_high_distance=distance_outcomes(sample),
               four_to_six_by_high_distance=distance_outcomes(sample[sample.distance.between(4,6)]))
    batch = json.loads(Path(sys.argv[1]).read_text())["batch"]
    candidates = [r for r in batch if r["source"] != "control"]
    scores = score([r["cdrh3"] for r in candidates])
    mapped = {r["query"]:{k:float(v[i]) for k,v in scores.items()} for i,r in enumerate(candidates)}
    proposal = unique_rows(rows(rank_path),"query_id")
    for name,entry in proposal.items():
        if not np.isclose(mapped[name]["model_mean"],float(entry["p_mean"]),atol=1e-8,rtol=0):
            raise ValueError("Published ranking disagrees with the frozen models")
    panel = rows(Path(sys.argv[2]))
    seeds, = (ROOT/"runs").glob("009-*")
    original_files = [archive,spr,gb_path,lr_path,rank_path]+[seeds/f for f in
                       ["multiseed_metrics.csv","multiseed_summary.csv","calibration.csv"]]
    out.update(inputs={str(f.relative_to(ROOT)):sha256(f) for f in original_files},
               unique_FACS_high=len(high),n_unique_spr=counts["unique_variants"],
               candidate_high_distance_counts=dict(Counter(int(-v) for v in scores["minus_nearest_FACS_high"])),
               team_top4=list(proposal)[:4],review_top4=[r["query"] for r in panel[:4]],
               overlap_top4=len(set(list(proposal)[:4]) & {r["query"] for r in panel[:4]}),
               overlap_top20=len(set(proposal)&{r["query"] for r in panel}),team_seed_summary=team_seed_snapshot(seeds))
    print(json.dumps(out,indent=2,allow_nan=False))


if __name__ == "__main__":
    main()
