"""Score the frozen sequence universe using only the freshly fitted assay models."""
import json,re
import numpy as np
import joblib
from train_generate import encoded,onehot,affinity_features,cal_predict
from prepare import RUN,write_csv


def motifs(sequence,pattern):return ';'.join(f'{m.start()+1}:{m.group()}' for m in re.finditer('(?=('+pattern+'))',sequence))


def main():
 meta=json.loads((RUN/'new-job-manifest.json').read_text());entries={r['sequence_id']:r for r in meta['targets']}
 entries.update({r['sequence_id']:r for r in json.loads((RUN/'new-sequence-experiment.json').read_text())['targets']})
 m=joblib.load(RUN/'training/fresh-models.joblib');scores=[]
 for r in entries.values():
  if r['kind']!='paired':continue
  h=r['heavy_sequence'];c=r['cdrh3_imgt'][2:-1]
  if len(c)!=10:raise ValueError('Assay model does not support this H3 length')
  x=encoded([c]);gb=float(cal_predict(m['gbm'],m['calibrators'][0],x)[0]);lr=float(cal_predict(m['logistic'],m['calibrators'][1],onehot(x))[0])
  f=affinity_features(x,encoded([m['WT']])[0]);pred=np.array([a.predict(f)[0] for a in m['affinity_ensemble']]);mean=float(pred.mean());spread=float(pred.std(ddof=1))
  fw=r['role'] in ['literature_framework_transfer_candidate','literature_framework_control']
  scores.append(dict(sequence_id=r['sequence_id'],role=r['role'],cdrh3=c,FACS_high_class_GBM=gb,FACS_high_class_LR=lr,
   FACS_agreement_min=min(gb,lr),SPR_predicted_log10_KD_ratio=mean,SPR_bootstrap_parameter_spread=spread,
   SPR_conservative_parameter_score=mean+spread,assay_model_scope='H3-only WT-framework counterfactual; new framework effect unmodelled' if fw else 'Same scaffold/10-aa core only; conditional on measurable SPR KD',
   whole_H_glycosylation_sequons=';'.join(f'{i+1}:{h[i:i+3]}' for i in range(len(h)-2) if h[i]=='N' and h[i+1]!='P' and h[i+2] in 'ST'),
   H3_deamidation_motifs=';'.join(f'{i+1}:{c[i:i+2]}' for i in range(9) if c[i:i+2] in ['NG','NS','NT']),
   H3_Asp_motifs=';'.join(f'{i+1}:{c[i:i+2]}' for i in range(9) if c[i:i+2] in ['DG','DP','DS']),
   H3_M_count=c.count('M'),H3_hydrophobic_fraction=sum(a in 'AVILMFWY' for a in c)/len(c),
   H3_formal_charge_proxy=sum(c.count(a) for a in 'KR')-sum(c.count(a) for a in 'DE'),
   biochemical_interpretation='Motif/sequence flags only; not expression, aggregation or Tm predictions.',
   historical_kd_nM=r.get('historical_kd_nM'),thermal_measurement=None,official_tier=None))
 write_csv(RUN/'fresh-assay-and-sequence-scores.csv',scores)
 print(json.dumps({'scored_Fab_constructs':len(scores),'framework_variants_outside_assay_training_domain':sum('counterfactual' in r['assay_model_scope'] for r in scores)}))

if __name__=='__main__':main()
