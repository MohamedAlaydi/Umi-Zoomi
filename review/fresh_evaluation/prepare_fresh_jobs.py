"""New full-context predictions and native-structure binding-ddG, with held-out controls."""
import csv,hashlib,json,sys,tarfile
from collections import defaultdict
from pathlib import Path
import numpy as np
from biotite.structure.io.pdbx import CIFFile,get_structure
from biotite.structure.io.pdb import PDBFile
from biotite.sequence import ProteinSequence
from biotite.sequence.align import align_optimal,SubstitutionMatrix
from immunum import Annotator
from prepare import ROOT,RUN,AA,table,write_csv,sha


def main():
 if (RUN/'new-job-manifest.json').exists():raise ValueError('New experiment already frozen')
 pool=json.loads((RUN/'pool.json').read_text());valid={r['sequence_id'] for r in table(RUN/'validation/validated-reference-checked.csv')}
 selected=[r for r in pool if r['kind']=='paired' and r['local_numeric_pass'] and r['sequence_id'] in valid]
 for r in selected:r['role']='candidate'
 parent=table(ROOT/'data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv')[0]
 H,L=parent['vh_sequence'],parent['vl_sequence'];pre,post=H.split(parent['cdrh3'])
 ann=Annotator(chains=['H'],scheme='imgt',min_confidence=.1)
 refs=json.loads((ROOT/'runs/011-codex-denovo-vhh/expanded-antibody-references.json').read_text())['polymer_entities']
 seqs=[]
 for ref in refs:
  num=ann.number(ref['entity_poly']['pdbx_seq_one_letter_code_can']);seqs.append((ref['rcsb_id'],''.join(num.numbering.values())))
 matrix=SubstitutionMatrix.std_protein_matrix();novel=[];identity_rows=[]
 for r in pool:
  if r['kind']!='vhh' or not r['local_numeric_pass'] or r['sequence_id'] not in valid:continue
  seq=r['heavy_sequence'];scores=[]
  for name,ref in seqs:
   a=align_optimal(ProteinSequence(seq),ProteinSequence(ref),matrix,gap_penalty=-10,terminal_penalty=True,max_number=1)[0];t=a.trace
   both=t[(t>=0).all(1)];scores.append((sum(seq[i]==ref[j] for i,j in both)/len(t),name))
  best=max(scores);identity_rows.append(dict(sequence_id=r['sequence_id'],identity=best[0],nearest=best[1]))
  if best[0]<.7 and r['canonical_cysteines']:
   r['role']='candidate';novel.append(r)
 # Exact public-database search is reviewed separately. Broadened VHH set remains scope-limited, not final de novo acceptance.
 for r in novel:r['global_known_identity_scope']='Recomputed against23-ish retrieved antibody references; universal database novelty unproven'
 selected+=novel
 (RUN/'fresh-known-identity.json').write_text(json.dumps(identity_rows,indent=2))
 # Controls are new scoring targets; group exact constructs before selecting assay-range controls.
 old={r['cdrh3'] for r in table(ROOT/'people/anas/stabddg_manifest.csv') if r['role']=='control'}
 groups=defaultdict(list)
 for row in table(ROOT/'data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv'):
  c=row['cdrh3']
  if row['vh_sequence']==pre+c+post and row['vl_sequence']==L and len(c)==10 and row['kd_nM'] and c!=parent['cdrh3'] and c not in old:groups[c].append(float(row['kd_nM']))
 ordered=sorted([(float(np.median(k)),c) for c,k in groups.items()]);indices=sorted({round(f*(len(ordered)-1)) for f in np.linspace(0,1,12)})
 controls=[]
 for n,i in enumerate(indices,1):
  kd,c=ordered[i];h=pre+c+post
  controls.append(dict(sequence_id=f'fresh_control_{n:02d}',kind='paired',heavy_sequence=h,light_sequence=L,cdrh3_imgt='SR'+c+'Y',
       role='measured_historical_control',historical_kd_nM=kd,historical_replicates=groups[c],aliases=[],sources=['original SPR table']))
 wt=dict(sequence_id='fresh_WT',kind='paired',heavy_sequence=H,light_sequence=L,cdrh3_imgt='SR'+parent['cdrh3']+'Y',role='WT_control',aliases=[],sources=['original SPR table'])
 # Keep the complete candidate set; no old scores or previous rank limits influence cofold selection.
 all_targets=[wt]+controls+sorted(selected,key=lambda r:r['sequence_id'])
 target=json.loads((ROOT/'review/denovo/rcsb_1n8z_her2_mapping.json').read_text())['query_sequence'];assert len(target)==607
 for batch,start in enumerate(range(0,len(all_targets),18)):
  folder=RUN/f'full607-mol1-batch{batch:02d}';folder.mkdir(exist_ok=False)
  targets=[]
  for r in all_targets[start:start+18]:
   seq={'H':r['heavy_sequence']}
   if r['light_sequence']:seq['L']=r['light_sequence']
   seq['T']=target
   targets.append(dict(name=r['sequence_id'],content=''.join(f'>{c}|protein\n{s}\n' for c,s in seq.items())))
  request=dict(model='mol1',name=f'team14-fresh-full-HER2-{batch:02d}',params=dict(output_format='cif',write_pae=True,seed=271828,diffusion_samples=1),targets=targets)
  (folder/'request.json').write_text(json.dumps(request,indent=2))
 # Native experimental structure for binding-ddG; retain all resolved HER2 protein atoms.
 reference=ROOT/'review/regelkontroll-premie/replay/1n8z.cif';native=get_structure(CIFFile.read(reference),model=1,use_author_fields=False)
 keep=((native.chain_id=='A')&(native.res_id<=107))|((native.chain_id=='B')&(native.res_id<=120))|(native.chain_id=='C')
 native=native[keep&~np.isin(native.element,['H','D'])]
 ca=native[native.atom_name=='CA']
 sequence=lambda chain:''.join(AA[x] for x in ca.res_name[ca.chain_id==chain])
 assert sequence('A')==L and sequence('B')==H and len(sequence('C'))==581
 input_folder=ROOT/'nebius/nebius-runs/inputs/run014';input_folder.mkdir(parents=True,exist_ok=True)
 pdb=PDBFile();pdb.set_structure(native);pdb.write(input_folder/'native_full_HER2.pdb')
 variants=[];variant_map=[]
 for r in selected+controls:
  if r['kind']!='paired':continue
  seq=r['heavy_sequence']
  if len(seq)!=len(H) or r['light_sequence']!=L:continue
  mutations=[]
  for i,(a,b) in enumerate(zip(H,seq),1):
   if a==b:continue
   mask=(native.chain_id=='B')&(native.res_id==i)
   assert set(native.atom_name[mask])>={'N','CA','C','O'}
   assert AA[native.res_name[mask][0]]==a
   mutations.append(dict(chain='B',residue_number=i,insertion_code='',wild_type=a,mutant=b))
  if not mutations:continue
  variants.append(dict(id=r['sequence_id'],mutations=mutations));variant_map.append(dict(sequence_id=r['sequence_id'],role=r['role'],heavy_sequence=seq,light_sequence=L,mutations=mutations,historical_kd_nM=r.get('historical_kd_nM')))
 params=dict(pdb_file='native_full_HER2.pdb',partner_a=['A','B'],partner_b=['C'],variants=variants,mc_samples=20,seed=271828,noise_level_angstrom=.1,batch_tokens=10000)
 (input_folder/'params.json').write_text(json.dumps(params))
 with tarfile.open(input_folder/'workload.tar','w') as tf:tf.add(input_folder/'native_full_HER2.pdb',arcname='native_full_HER2.pdb')
 (RUN/'binding-ddg-variant-map.json').write_text(json.dumps(variant_map,indent=2))
 (RUN/'new-job-manifest.json').write_text(json.dumps(dict(target_sequence=target,targets=all_targets,full_context='607-residue native HER2 sequence. No input template, no hotspots, fresh seed271828.',
  scoring='native experimental 1N8Z Fv +581 observed HER2 residues;26 unresolved residues and glycans not represented in ddG input.',native_reference_sha256=sha(reference),
  ddg_PDB_sha256=sha(input_folder/'native_full_HER2.pdb'),binding_ddg_parameters=params,unpaired_VHHs=len(novel),paired_candidates=sum(r['kind']=='paired' for r in selected),
  candidate_count=len(selected),controls=len(controls),WT=True),indent=2))
 print(json.dumps({'candidates':len(selected),'paired':sum(r['kind']=='paired' for r in selected),'VHH':len(novel),'historical_controls':len(controls),'cofold_targets':len(all_targets),'ddg_variants':len(variants),'cofold_batches':len(list(RUN.glob('full607-*')))},indent=2))

if __name__=='__main__':main()
