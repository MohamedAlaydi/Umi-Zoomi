"""Reconstruct the experimental data from original tables, retaining missingness."""
import csv,io,json,zipfile
from collections import Counter,defaultdict
import numpy as np
from rapidfuzz.distance import Levenshtein
from prepare import ROOT,RUN,table,write_csv,sha


def main():
 sprpath=ROOT/'data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv';spr=table(sprpath);parent=spr[0];wt=parent['cdrh3'];pre,post=parent['vh_sequence'].split(wt)
 facspath=ROOT/'data/her2-trastuzumab/tz_her2_facs_3classes_524346.csv.zip';facs=set();class_count=Counter()
 with zipfile.ZipFile(facspath) as z:
  name,=[n for n in z.namelist() if n.endswith('.csv') and '__MACOSX' not in n]
  for r in csv.DictReader(io.TextIOWrapper(z.open(name))):facs.add(r['cdrh3']);class_count[r['binding_class']]+=1
 groups=defaultdict(list)
 for r in spr:groups[(r['vh_sequence'],r['vl_sequence'])].append(r)
 wtvalues=[float(r['kd_nM']) for r in spr if r['vh_sequence']==parent['vh_sequence'] and r['vl_sequence']==parent['vl_sequence'] and r['kd_nM']]
 baseline=float(np.median(wtvalues));rows=[]
 for (h,l),rr in groups.items():
  cores={r['cdrh3'] for r in rr};assert len(cores)==1;c=next(iter(cores));values=[float(r['kd_nM']) for r in rr if r['kd_nM']]
  same=h==pre+c+post and l==parent['vl_sequence'];distance=Levenshtein.distance(c,wt) if same else None
  rows.append(dict(heavy_sequence=h,light_sequence=l,cdrh3=c,same_training_background=same,WT_core_edit_distance=distance,
   overlaps_FACS_exact_H3=c in facs,assay_rows=len(rr),reported_KD_count=len(values),median_KD_nM=float(np.median(values)) if values else None,
   reported_outcomes=';'.join(sorted({r['binding_result'] for r in rr})),historical_KD_better_than_median_WT=(float(np.median(values))<baseline) if values else None))
 unseen=[r for r in rows if r['same_training_background'] and not r['overlaps_FACS_exact_H3']]
 regime=[r for r in unseen if 4<=r['WT_core_edit_distance']<=6]
 measured=[r for r in regime if r['median_KD_nM'] is not None]
 summary=dict(SPR_rows=len(spr),SPR_unique_full_constructs=len(groups),SPR_row_outcomes=dict(Counter(r['binding_result'] for r in spr)),
  FACS_unique=len(facs),FACS_class_rows=dict(class_count),WT_measured_KDs_nM=wtvalues,WT_median_nM=baseline,
  FACS_unseen_same_background_constructs=len(unseen),FACS_unseen_4_to6_mutation_constructs=len(regime),
  FACS_unseen_4_to6_with_quantified_KD=len(measured),FACS_unseen_4_to6_measured_KD_better_than_WT=sum(r['historical_KD_better_than_median_WT'] for r in measured),
  WT_baseline_sensitivity=[dict(WT_nM=v,better_count=sum(r['median_KD_nM']<v for r in measured),quantified_denominator=len(measured)) for v in [min(wtvalues),baseline,max(wtvalues)]],
  interpretation='A selected historical cohort. No-reportable-KD is not a proven nonbinder; quantified-only analysis is conditional on assay reportability. No thermal or competition data for our sequences.',
  source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [sprpath,facspath]})
 write_csv(RUN/'fresh-SPR-construct-audit.csv',rows);(RUN/'fresh-assay-audit.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
