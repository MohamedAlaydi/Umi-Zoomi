"""Evaluate prespecified regional confidence on the completed 30-member SPR panel."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
from regional_confidence import confidence

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/011-codex-denovo-vhh'
SOURCE=ROOT/'data/rfd4-proteina/docs/runs/009-claude-multiseed-refold/boltz2-calib'
MANIFEST=ROOT/'runs/009-claude-multiseed-refold/manifest_calibration.csv'


def main():
    manifest=list(csv.DictReader(MANIFEST.open()));results=[];digests={}
    metrics=['ca_nac','cdr_ca_plddt','antibody_ca_plddt','iptm','vh_min_pair']
    per_seed=[]
    for row in manifest:
        query=row['query_id'];sample=[]
        for seed in [1,2,42]:
            files=list((SOURCE/query/f'seed_{seed}').glob('*_model.cif'))
            if len(files)!=1:raise ValueError(f'Incomplete/ambiguous panel {query} seed{seed}')
            structure=files[0];scores=structure.with_name(structure.name.replace('_model.cif','_scores.json'))
            score=json.loads(scores.read_text());regional=confidence(structure,['A','B'])
            h=regional['chains']['B']['sequence']
            if h[98:108]!=row['cdrh3']:raise ValueError('SPR candidate/model mismatch')
            mat=np.asarray(score['chain_chain_interface_predicted_tm_score'],float)
            native={'iptm':score['interface_predicted_tm_score'],
                    'vh_min_pair':min((mat[1,2]+mat[2,1])/2,(mat[1,3]+mat[3,1])/2)}
            item=dict(query=query,seed=seed,**{m:regional[m] for m in metrics if m in regional},**native)
            sample.append(item);per_seed.append(item)
            for p in [structure,scores]:digests[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
        results.append({**row,**{m:float(np.median([s[m] for s in sample])) for m in metrics},'n_seeds':len(sample)})
    quantified=[r for r in results if r['binding_result']=='quantified_binding' and r['kd_nM']]
    y=np.log10([float(r['kd_nM']) for r in quantified])
    rng=np.random.default_rng(20261114);statistics={}
    for m in metrics:
        x=np.asarray([r[m] for r in quantified])
        observed=spearmanr(x,y)
        samples=[]
        for _ in range(2000):
            indices=rng.integers(0,len(y),len(y));v=spearmanr(x[indices],y[indices]).statistic
            if np.isfinite(v):samples.append(v)
        statistics[m]={'n_constructs':len(y),'rho_log10_KD':float(observed.statistic),
                       'p':float(observed.pvalue),'bootstrap_ci95':np.percentile(samples,[2.5,97.5]).tolist()}
    with (RUN/'regional-calibration.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
    with (RUN/'regional-calibration-seeds.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(per_seed[0]));writer.writeheader();writer.writerows(per_seed)
    paired_rng=np.random.default_rng(20261115);paired_differences=[]
    xn=np.asarray([r['ca_nac'] for r in quantified]);xi=np.asarray([r['iptm'] for r in quantified])
    for _ in range(2000):
        ids=paired_rng.integers(0,len(y),len(y))
        delta=spearmanr(xn[ids],y[ids]).statistic-spearmanr(xi[ids],y[ids]).statistic
        if np.isfinite(delta):paired_differences.append(delta)
    paired={'definition':'rho(NAC, logKD) minus rho(ipTM, logKD); more negative favors NAC',
            'difference':statistics['ca_nac']['rho_log10_KD']-statistics['iptm']['rho_log10_KD'],
            'paired_bootstrap_ci95':np.percentile(paired_differences,[2.5,97.5]).tolist()}
    report={'source':'CA-based NAC adaptation of arXiv:2610.23136v2; region masks from immunum2.1.0',
        'scope':'Retrospective stratified 30-sequence panel, 3 Boltz2 seeds per construct, 25 quantified KD. No threshold fitting or prospective validation. Five no-reportable-KD rows excluded from continuous affinity endpoint.',
        'n_sequences':len(results),'n_structures':len(per_seed),'statistics':statistics,
        'paired_NAC_minus_ipTM':paired,'input_hashes':digests,
        'manifest_sha256':hashlib.sha256(MANIFEST.read_bytes()).hexdigest()}
    (RUN/'regional-calibration.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='input_hashes'},indent=2))


if __name__=='__main__':main()
