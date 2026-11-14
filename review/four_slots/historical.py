"""Compare four-slot selections on repeated draws from the historical SPR panel."""
import json
from pathlib import Path
import sys
from zipfile import ZipFile

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assay_transfer import ROOT, WT, FITTED, NO_FIT, blosum_scores, ordinal, sha256, spr_population


def main():
    data = ROOT / "data/her2-trastuzumab"
    spr = data / "trastuzumab_her2_spr_all_768.csv"
    facs = data / "tz_her2_facs_3classes_524346.csv.zip"
    model = ROOT / "people/anas/facs_model.joblib"
    with ZipFile(facs) as archive:
        member, = [n for n in archive.namelist() if n.endswith(".csv") and "__MACOSX" not in n]
        with archive.open(member) as h:
            seen = set(pd.read_csv(h, usecols=["cdrh3"]).cdrh3)
    frame, _ = spr_population(pd.read_csv(spr), seen)
    distance = frame.cdrh3.map(lambda loop: sum(a != b for a,b in zip(WT,loop)))
    frame = frame[distance.between(4,6)].reset_index(drop=True)
    with threadpool_limits(2):
        scores = {"BLOSUM62":np.asarray(blosum_scores(frame.cdrh3)),
                  "high_FACS":joblib.load(model)["model"].predict_proba(ordinal(frame.cdrh3))[:,2]}
    # Draw the pool and break exact score ties before looking at any SPR outcomes.
    rng = np.random.default_rng(14112026)
    pools = np.stack([rng.choice(len(frame),40,replace=False) for _ in range(5000)])
    orders = {"random":pools[:,:4]}
    for key, score in scores.items():
        best = np.argsort(-score[pools],axis=1,kind="stable")[:,:4]
        orders[key] = np.take_along_axis(pools,best,axis=1)
    is_fit = (frame.outcome == FITTED).to_numpy()
    is_unknown = (~frame.outcome.isin([FITTED,NO_FIT])).to_numpy()
    result = dict(seed=14112026, draws=5000, pool_size=40, slots=4, unique_historical=len(frame),
                  population_outcomes=frame.outcome.value_counts().to_dict(),
                  input_sha256={str(f.relative_to(ROOT)):sha256(f) for f in [spr,facs,model]}, methods={})
    for key,selected in orders.items():
        fits = is_fit[selected].sum(axis=1)
        unknown = is_unknown[selected].sum(axis=1)
        result["methods"][key] = dict(mean_fits=float(fits.mean()),mean_unassessed=float(unknown.mean()),
                                      mean_no_fit=float((4-fits-unknown).mean()))
    print(json.dumps(result,indent=2))

if __name__ == "__main__":
    main()
