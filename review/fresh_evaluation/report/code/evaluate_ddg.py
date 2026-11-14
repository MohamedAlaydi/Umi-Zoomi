"""Evaluate the new binding-ddG run against new, measured historical controls.

MC error measures numerical sampling, not experimental or predictive uncertainty.
The primary control outcome is log measured KD, grouped by exact construct.
"""
import csv,json
import numpy as np
from scipy.stats import spearmanr
from prepare import ROOT,RUN,table,write_csv,sha


def main():
 folder=RUN/'native-binding-ddg';receipt=json.loads((folder/'result.json').read_text())
 assert receipt['status']=='succeeded' and receipt['semantic_validation']['variants_scored']==76
 files={sha(p):p for p in folder.iterdir() if p.is_file()}
 for item in receipt['native_result']['files']:
  assert item['file']['sha256'] in files,'Missing or changed downloaded artifact'
 scoremeta=next(v for v in receipt['native_result']['files'] if v['name']=='scores')
 rows=table(files[scoremeta['file']['sha256']]);meta=next(v for v in receipt['native_result']['files'] if v['name']=='result')
 details=json.loads(files[meta['file']['sha256']].read_text());variant={r['sequence_id']:r for r in json.loads((RUN/'binding-ddg-variant-map.json').read_text())}
 assert len(rows)==len(variant)==len({r['variant_id'] for r in rows})
 result=[]
 for r in rows:
  v=variant[r['variant_id']]
  result.append(dict(sequence_id=v['sequence_id'],role=v['role'],binding_ddg_kcal_mol=float(r['binding_ddg_kcal_mol']),
   numerical_MC_standard_error=float(r['mc_standard_error_kcal_mol']),historical_kd_nM=v['historical_kd_nM'],
   mutations=len(v['mutations']),heavy_sequence=v['heavy_sequence'],light_sequence=v['light_sequence']))
 controls=[r for r in result if r['role']=='measured_historical_control'];x=np.array([r['binding_ddg_kcal_mol'] for r in controls]);y=np.log10([r['historical_kd_nM'] for r in controls])
 rho=float(spearmanr(x,y).statistic);rng=np.random.default_rng(271828);boot=[]
 for _ in range(5000):
  i=rng.integers(len(x),size=len(x))
  if len(set(x[i]))>1 and len(set(y[i]))>1:boot.append(float(spearmanr(x[i],y[i]).statistic))
 ci=np.quantile(boot,[.025,.975]).tolist();usable=bool(rho>0 and ci[0]>0)
 summary=dict(operation_id=receipt['operation_id'],variants=len(rows),controls=len(controls),
  control_sampling='12 previously unscored quantified constructs, chosen across the observed KD range. Not prevalence-representative.',
  control_spearman_rho=rho,control_construct_bootstrap_95CI=ci,
  control_better_than_historical_WT=sum(r['historical_kd_nM']<.1345 for r in controls),
  ranking_role='secondary, conditional on native bound pose' if usable else 'informational only; insufficient control evidence',
  usable_secondary_ranker=usable,source_revision=details['source_revision'],checkpoint_sha256=details['checkpoint_sha256'],
  binding_ddg_convention=details['binding_ddg_convention'],
  caveats=['Native-pose conditional: cannot establish docking, competition, expression or thermal stability.',
   'Negative predicted binding-ddG is not demonstrated tighter binding than WT.',
   'MC standard error is not a prediction interval.',
   '12 controls span the KD range; performance may be lower in the narrow candidate range.'])
 write_csv(RUN/'fresh-binding-ddg.csv',result);(RUN/'binding-ddg-calibration.json').write_text(json.dumps(summary,indent=2))
 print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
