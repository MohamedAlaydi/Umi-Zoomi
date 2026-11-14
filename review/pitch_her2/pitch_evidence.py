"""Replay the matched candidate poses and calibration from archived Foundry outputs."""
import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr
from biotite.structure.io.pdbx import CIFFile

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT/"review"))
from structure_checks import atom_data, footprint, pair_scores, check_chains

def read_rows(p):
    with p.open() as f:
        return list(csv.DictReader(f))

def read(p):
    return json.loads(p.read_text())

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    r6, = (ROOT/"runs").glob("006-*")
    r9, = (ROOT/"runs").glob("009-*")
    m6 = {r["query_id"]:r["cdrh3"] for r in read_rows(r6/"manifest.csv")}
    m9 = {r["query_id"]:r["cdrh3"] for r in read_rows(r9/"manifest_candidates.csv")}
    cal = {r["query_id"]:r for r in read_rows(r9/"manifest_calibration.csv")}
    ref = ROOT/"data/rfd4-proteina/docs/Data/12-her2/her2_fv_1n8z.cif"
    spr = read_rows(ROOT/"data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv")
    atoms,residues = atom_data(CIFFile.read(ref).block)
    cutoff=4.5
    expected, anchors = footprint(atoms,cutoff)
    assert anchors=={99,103,104,105} and len(expected)==19
    assert digest(r6/"out/prepared/holo/template.cif")==digest(r9/"out/prepared/holo/template.cif")
    marked = {}
    names = [r["query"] for r in read_rows(ROOT/"review/evidence/panel.csv")[:4]]
    poses = defaultdict(dict)
    calibration = defaultdict(list)
    for run,job,queryfile,expected_seeds,sequences in [
        (r6,"boltz2","queries.json",{42},m6),
        (r9,"boltz2-cand-s1to5","queries_cand.json",set(range(1,6)),m9),
        (r9,"boltz2-calib","queries_calib.json",{1,2,42},{k:v["cdrh3"] for k,v in cal.items()})]:
        base=run/"out"/job
        qp=run/"out/prepared/holo"/queryfile
        queries={r["query_id"]:r["chains"] for r in read(qp)["queries"]}
        predictions=read(base/"result.json")["result"]["predictions"]
        pairs={(r["query_id"],r["seed"]) for r in predictions}
        assert set(queries)==set(sequences) and pairs=={(q,s) for q in queries for s in expected_seeds} and len(pairs)==len(predictions)
        for q,chains in queries.items():
            check_chains(chains,sequences[q],spr[0],residues)
        for p in [qp,base/"result.json",base/"config.json"]:
            marked[str(p.relative_to(ROOT))]=digest(p)
        for p in predictions:
            q,s=p["query_id"],p["seed"]
            if job!="boltz2-calib" and q not in m6:continue
            cif=base/p["path"];score=base/p["scores_path"]
            block=CIFFile.read(cif).block
            order=list(block["struct_asym"]["id"].as_array())
            assert order==[c["chain_id"] for c in queries[q]]
            score_v=pair_scores(read(score)["chain_chain_interface_predicted_tm_score"],order)["VH_min"]
            if job=="boltz2-calib":
                calibration[q].append(score_v)
            else:
                a,res=atom_data(block)
                for c in queries[q]:
                    vals=res[c["chain_id"]]; assert "".join(vals[i] for i in sorted(vals))==c["sequence"]
                    if c['chain_id'] in ('C','D'):assert set(vals)==set(residues[c['chain_id']])
                ep,hits=footprint(a,cutoff)
                poses[q][s]=dict(all_four=anchors<=hits,exact=ep==expected,jaccard=len(ep&expected)/len(ep|expected),vh=score_v)
            for f in [cif,score]:marked[str(f.relative_to(ROOT))]=digest(f)
    all_candidates=[q for q in m6 if q.startswith("anas_")]
    seeds=sorted(poses["trastuzumab_wt"])
    assert len(all_candidates)==40 and len(seeds)==6 and all(set(poses[q])==set(seeds) for q in m6)
    kds=[];means=[]
    for q,r in cal.items():
        measured=[float(x['kd_nM']) for x in spr if x['cdrh3']==r['cdrh3'] and x['kd_nM']]
        if not r['kd_nM']:continue
        assert measured and np.isclose(np.median(measured),float(r['kd_nM']),rtol=.0001)
        kds.append(float(r['kd_nM']));means.append(np.mean(calibration[q]))
    print(json.dumps(dict(seeds=seeds,raw_file_digests=marked,
          all_four_by_seed={s:sum(poses[q][s]['all_four'] for q in all_candidates) for s in seeds},
          all_four_every_seed=sum(all(v['all_four'] for v in poses[q].values()) for q in all_candidates),
          exact_by_seed={s:sum(poses[q][s]['exact'] for q in all_candidates) for s in seeds},
          panel_poses={q:poses[q] for q in m6},
          calibration=dict(queries=len(cal),quantified=len(kds),seed_count=3,
                           rho_vh_vs_log_kd=spearmanr(means,np.log10(kds)).statistic)),indent=2,allow_nan=False))

if __name__=="__main__":main()
