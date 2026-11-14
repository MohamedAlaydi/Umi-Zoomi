"""Freeze fresh model-generated sequence and literature-informed framework tests."""
import json,csv,tarfile
from pathlib import Path
import numpy as np
from biotite.structure.io.pdbx import CIFFile
from prepare import ROOT,RUN,AA,table,write_csv,sha


def main():
 dest=RUN/'new-sequence-experiment.json'
 if dest.exists():raise ValueError('Preserve already frozen experiment')
 props=table(RUN/'training/new-proposals.csv');selected=[]
 # Complementary measured-assay hypotheses; rules do not use cofold outcomes.
 for column,reverse,n in [('FACS_conservative_agreement',True,4),('predicted_log10_KD_ratio',False,4)]:
  for r in sorted(props,key=lambda x:float(x[column]),reverse=reverse):
   if r['sequence_id'] not in {x['sequence_id'] for x in selected}:selected.append(r)
   if len(selected)>=n+(4 if not reverse else 0):break
 balance=sorted(props,key=lambda x:float(x['predicted_log10_KD_ratio'])-float(x['FACS_conservative_agreement']))
 for r in balance:
  if float(r['FACS_conservative_agreement'])>=.5 and r['sequence_id'] not in {x['sequence_id'] for x in selected}:selected.append(r)
  if len(selected)>=12:break
 assert len(selected)==12
 # Verify paper residue numbering directly against its named experimental PDB.
 paper=RUN/'framework-7mn8.cif';t=next(iter(CIFFile.read(paper).values()))['atom_site'];col=lambda n:t[n].as_array(str)
 m=(col('label_asym_id')=='E')&(col('label_atom_id')=='CA');seq=''.join(AA[a] for a in col('label_comp_id')[m])
 orig=table(ROOT/'data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv')[0];H=orig['vh_sequence'];L=orig['vl_sequence']
 assert seq[:len(H)]==H and H[84]=='S' and H[86]=='R'
 assert [(int(a),int(b)) for a,b in zip(col('auth_seq_id')[m],col('label_seq_id')[m])][:len(H)]==[(i,i) for i in range(1,len(H)+1)]
 targets=[]
 for r in selected:
  targets.append(dict(sequence_id=r['sequence_id'],kind='paired',heavy_sequence=r['heavy_sequence'],light_sequence=r['light_sequence'],
   role='new_model_generated_candidate',cdrh3_imgt='SR'+r['cdrh3']+'Y',design_description='New grouped assay-model-guided H3 proposal; unmeasured phenotype',
   sources=['training/new-proposals.csv'],aliases=[],parent=None))
 # Matched framework tests: two from each assay objective. The measured paper
 # result was on full mAb, with possible glycan effects; transfer is unproven.
 for r in [targets[i] for i in [0,1,4,5]]:
  h=r['heavy_sequence'];assert h[84]=='S' and h[86]=='R';mut=h[:84]+'N'+h[85:86]+'T'+h[87:]
  targets.append({**r,'sequence_id':r['sequence_id']+'_FW85N87T','heavy_sequence':mut,'parent':r['sequence_id'],
   'role':'literature_framework_transfer_candidate','design_description':'New H3 + verified 7MN8 VH S85N/R87T framework hypothesis. Fv/cell-free transfer unproven; adds NLT glycosylation sequon.'})
 control={**targets[0],'sequence_id':'fresh_WT_FW85N87T','heavy_sequence':H[:84]+'N'+H[85:86]+'T'+H[87:],
  'cdrh3_imgt':'SR'+orig['cdrh3']+'Y','role':'literature_framework_control','parent':'fresh_WT','design_description':'Framework transfer control; WT H3 means ineligible for submission.'}
 targets.append(control)
 target=json.loads((RUN/'new-job-manifest.json').read_text())['target_sequence'];folder=RUN/'newML-full607-mol1';folder.mkdir()
 request=dict(model='mol1',name='team14-fresh-new-sequences-and-framework',params=dict(output_format='cif',write_pae=True,seed=271828,diffusion_samples=1),targets=[])
 for r in targets:
  request['targets'].append(dict(name=r['sequence_id'],content=''.join(f'>{c}|protein\n{s}\n' for c,s in [('H',r['heavy_sequence']),('L',L),('T',target)])))
 (folder/'request.json').write_text(json.dumps(request,indent=2))
 variants=[]
 for r in targets:
  mutations=[dict(chain='B',residue_number=i,insertion_code='',wild_type=a,mutant=b) for i,(a,b) in enumerate(zip(H,r['heavy_sequence']),1) if a!=b]
  variants.append(dict(id=r['sequence_id'],mutations=mutations))
 old=ROOT/'nebius/nebius-runs/inputs/run014';new=ROOT/'nebius/nebius-runs/inputs/run014-newML';new.mkdir()
 (new/'native_full_HER2.pdb').write_bytes((old/'native_full_HER2.pdb').read_bytes());params=json.loads((old/'params.json').read_text());params['variants']=variants
 (new/'params.json').write_text(json.dumps(params,indent=2))
 with tarfile.open(new/'workload.tar','w') as tf:tf.add(new/'native_full_HER2.pdb',arcname='native_full_HER2.pdb')
 write_csv(RUN/'new-sequences-submission.csv',[{k:r[k] for k in ['sequence_id','kind','heavy_sequence','light_sequence','design_description']} for r in targets if r['role']!='literature_framework_control'])
 dest.write_text(json.dumps(dict(targets=targets,seed=271828,paper='https://doi.org/10.1080/19420862.2025.2532117',paper_PDB='7MN8 entity chain E, auth=label=raw linear positions85/87, verified WT120aa exact prefix',
  paper_PDB_sha256=sha(paper),literature_result_scope='Full trastuzumab mAb, measured higher Tm and retained HER2 cell binding. New N-linked glycosylation site; no evidence of transfer to new H3/Fv/cell-free expression.',
  hypothesis='Separately modify H3 for binding and distant framework for thermal stability. No measured Tm or affinity claimed.',raw_proposal_count=len(props),
  generation_correction='First generation emitted68 proposals because a Pareto-front loop finished the front after reaching64. Source cap fixed; all68 retained as auditable raw proposals. Only12 prospectively selected for this experiment.'),indent=2))
 print(json.dumps({'new_H3_parents':12,'matched_framework_variants':4,'framework_control':1,'cofold_targets':len(targets),'submission_candidates':16}))

if __name__=='__main__':main()
