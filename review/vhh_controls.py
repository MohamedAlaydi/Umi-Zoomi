"""Compare the three supplied ipTM matrices on the same PDB-ID pairs."""
import json
from zipfile import ZipFile

import pandas as pd
from sklearn.metrics import roc_auc_score

from assay_transfer import ROOT, sha256


def main():
    src = ROOT / "data/zenodo-18390239-ab-ag-complexes/iptm_confidence_scores.zip"
    spr = ROOT / "data/spr-supplementary/spr_table_s1_pairwise.csv"
    scores = {}
    with ZipFile(src) as archive:
        for model in ["boltz2","chai1","af3"]:
            with archive.open(f"iptm_confidence_scores/{model}_matrix_clean.csv") as handle:
                matrix = pd.read_csv(handle,index_col=0)
            if matrix.index.has_duplicates or matrix.columns.has_duplicates:
                raise ValueError(f"Ambiguous matrix IDs in {model}")
            matrix.columns.name = "antigen"
            matrix.index.name = "vhh"
            scores[model] = matrix.stack()
    pairs = pd.DataFrame(scores)
    complete = pairs.dropna().copy()
    cognate = complete.index.get_level_values("vhh") == complete.index.get_level_values("antigen")
    table = {}
    for model in scores:
        off = complete[model][~cognate]
        on = complete[model][cognate]
        table[model] = dict(nonmissing=int(pairs[model].notna().sum()),
                            same_pair_auc=roc_auc_score(cognate, complete[model]),
                            shuffled_ge_070=int((off >= .7).sum()),
                            cognate_ge_070=int((on >= .7).sum()))
    measured = pd.read_csv(spr)
    report = dict(inputs={p.name:sha256(p) for p in [src,spr]},
                  paired_coverage=len(complete), cognate=int(cognate.sum()),
                  shuffled=int((~cognate).sum()), models=table,
                  off_diagonal_rank_correlations=complete[~cognate].corr(method="spearman").to_dict(),
                  measured_outcomes=measured.outcome_class.value_counts().to_dict(),
                  examples=measured[measured.af3_iptm.notna()][["antigen_name","vhh_design","pair_type",
                                      "outcome_class","kd_nM","af3_iptm"]].astype(object))
    report["examples"] = report["examples"].where(pd.notna(report["examples"]),None).to_dict("records")
    print(json.dumps(report,indent=2,allow_nan=False))


if __name__ == "__main__":
    main()
