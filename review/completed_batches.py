"""Audit the completed run 008 index and the first matched batches in 009/010."""
import json
from collections import Counter

from assay_transfer import ROOT, sha256
from structure_checks import pair_scores, rows, unique_rows


def read_json(path):
    return json.loads(path.read_text())


def matched_batch(folder, query_path, out, reference_folder, reference):
    template = folder/"out/prepared/holo/template.cif"
    reference_out = reference_folder/"out/boltz2"
    if sha256(template) != sha256(reference_folder/"out/prepared/holo/template.cif"):
        raise ValueError("Different templates")
    cfg = read_json(out/"config.json")
    if cfg != read_json(reference_out/"config.json"):
        raise ValueError("Unmatched run configuration")
    queries = unique_rows(read_json(query_path)["queries"], "query_id")
    inputs_006 = unique_rows(read_json(reference_folder/"out/prepared/holo/queries.json")["queries"], "query_id")
    predictions = unique_rows(read_json(out/"result.json")["result"]["predictions"], "query_id")
    if set(queries) != set(predictions):
        raise ValueError("Incomplete result")
    metrics, common = {}, {}
    for name, pred in predictions.items():
        if (pred["seed"], pred["sample"]) != (42, 1):
            raise ValueError("Unexpected seed or sample")
        order = [c["chain_id"] for c in queries[name]["chains"]]
        if order != ["A","B","C","D"]:
            raise ValueError("Unexpected chain order")
        scores_path = out/pred["scores_path"]
        scores = read_json(scores_path)
        metrics[name] = dict(scores_sha256=sha256(scores_path),
                             VH_min=pair_scores(scores["chain_chain_interface_predicted_tm_score"],order)["VH_min"])
        if name in reference:
            if queries[name]["chains"] != inputs_006[name]["chains"]:
                raise ValueError("Shared names refer to different complex inputs")
            obj = reference[name]
            score_006 = read_json(reference_out/obj["scores_path"])
            common[name] = dict(same_coordinates=sha256(out/pred["path"]) == sha256(reference_out/obj["path"]),
                                same_pair_matrix=scores["chain_chain_interface_predicted_tm_score"] ==
                                                 score_006["chain_chain_interface_predicted_tm_score"])
    return dict(n=len(predictions),common_with_006=common,metrics=metrics,
                inputs={str(p.relative_to(ROOT)):sha256(p) for p in
                        [template,query_path,out/"config.json",out/"result.json"]})


def main():
    run_dir = ROOT/"runs"
    r6, = run_dir.glob("006-*")
    r8, = run_dir.glob("008-*")
    r9, = run_dir.glob("009-*")
    r10, = run_dir.glob("010-*")
    first_file = r8/"first_pass_candidates.csv"
    first = rows(first_file)
    report = {"008":dict(n=len(first), unique_loops=len({row["cdrh3"] for row in first}),
                         columns=len(first[0]),structural_rows=sum(r["has_structure"]=="TRUE" for r in first),
                         by_run=dict(Counter(r["run"] for r in first)),file_sha256=sha256(first_file))}
    ref = unique_rows(read_json(r6/"out/boltz2/result.json")["result"]["predictions"],"query_id")
    report["009_seed42"] = matched_batch(r9,r9/"out/prepared/holo/queries_cand42.json",
                                         r9/"out/boltz2-cand-s42",r6,ref)
    candidate_manifest, calibration_manifest = (r9/"manifest_candidates.csv", r9/"manifest_calibration.csv")
    calibration = rows(calibration_manifest)
    report["009_plan"] = dict(candidate_queries=len(rows(candidate_manifest)),calibration_queries=len(calibration),
                              calibration_strata=dict(Counter(r["stratum"] for r in calibration)),
                              manifests={p.name:sha256(p) for p in [candidate_manifest,calibration_manifest]})
    latest = matched_batch(r10,r10/"out/prepared/holo/queries.json",r10/"out/boltz2",r6,ref)
    candidates = unique_rows(rows(r10/"candidates.csv"),"query_id")
    if set(candidates) != set(latest["metrics"])-set(latest["common_with_006"]):
        raise ValueError("Unexpected run 010 comparator membership")
    wt = latest["metrics"]["trastuzumab_wt"]["VH_min"]
    latest.update(new_or_refolded=len(candidates), distances_reported=dict(Counter(int(r["min_dist"]) for r in candidates.values())),
                  above_WT=sum(latest["metrics"][k]["VH_min"] > wt+1e-9 for k in candidates),
                  candidates_sha256=sha256(r10/"candidates.csv"))
    report["010_seed42"] = latest
    print(json.dumps(report,indent=2,allow_nan=False))


if __name__ == "__main__":
    main()
