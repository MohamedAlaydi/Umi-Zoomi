"""Independent full-context geometry evaluator; no previous score code imported.

All interfaces are protein heavy-atom contacts. Native missing residues/glycans
are explicitly absent; experimental B factors are never interpreted as pLDDT.
"""
import json
import numpy as np
from scipy.spatial import cKDTree
from biotite.structure.io.pdbx import CIFFile
from prepare import ROOT,RUN,AA,sha,write_csv


def read_atoms(path):
 t=next(iter(CIFFile.read(path).values()))['atom_site']
 col=lambda n,dtype=str:t[n].as_array(dtype)
 active=(col('group_PDB')=='ATOM')&(col('pdbx_PDB_model_num',int)==1)&(col('occupancy',float)>0)&~np.isin(col('type_symbol'),['H','D'])
 assert np.isin(col('label_alt_id')[active],['.','?','A']).all(),'Ambiguous alternate atoms'
 names=col('label_atom_id')[active];chain=col('label_asym_id')[active];res=col('label_seq_id',int)[active]
 xyz=np.column_stack([col('Cartn_'+a,float)[active] for a in 'xyz']);comp=col('label_comp_id')[active];b=col('B_iso_or_equiv',float)[active]
 chains={};tokens={};token=0
 for c in dict.fromkeys(chain[names=='CA']):
  idx=np.flatnonzero((chain==c)&(names=='CA'));ids=res[idx]
  assert len(set(ids))==len(ids),'Duplicate CA residue'
  sequence=''.join(AA[a] for a in comp[idx]);positions={int(r):i for i,r in enumerate(ids)}
  chains[c]=dict(sequence=sequence,ids=ids,ca=xyz[idx],ca_confidence=b[idx],atom_indices=np.flatnonzero(chain==c),positions=positions)
 # PAE documentation specifies tokens of the written structure, in file order.
 for i in np.flatnonzero(names=='CA'):
  tokens[(str(chain[i]),int(res[i]))]=token;token+=1
 assert len(tokens)==token
 return dict(chain=chain,res=res,xyz=xyz,names=names,chains=chains,tokens=tokens)


def map_roles(chains,expected):
 roles={}
 for role,sequence in expected.items():
  matched=[c for c,v in chains.items() if v['sequence']==sequence]
  if len(matched)!=1:raise ValueError('Exact chain identity ambiguous or absent: '+role)
  roles[role]=matched[0]
 if len(set(roles.values()))!=len(roles) or set(roles.values())!=set(chains):raise ValueError('Unexpected chain composition')
 return roles


def fit(moving,reference):
 if np.shape(moving)!=np.shape(reference) or len(moving)<3:raise ValueError('Invalid alignment correspondence')
 x=moving-moving.mean(0);y=reference-reference.mean(0);u,_,vt=np.linalg.svd(x.T@y)
 rotation=u@np.diag([1.,1.,np.linalg.det(u@vt)])@vt;offset=reference.mean(0)-moving.mean(0)@rotation
 assert np.linalg.det(rotation)>.99999
 return rotation,offset,float(np.sqrt(np.mean(np.sum((moving@rotation+offset-reference)**2,axis=1))))


def contact_pairs(atoms,antibody,target,cutoff):
 ai=np.flatnonzero(np.isin(atoms['chain'],antibody));ti=np.flatnonzero(atoms['chain']==target)
 groups=cKDTree(atoms['xyz'][ti]).query_ball_point(atoms['xyz'][ai],cutoff)
 return {((str(atoms['chain'][i]),int(atoms['res'][i])),(str(atoms['chain'][ti[j]]),int(atoms['res'][ti[j]]))) for i,group in zip(ai,groups) for j in group}


def interface_pae(pairs,tokens,pae):
 if not pairs:return None
 if pae.shape!=(len(tokens),len(tokens)):raise ValueError('PAE token count mismatch')
 values=[(pae[tokens[a],tokens[b]]+pae[tokens[b],tokens[a]])/2 for a,b in pairs]
 if not np.isfinite(values).all():raise ValueError('Non-finite PAE')
 return float(np.mean(values))


def native_reference():
 p=ROOT/'review/regelkontroll-premie/replay/1n8z.cif';a=read_atoms(p)
 # Explicit variable-domain bounds; remove constant domains before deriving contacts.
 keep=((a['chain']=='A')&(a['res']<=107))|((a['chain']=='B')&(a['res']<=120))|(a['chain']=='C')
 for k in ['chain','res','xyz','names']:a[k]=a[k][keep]
 # Reuse sequence-validated target CA mapping with crystallographic entity IDs.
 assert len(a['chains']['C']['ids'])==581
 footprints={str(d):{b[1] for aa,b in contact_pairs(a,['A','B'],'C',d)} for d in [4.,4.5,5.]}
 return a,footprints,sha(p)


def evaluate(path,entry,meta,native,footprints):
 a=read_atoms(path);expected={'H':entry['heavy_sequence'],'T':meta['target_sequence']}
 if entry['light_sequence']:expected['L']=entry['light_sequence']
 roles=map_roles(a['chains'],expected);ab=[c for k,c in roles.items() if k!='T'];target=roles['T'];tc=a['chains'][target]
 assert len(tc['sequence'])==607
 entity={int(r):i for i,r in enumerate(tc['ids'],1)}
 native_ids=native['chains']['C']['ids'];native_ca=native['chains']['C']['ca']
 # Verify the native resolved sequence against the complete target, residue by residue.
 assert all(meta['target_sequence'][int(i)-1]==aa for i,aa in zip(native_ids,native['chains']['C']['sequence']))
 result=dict(chain_roles=roles,structure_sha256=sha(path),target_length=607,
  conditioning='sequence-only, no input template/hotspot',model_seed=271828)
 atom_ab=np.isin(a['chain'],ab);atom_ag=a['chain']==target
 result['own_interface_atom_clashes_lt2A']=sum(map(len,cKDTree(a['xyz'][atom_ag]).query_ball_point(a['xyz'][atom_ab],2.)))
 atom_order=[a['chains'][c]['ca_confidence'] for c in ab];conf=np.concatenate(atom_order)
 if not ((conf>=0)&(conf<=100)).all():raise ValueError('Unexpected confidence scale')
 result['binder_mean_plddt']=float(conf.mean());result['binder_low_decile_plddt']=float(np.quantile(conf,.1))
 h3=entry['cdrh3_imgt'];h=entry['heavy_sequence'];assert h.count(h3)==1;start=h.index(h3)
 hc=a['chains'][roles['H']]['ca_confidence'][start:start+len(h3)]
 result['H3_mean_plddt']=float(hc.mean());result['H3_low_decile_plddt']=float(np.quantile(hc,.1))
 side=path.with_name(path.stem+'_pae.json');pae=None
 if side.exists() and path.with_name(path.stem+'_pae.npz').exists():
  s=json.loads(side.read_text());assert 'file order' in s.get('token_order',''),'Unknown PAE token ordering'
  with np.load(path.with_name(path.stem+'_pae.npz'),allow_pickle=False) as data:
   assert 'pae' in data.files;pae=data['pae']
  assert pae.shape==(len(a['tokens']),len(a['tokens']))
 result['PAE_artifact_status']='present_and_mapped' if pae is not None else 'missing; interface PAE unavailable'
 observed=set(map(int,native_ids))
 for cutoff in [4.,4.5,5.]:
  pairs=contact_pairs(a,ab,target,cutoff);positions={entity[b[1]] for _,b in pairs};ref=footprints[str(cutoff)]
  result[f'contact_positions_{cutoff}']=sorted(positions)
  result[f'epitope_recall_{cutoff}']=len(positions&ref)/len(ref)
  result[f'epitope_jaccard_all_{cutoff}']=len(positions&ref)/len(positions|ref)
  result[f'epitope_jaccard_observed_{cutoff}']=len(positions&ref)/len((positions&observed)|ref)
  result[f'contacts_at_native_unresolved_{cutoff}']=len(positions-observed)
  result[f'residue_pair_contact_PAE_{cutoff}']=interface_pae(pairs,a['tokens'],pae) if pae is not None else None
 # Three explicit antigen fits reveal domain movement vs local binding-pose error.
 fits={'whole_antigen':observed,'binding_domain':set(range(489,581))|set(range(591,608)),'native_epitope':footprints['4.5']}
 native_fv=np.isin(native['chain'],['A','B'])
 for name,positions in fits.items():
  ids=sorted(positions&observed);reference=np.array([native_ca[np.flatnonzero(native_ids==i)[0]] for i in ids]);moving=tc['ca'][np.array(ids)-1]
  rotation,offset,rmsd=fit(moving,reference);result[name+'_target_CA_rmsd']=rmsd
  moved=a['xyz'][atom_ab]@rotation+offset
  result[name+'_WT_cobinding_atom_overlap_lt2A']=sum(map(len,cKDTree(native['xyz'][native_fv]).query_ball_point(moved,2.)))
 result['competition_interpretation']='Native WT steric overlap supports a competition hypothesis; not a competitive binding assay.'
 return result


def main():
 meta=json.loads((RUN/'new-job-manifest.json').read_text());entries={r['sequence_id']:r for r in meta['targets']}
 if (RUN/'new-sequence-experiment.json').exists():entries.update({r['sequence_id']:r for r in json.loads((RUN/'new-sequence-experiment.json').read_text())['targets']})
 native,footprints,native_sha=native_reference();output=[];seen=set()
 for folder in sorted(RUN.iterdir()):
  if not folder.is_dir() or not(folder/'results.json').exists() or not(folder/'submission.json').exists():continue
  results=json.loads((folder/'results.json').read_text());job=json.loads((folder/'submission.json').read_text())['job_id']
  for r in results['rows']:
   if r.get('status')!='ok':continue
   seqid=r['id'];model=json.loads((folder/'request.json').read_text())['model'];key=(seqid,model,271828)
   if key in seen:raise ValueError('Duplicate delivered prediction; do not choose a best result')
   path=folder/'artifacts'/(seqid+'.cif')
   if not path.exists():continue
   entry=entries[seqid]
   try:row=evaluate(path,entry,meta,native,footprints);seen.add(key);row.update(status='ok')
   except Exception as e:row=dict(status='evaluation_error',error=str(e))
   row.update(sequence_id=seqid,role=entry['role'],kind=entry['kind'],model=model,job_id=job,
    global_iptm=r.get('iptm'),API_runtime_s=r.get('runtime_s'),structure=str(path.relative_to(ROOT)),native_sha256=native_sha)
   output.append(row)
 (RUN/'fresh-full-context-geometry.json').write_text(json.dumps(dict(native_footprints=footprints,rows=output,
  interpretation='Geometry and model confidence only. No measured binding, competition, expression or thermal result.'),indent=2,default=lambda s:sorted(s)))
 flat=[{k:v for k,v in r.items() if not isinstance(v,(dict,list))} for r in output]
 if flat:
  columns=list(dict.fromkeys(k for r in flat for k in r));write_csv(RUN/'fresh-full-context-geometry.csv',[{k:r.get(k) for k in columns} for r in flat])
 print(json.dumps(dict(predictions=len(output),errors=[r for r in output if r['status']!='ok'],native_footprint_counts={k:len(v) for k,v in footprints.items()}),indent=2))

if __name__=='__main__':main()
