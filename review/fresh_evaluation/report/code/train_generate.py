"""Train fresh assay-specific models and generate new, independently gated H3 proposals.

No old model, saved probability, old ranking or model-generated label is loaded.
FACS high-class calibration is not an affinity probability. Quantitative SPR is
modelled only where KD was actually reported. Thermal outcome stays unknown.
"""
import csv,hashlib,io,json,os,sys,zipfile
from collections import defaultdict,Counter
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.special import logit
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression,Ridge
from sklearn.metrics import roc_auc_score,brier_score_loss,mean_squared_error
from sklearn.model_selection import GroupKFold
from threadpoolctl import threadpool_limits
import joblib
from rapidfuzz import process
from rapidfuzz.distance import Levenshtein
from prepare import ROOT,RUN,table,write_csv,sha
AA='ACDEFGHIKLMNPQRSTVWY';IDX={a:i for i,a in enumerate(AA)};SEED=271828


def encoded(seqs):return np.array([[IDX[a] for a in s] for s in seqs],dtype=np.int16)
def onehot(x):
 n=len(x);return sparse.csr_matrix((np.ones(n*10,dtype=np.float32),(np.repeat(np.arange(n),10),(np.tile(np.arange(10),n)*20+x.ravel()))),shape=(n,200))
def affinity_features(x,wt):return sparse.hstack([onehot(x),sparse.csr_matrix((x!=wt).sum(1)[:,None]/10)],format='csr')
def cal_predict(model,cal,x):
 p=model.predict_proba(x)[:,1];return cal.predict_proba(logit(np.clip(p,1e-6,1-1e-6))[:,None])[:,1]
def cluster_sequences(seqs):
 parent=list(range(len(seqs)))
 def find(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 for i,a in enumerate(seqs):
  for j in range(i):
   if Levenshtein.distance(a,seqs[j])<=2:parent[find(i)]=find(j)
 return np.array([find(i) for i in range(len(seqs))])


def main():
 out=RUN/'training';out.mkdir(exist_ok=True)
 if (out/'fresh-models.joblib').exists():raise ValueError('Training already completed; preserve frozen model')
 sprpath=ROOT/'data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv';spr=table(sprpath);parent=spr[0];wt=parent['cdrh3'];prefix,suffix=parent['vh_sequence'].split(wt)
 sprseq={r['cdrh3'] for r in spr};facs=ROOT/'data/her2-trastuzumab/tz_her2_facs_3classes_524346.csv.zip'
 seqs=[];labels=[]
 with zipfile.ZipFile(facs) as z:
  name,=[n for n in z.namelist() if n.endswith('.csv') and '__MACOSX' not in n]
  for r in csv.DictReader(io.TextIOWrapper(z.open(name))):
   s=r['cdrh3']
   if s in sprseq:continue # Reserve all overlapping SPR constructs for external assessment.
   assert len(s)==10 and set(s)<=set(AA)
   seqs.append(s);labels.append(int(r['binding_class']=='high'))
 assert len(seqs)==len(set(seqs))
 x=encoded(seqs);y=np.asarray(labels,dtype=int)
 keys=np.array([s[0]+s[4:7] for s in seqs]);unique_keys=set(keys.tolist())
 assignment={k:int(hashlib.sha256((str(SEED)+':'+k).encode()).hexdigest()[:8],16)%100 for k in unique_keys}
 values=np.array([assignment[k] for k in keys]);train=values<70;cal=(values>=70)&(values<85);test=values>=85
 assert not(set(keys[train])&set(keys[test])) and not(set(keys[cal])&set(keys[test]))
 protocol=dict(seed=SEED,source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [sprpath,facs]},
  FACS_objective='High FACS class versus other classes; expression/binding confounded, not KD or Tm.',
  split='SHA256 of four native-contact-position amino acids,70/15/15 train/calibration/test; all SPR overlap removed before fitting.',
  counts={'train':int(train.sum()),'calibration':int(cal.sum()),'test':int(test.sum())},
  contact_patterns=len(unique_keys),WT_contact_pattern_split=assignment[wt[0]+wt[4:7]],
  SPR_objective='log10 quantified KD relative to median historical WT; no-reportable/inconclusive/unreported are not imputed affinities.',
  SPR_validation='GroupKFold5 on connected components of edit distance<=2; one row per measured construct.',
  fixed_models='Binary categorical GBM(max_iter120,max_leaf15,min_leaf40,l2=.5) and one-hot logistic(C=1). Ridge(alpha10) on measured logKD. Scalar Platt calibration on disjoint contact groups.',
  generator='200k deterministic proposals from WT plus6 measured tight-binding parents; no hard D/M removal or fixed-contact identity. Exact reference gate after proposal scoring.',
  caveats=['FACS split remains within one scaffold.','Cluster-CV uncertainty cannot establish novel-scaffold transfer.','Bootstrap ensemble spread is not predictive confidence.','No learned thermal predictor.'])
 (out/'protocol-before-fit.json').write_text(json.dumps(protocol,indent=2))
 print(json.dumps({'phase':'training_started',**protocol['counts']}),flush=True)
 oh=onehot(x)
 with threadpool_limits(4):
  gb=HistGradientBoostingClassifier(max_iter=120,max_leaf_nodes=15,min_samples_leaf=40,l2_regularization=.5,categorical_features=list(range(10)),random_state=SEED)
  gb.fit(x[train],y[train]);lr=LogisticRegression(C=1.,max_iter=500,solver='lbfgs');lr.fit(oh[train],y[train])
  calibrators=[];scores={}
  for name,model,xx in [('categorical_gbm',gb,x),('onehot_logistic',lr,oh)]:
   pc=model.predict_proba(xx[cal])[:,1];platt=LogisticRegression(C=100.,max_iter=300).fit(logit(np.clip(pc,1e-6,1-1e-6))[:,None],y[cal]);calibrators.append(platt)
   p=cal_predict(model,platt,xx[test]);scores[name]=dict(test_auc=float(roc_auc_score(y[test],p)),test_brier=float(brier_score_loss(y[test],p)),
    test_n=int(test.sum()),test_high=int(y[test].sum()))
  # Exact-construct SPR aggregation. Quantified affinity is kept separate from assay reportability.
  groups=defaultdict(list)
  for r in spr:
   c=r['cdrh3']
   if len(c)==10 and r['vh_sequence']==prefix+c+suffix and r['vl_sequence']==parent['vl_sequence']:groups[c].append(r)
  quantified=[]
  wtvals=[float(r['kd_nM']) for r in groups[wt] if r['kd_nM']];wtkd=float(np.median(wtvals))
  for c,rr in groups.items():
   vals=[float(r['kd_nM']) for r in rr if r['kd_nM']]
   if vals:quantified.append((c,float(np.median(vals))))
  s=[q[0] for q in quantified];kd=np.array([q[1] for q in quantified]);xs=encoded(s);ys=np.log10(kd/wtkd);features=affinity_features(xs,encoded([wt])[0])
  clusters=cluster_sequences(s);unique_clusters=len(set(clusters));oof=np.full(len(s),np.nan)
  if unique_clusters>=5:
   for tr,te in GroupKFold(5).split(features,ys,groups=clusters):
    m=Ridge(alpha=10.,solver='lsqr').fit(features[tr],ys[tr]);oof[te]=m.predict(features[te])
   rho=float(spearmanr(ys,oof).statistic);mse=float(mean_squared_error(ys,oof));baseline=float(np.mean((ys-np.mean(ys))**2))
  else:rho=None;mse=None;baseline=None
  usable=bool(rho is not None and rho>0 and mse<baseline)
  rng=np.random.default_rng(SEED);ensemble=[]
  for i in range(16):
   ix=rng.integers(len(ys),size=len(ys));ensemble.append(Ridge(alpha=10.,solver='lsqr').fit(features[ix],ys[ix]))
  fit=Ridge(alpha=10.,solver='lsqr').fit(features,ys)
  for name,model,xx in [('categorical_gbm',gb,xs),('onehot_logistic',lr,onehot(xs))]:
   p=cal_predict(model,calibrators[0 if name=='categorical_gbm' else 1],xx)
   scores[name]['external_quantified_SPR_rho_logKD']=float(spearmanr(np.log10(kd),p).statistic)
  spr_summary=dict(quantified_constructs=len(s),clusters=unique_clusters,WT_historical_kd_nM=wtkd,WT_observations=wtvals,
   cluster_OOF_rho=rho,cluster_OOF_MSE=mse,mean_baseline_MSE=baseline,affinity_score_used_for_generation=usable,
   restriction='Conditional on reported KD, not a calibrated probability of measurable binding or S-tier.')
  model=dict(gbm=gb,logistic=lr,calibrators=calibrators,affinity=fit,affinity_ensemble=ensemble,AA=AA,WT=wt,protocol=protocol)
  joblib.dump(model,out/'fresh-models.joblib')
  write_csv(out/'SPR-OOF.csv',[dict(cdrh3=c,kd_nM=float(k),cluster=int(g),OOF_log10_KD_ratio=float(p)) for c,k,g,p in zip(s,kd,clusters,oof)])
  (out/'metrics.json').write_text(json.dumps({'FACS':scores,'SPR':spr_summary},indent=2))
  print(json.dumps({'phase':'models_fitted','FACS':scores,'SPR':spr_summary}),flush=True)
  # New proposals, anchored to experiments rather than to any prior generated shortlist.
  parentseq=[wt]+[c for c,k in sorted(quantified,key=lambda q:q[1]) if c!=wt][:6]
  alphabet=np.array(list(AA.replace('C','')));proposals=set();weights=np.array([.4,1,1,1,.4,.4,.4,1,1,1],dtype=float);weights/=weights.sum()
  for i in range(200000):
   p=list(parentseq[int(rng.integers(len(parentseq)))]);n=int(rng.integers(3,7));sites=rng.choice(10,size=n,replace=False,p=weights)
   for j in sites:p[j]=rng.choice(alphabet[alphabet!=p[j]])
   c=''.join(p)
   if sum(a==b for a,b in zip(c,wt))<=6:proposals.add(c)
  proposals=sorted(proposals);xp=encoded(proposals);pp1=cal_predict(gb,calibrators[0],xp);pp2=cal_predict(lr,calibrators[1],onehot(xp));consensus=np.minimum(pp1,pp2)
  ff=affinity_features(xp,encoded([wt])[0]);preds=np.stack([m.predict(ff) for m in ensemble]);mean=preds.mean(0);sd=preds.std(0,ddof=1);risk=mean+sd
  # Predeclared union of two assays, then actual novelty gate. Missing/failed affinity validation disables its selection role.
  take=set(np.argsort(-consensus)[:1000].tolist())
  if usable:take.update(np.argsort(risk)[:1000].tolist())
  indices=sorted(take);chosen=[proposals[i] for i in indices]
  # Full IMGT loop convention proved by the raw-input cohort script.
  with zipfile.ZipFile(facs) as z:
   name,=[n for n in z.namelist() if n.endswith('.csv') and '__MACOSX' not in n]
   known={'SR'+r['cdrh3']+'Y' for r in csv.DictReader(io.TextIOWrapper(z.open(name)))}
  # Include all provided SPR loops, including different-length controls.
  # Same-background sequences use the independently verified fixed flanks;
  # other backgrounds are numbered by the installed validator environment.
  same_background=[r for r in spr if r['vh_sequence']==prefix+r['cdrh3']+suffix]
  known.update('SR'+r['cdrh3']+'Y' for r in same_background)
  other_heavy=sorted({r['vh_sequence'] for r in spr if r not in same_background})
  if other_heavy:
   import subprocess
   code="import json,sys;from immunum import Annotator;a=Annotator(chains=['H'],scheme='imgt',min_confidence=.1);print(json.dumps([a.segment(s).cdr3 for s in json.load(sys.stdin)]))"
   result=subprocess.run(['/home/hackathon/tools/abguard-venv/bin/python','-c',code],input=json.dumps(other_heavy),text=True,capture_output=True,check=True)
   known.update(json.loads(result.stdout))
  assert len(known)==525063, 'The novelty gate must include every provided loop'
  references=sorted(known);passing=[]
  for start in range(0,len(chosen),32):
   cdrs=chosen[start:start+32];dist=process.cdist(['SR'+c+'Y' for c in cdrs],references,scorer=Levenshtein.distance,score_cutoff=2,workers=4,dtype=np.uint8).min(1)
   for c,d in zip(cdrs,dist):
    if d>=3:passing.append(c)
  lookup={s:i for i,s in enumerate(proposals)};remaining=set(passing);ordered=[]
  while remaining and len(ordered)<64:
   # Two-objective nondominated front; no numerical probability of S-tier is invented.
   values=sorted(remaining,key=lambda c:(risk[lookup[c]] if usable else -consensus[lookup[c]],-consensus[lookup[c]],c));front=[];best=-1.
   for c in values:
    p=consensus[lookup[c]]
    if p>best:front.append(c);best=p
   for c in sorted(front,key=lambda c:-consensus[lookup[c]]):
    remaining.remove(c)
    if all(Levenshtein.distance(c,prior)>=3 for prior in ordered):ordered.append(c)
    if len(ordered)>=64:break
  output=[]
  for rank,c in enumerate(ordered,1):
   i=lookup[c];full=prefix+c+suffix;nn=process.extractOne('SR'+c+'Y',references,scorer=Levenshtein.distance)
   output.append(dict(sequence_id='newML_'+hashlib.sha256(full.encode()).hexdigest()[:12],kind='paired',heavy_sequence=full,light_sequence=parent['vl_sequence'],
    design_description='Fresh grouped FACS/quantified-SPR-guided proposal; no measured phenotype',proposal_rank=rank,cdrh3=c,
    calibrated_FACS_GBM=float(pp1[i]),calibrated_FACS_LR=float(pp2[i]),FACS_conservative_agreement=float(consensus[i]),
    predicted_log10_KD_ratio=float(mean[i]),bootstrap_parameter_spread=float(sd[i]),affinity_score_used=usable,
    provided_IMGT_min_edit_distance=nn[1],provided_IMGT_nearest=nn[0],thermal_measurement=None,official_tier=None))
  write_csv(out/'new-proposals.csv',output)
  write_csv(out/'new-submission.csv',[{k:r[k] for k in ['sequence_id','kind','heavy_sequence','light_sequence','design_description']} for r in output])
  (out/'generation-summary.json').write_text(json.dumps(dict(raw_proposals=200000,unique_after_WT_identity_gate=len(proposals),assay_shortlist=len(chosen),exact_novelty_passes=len(passing),diverse_output=len(output),parents=parentseq,
    no_fixed_grip=True,no_forced_D102_M107_replacement=True,thermostability='unmeasured',S_tier='unknown'),indent=2))
  print(json.dumps({'phase':'generation_completed','unique':len(proposals),'shortlist':len(chosen),'novel':len(passing),'output':len(output)}),flush=True)

if __name__=='__main__':main()
