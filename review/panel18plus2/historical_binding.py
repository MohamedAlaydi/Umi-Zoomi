"""Re-run the existing four-slot selection and count historical KD below three WT values."""
from pathlib import Path
from zipfile import ZipFile
import argparse
import json
import sys

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits


def evaluate(root):
    sys.path.insert(0, str(root / 'review'))
    from assay_transfer import WT, FITTED, NO_FIT, blosum_scores, ordinal, spr_population, sha256
    files = [root / 'data/her2-trastuzumab' / name for name in
             ('trastuzumab_her2_spr_all_768.csv', 'tz_her2_facs_3classes_524346.csv.zip')]
    spr, facs = files
    model = root / 'people/anas/facs_model.joblib'
    with ZipFile(facs) as archive:
        member, = [n for n in archive.namelist() if n.endswith('.csv') and '__MACOSX' not in n]
        with archive.open(member) as h:
            seen = set(pd.read_csv(h, usecols=['cdrh3']).cdrh3)
    frame, counts = spr_population(pd.read_csv(spr), seen)
    mutations = frame.cdrh3.map(lambda s: sum(a != b for a, b in zip(WT, s, strict=True)))
    frame = frame[mutations.between(4, 6)].reset_index(drop=True)
    with threadpool_limits(2):
        scores = {'BLOSUM62': np.array(blosum_scores(frame.cdrh3)),
                  'high_FACS': joblib.load(model)['model'].predict_proba(ordinal(frame.cdrh3))[:, 2]}
    rng = np.random.default_rng(14112026)
    pools = np.stack([rng.choice(len(frame), 40, replace=False) for _ in range(5000)])
    picks = {'random': pools[:, :4]}
    for k, score in scores.items():
        order = np.argsort(-score[pools], axis=1, kind='stable')[:, :4]
        picks[k] = np.take_along_axis(pools, order, axis=1)
    kd = frame.kd.to_numpy()
    fits = (frame.outcome == FITTED).to_numpy()
    unknown = (~frame.outcome.isin([FITTED, NO_FIT])).to_numpy()
    wt = counts['wt_values_nM']
    thresholds = {'lowest_observation': min(wt), 'median_observation': float(np.median(wt)), 'highest_observation': max(wt)}
    previous = json.loads((root / 'review/four_slots/historical.json').read_text())
    methods = {}
    for name, selected in picks.items():
        fits_per_four = float(fits[selected].sum(axis=1).mean())
        assert abs(fits_per_four - previous['methods'][name]['mean_fits']) < 1e-10
        methods[name] = {'fits_per_four': fits_per_four,
                         'unknown_per_four': float(unknown[selected].sum(axis=1).mean()),
                         'observed_below_threshold_per_four': {k: float((kd[selected] < limit).sum(axis=1).mean())
                                                              for k, limit in thresholds.items()}}
    return {'unique_constructs': len(frame), 'draws': 5000, 'slots': 4, 'seed': 14112026,
            'wt_observations_nM': wt, 'thresholds_nM': thresholds,
            'quantified_constructs': int(fits.sum()), 'lowest_quantified_kd_nM': float(np.nanmin(kd)),
            'inconclusive_or_unreported': int(unknown.sum()), 'no_reportable_kd': int((frame.outcome == NO_FIT).sum()),
            'measured_below_threshold_counts': {k: int((kd < v).sum()) for k, v in thresholds.items()},
            'methods': methods, 'sha256': {str(p.relative_to(root)): sha256(p) for p in [*files, model]},
            'interpretation': 'Historical descriptive threshold sensitivity; neither batch-matched improvement nor a prospective S-tier estimate. Unknown outcomes are not counted as observed wins.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('team_root', type=Path)
    print(json.dumps(evaluate(parser.parse_args().team_root.resolve()), indent=2))
