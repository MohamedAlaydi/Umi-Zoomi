"""Quantify old implementation issues without using old ranks for new selection."""
import importlib.util,json,sys
from collections import Counter
from prepare import ROOT,RUN,table,write_csv
sys.path.insert(0,str(ROOT/'scripts'))
import novelty


def main():
 spec=importlib.util.spec_from_file_location('old_numeric_novelty',RUN/'source-before/scripts__novelty.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
 pool=novelty.load();raw=json.loads((RUN/'pool.json').read_text());rows=[]
 for r in raw:
  if r['kind']!='paired':continue
  core=r['heavy_sequence'][98:108];before,nn_before=old.min_distance(core,pool);after,nn_after=novelty.min_distance(core,pool)
  rows.append(dict(sequence_id=r['sequence_id'],core=core,old_distance=before,true_edit_distance=after,old_nearest=nn_before,edit_nearest=nn_after,
   old_loose_numeric_pass=before>=2 and old.identity_to_trastuzumab(core)<=70,
   fresh_full_IMGT_conservative_pass=r['local_numeric_pass']))
 write_csv(RUN/'novelty-source-impact.csv',rows)
 historical=table(ROOT/'runs/009-claude-multiseed-refold/first_pass_candidates_v2.csv')
 wrong={r['cdrh3']:r for r in historical if r['v2_label']=='NONINFERIOR' and r['v2_delta_lo95_onesided'] and float(r['v2_delta_lo95_onesided'])<-.03}
 summary=dict(raw_Fab_sequences=len(rows),nearest_distance_changed=sum(r['old_distance']!=r['true_edit_distance'] for r in rows),
  old_loose_pass_but_fails_fresh_full_IMGT_conservative=sum(r['old_loose_numeric_pass'] and not r['fresh_full_IMGT_conservative_pass'] for r in rows),
  historical_NONINFERIOR_unique_sequences_lacking_required_lower_bound=len(wrong),affected_historical_H3s=sorted(wrong),
  scope='Historical label audit only. The new candidate evaluation does not load these labels or scores.',
  semantics='Seed-to-seed model confidence cannot establish therapeutic or assay noninferiority, even with the statistical sign corrected.')
 (RUN/'source-audit-impact.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
