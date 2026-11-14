"""Transparent experiment allocation; priorities are not probabilities of S-tier.

Selection is adaptive to the new evidence, not a held-out benchmark of ranking.
Two formats are kept because the user requested18 optimisation +2 de novo.
"""
import json
from collections import defaultdict
from rapidfuzz.distance import Levenshtein
from prepare import ROOT,RUN,table,write_csv


def main():
 meta=json.loads((RUN/'new-job-manifest.json').read_text());entries={r['sequence_id']:r for r in meta['targets']};entries.update({r['sequence_id']:r for r in json.loads((RUN/'new-sequence-experiment.json').read_text())['targets']})
 assays={r['sequence_id']:r for r in table(RUN/'fresh-affinity-sensitivity.csv')};known={r['sequence_id']:r for r in table(RUN/'fresh-known-antibody-recheck.csv')};geometry=defaultdict(dict)
 for r in json.loads((RUN/'fresh-full-context-geometry.json').read_text())['rows']:
  if r['status']=='ok':geometry[r['sequence_id']][r['model']]=r
 validated={r['sequence_id'] for folder in ['validation','new-sequence-validation'] for r in table(RUN/folder/'validated-reference-checked.csv')}
 rows=[]
 for sid,e in entries.items():
  if e['role'] in ['WT_control','measured_historical_control','literature_framework_control']:continue
  g=geometry[sid];m=g.get('mol1');od=g.get('opendde-abag');a=assays.get(sid,{})
  supported=bool(m and m['epitope_recall_4.5']>=.8 and m.get('residue_pair_contact_PAE_4.5') is not None and m['residue_pair_contact_PAE_4.5']<=10 and m['own_interface_atom_clashes_lt2A']<=5)
  k=known.get(sid);row=dict(sequence_id=sid,kind=e['kind'],role=e['role'],aliases=';'.join(e.get('aliases',[])),
   heavy_sequence=e['heavy_sequence'],light_sequence=e['light_sequence'],cdrh3_imgt=e['cdrh3_imgt'],local_abguard_pass=sid in validated,
   full_HER2_Mol1_geometry_supported=supported,Mol1_epitope_recall=m.get('epitope_recall_4.5') if m else None,
   Mol1_interface_PAE=m.get('residue_pair_contact_PAE_4.5') if m else None,Mol1_H3_plddt=m.get('H3_mean_plddt') if m else None,
   OpenDDE_epitope_recall=od.get('epitope_recall_4.5') if od else None,OpenDDE_interface_PAE=od.get('residue_pair_contact_PAE_4.5') if od else None,
   FACS_agreement=a.get('FACS_agreement_min'),Ridge_log10_KD_ratio=a.get('SPR_predicted_log10_KD_ratio'),GP_log10_KD_ratio=a.get('GP_sensitivity_log10_KD_ratio'),
   framework_transfer_hypothesis=e['role']=='literature_framework_transfer_candidate',
   assay_model_scope=a.get('assay_model_scope'),known_identity_conservative=k.get('max_identity_conservative_two_definitions') if k else None,
   global_database_de_novo_status='pending organiser database' if e['kind']=='vhh' else 'optimisation',
   thermal_measurement=None,official_tier=None)
  rows.append(row)
 write_csv(RUN/'candidate-evidence.csv',rows)
 fabs=[r for r in rows if r['kind']=='paired' and r['local_abguard_pass'] and r['full_HER2_Mol1_geometry_supported']]
 def risk(r):return max(float(r['Ridge_log10_KD_ratio']),float(r['GP_log10_KD_ratio']))
 regular=[r for r in fabs if not r['framework_transfer_hypothesis']];selected=[];reasons={}
 def add(r,reason,diverse=True):
  if r['sequence_id'] in reasons:return False
  if diverse and any(Levenshtein.distance(r['cdrh3_imgt'],p['cdrh3_imgt'])<2 for p in selected if not p['framework_transfer_hypothesis']):return False
  selected.append(r);reasons[r['sequence_id']]=reason;return True
 # Fixed allocation of complementary hypotheses; thresholds are internal
 # prioritisation choices, never official eligibility or biological pass marks.
 framework=sorted([r for r in fabs if r['framework_transfer_hypothesis']],key=risk)[:2]
 for r in framework:add(r,'Literature-informed framework transfer hypothesis; phenotype unknown',False)
 for predicate,n,reason in [
  (lambda r:float(r['FACS_agreement'])>=.1,6,'Lower conditional-affinity predictions from both fresh models'),
  (lambda r:float(r['FACS_agreement'])>=.7,6,'Balance FACS-class agreement and conditional-affinity models'),
  (lambda r:float(r['FACS_agreement'])>=.95,4,'FACS-screening hedge; not evidence of tighter-than-WT affinity')]:
  count=0
  for r in sorted([r for r in regular if predicate(r)],key=risk):
   if add(r,reason):count+=1
   if count>=n or len(selected)>=18:break
 for r in sorted(regular,key=risk):
  if len(selected)>=18:break
  add(r,'Additional diverse, full-context-supported Fab')
 if len(selected)<18:raise ValueError('Insufficient supported unique Fab hypotheses; do not fill silently')
 selected=selected[:18]
 # Rank two framework tests and assay-guided parents near the top, with a
 # screened, higher-expression-class alternative among the guaranteed four.
 chosen_ids={r['sequence_id'] for r in selected};priority=[]
 aff=sorted([r for r in selected if not r['framework_transfer_hypothesis']],key=risk)
 if aff:priority.append(aff[0])
 if framework:priority.append(framework[0])
 balanced=next((r for r in aff if float(r['FACS_agreement'])>=.7 and r not in priority),None)
 if balanced:priority.append(balanced)
 if len(framework)>1:priority.append(framework[1])
 priority+=sorted([r for r in selected if r not in priority],key=risk)
 # VHHs are explicitly exploratory. Choose observed epitope support first;
 # nearest-known identity margin remains visible and requires official check.
 vhh=[r for r in rows if r['kind']=='vhh' and r['local_abguard_pass'] and r['known_identity_conservative'] is not None and float(r['known_identity_conservative'])<.7]
 vhh.sort(key=lambda r:(-(r['Mol1_epitope_recall'] or 0),float(r['known_identity_conservative'])))
 if len(vhh)<2:raise ValueError('Two provisional de novo hypotheses unavailable')
 denovo=vhh[:2]
 # Default: preserve strongest Fab opportunities in guaranteed4; de novo
 # reaches the lab if at least16 are allocated. Alternative guarantees both tracks.
 ordered=priority[:14]+denovo+priority[14:]
 alternate=priority[:2]+denovo+priority[2:]
 for name,items in [('18plus2_DRAFT_optimisation_first',ordered),('18plus2_DRAFT_both_tracks_top4',alternate)]:
  assert len(items)==20 and len({r['sequence_id'] for r in items})==20 and sum(r['kind']=='paired' for r in items)==18
  output=[];submission=[]
  for i,r in enumerate(items,1):
   reason=reasons.get(r['sequence_id'],'Exploratory VHH; global database novelty and binding unproven')
   output.append(dict(rank=i,reason=reason,**r));submission.append({k:r[k] for k in ['sequence_id','kind','heavy_sequence','light_sequence']}|{'design_description':reason})
  write_csv(RUN/(name+'.csv'),submission);write_csv(RUN/(name+'_evidence.csv'),output)
 (RUN/'prioritisation-policy.json').write_text(json.dumps(dict(status='DRAFT: no measured phenotype; de novo database eligibility unresolved',
  ranking_role='Heuristic allocation of complementary hypotheses; not calibrated S-tier probability, not a validated decision rule.',
  technical_support='Local explicit-reference abguard pass; Mol1full607 native recall>=.8, contactPAE<=10, own clashes<=5. Internal geometry thresholds, not challenge rules.',
  assay_order='Conservative max of primary Ridge and secondary GP logKD scores; 6 affinity hypotheses,6 FACS-balanced,4 high-FACS hedges,up to2 framework hypotheses; ordinary H3 diversity>=2.',
  OpenDDE='No negative gate: matched full-context WT itself fails to recover native epitope; positive results are additional uncalibrated geometry support.',
  default='Two provisional de novo at15/16; top4 are Fab. Both tracks tested if N>=16.',
  alternate='Two provisional de novo at3/4; both tracks among guaranteed4, at cost of two Fab opportunities.',
  guaranteed4=[r['sequence_id'] for r in ordered[:4]],de_novo_candidates=[r['sequence_id'] for r in denovo]),indent=2))
 print(json.dumps({'supported_Fabs':len(fabs),'selected_Fabs':18,'provisional_VHHs':[r['sequence_id'] for r in denovo],'guaranteed4':[(r['sequence_id'],r['cdrh3_imgt']) for r in ordered[:4]]},indent=2))

if __name__=='__main__':main()
