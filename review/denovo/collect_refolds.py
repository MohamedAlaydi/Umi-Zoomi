"""Sequence-matched cofold evidence, explicit antigen contexts and design-pose RMSD."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from biotite.structure.io.pdbx import CIFFile
from collect_campaign import coordinates,ROOT,RUN,EPITOPE
from regional_confidence import confidence


def ca(path):
    t=next(iter(CIFFile.read(path).values()))['atom_site']
    col=lambda name,dtype=str:t[name].as_array(dtype)
    mask=(col('label_atom_id')=='CA')&(col('pdbx_PDB_model_num',int)==1)
    xyz=np.column_stack([col('Cartn_'+a,float) for a in 'xyz'])
    return {str(c):xyz[mask&(col('label_asym_id')==c)] for c in dict.fromkeys(col('label_asym_id')[mask])}


def align(moving,reference):
    x=moving-moving.mean(axis=0);y=reference-reference.mean(axis=0)
    u,_,vt=np.linalg.svd(x.T@y);rotation=u@np.diag([1,1,np.linalg.det(u@vt)])@vt
    return rotation,reference.mean(axis=0)-moving.mean(axis=0)@rotation


def evaluate(path,entry):
    chains,(chain,pos,xyz)=coordinates(path)
    mapping={}
    for role,sequence in {**entry['antibody_sequences'],'T':entry['target_sequence']}.items():
        matches=[c for c,v in chains.items() if v['sequence']==sequence]
        if len(matches)!=1:raise ValueError(f'Unmatched {entry["name"]} chain {role}')
        mapping[role]=matches[0]
    ab=[mapping[c] for c in entry['antibody_sequences']];target=mapping['T']
    ab_indices=np.flatnonzero(np.isin(chain,ab));ag_indices=np.flatnonzero(chain==target)
    tree=cKDTree(xyz[ag_indices]);id_to_order=dict(zip(chains[target]['ids'],range(1,len(entry['target_sequence'])+1)))
    expected=EPITOPE if entry['context']=='crop119' else {p+488 for p in EPITOPE}
    result={'chain_roles':mapping,'antibody_n_chains':len(ab),
        'clashing_cross_chain_atom_pairs_2A':sum(len(x) for x in tree.query_ball_point(xyz[ab_indices],2.))}
    for cutoff in [4.,4.5,5.]:
        contacted={id_to_order[int(pos[ag_indices[j]])] for group in tree.query_ball_point(xyz[ab_indices],cutoff) for j in group}
        result[f'epitope_recall_{cutoff}']=len(contacted&expected)/19
        result[f'epitope_jaccard_{cutoff}']=len(contacted&expected)/len(contacted|expected)
        result[f'target_residue_contacts_{cutoff}']=len(contacted)
    regional=confidence(path,ab)
    result.update({k:v for k,v in regional.items() if k!='chains'})
    result['regional_chains']=regional['chains']
    if entry.get('design_structure'):
        design=ROOT/entry['design_structure'];dca=ca(design);pca=ca(path)
        target_reference=np.concatenate([dca['C'],dca['D']])
        positions=list(range(489,581))+list(range(591,608))
        indices=np.asarray([p-489 if entry['context']=='crop119' else p-1 for p in positions])
        target_prediction=pca[target][indices]
        rotation,offset=align(target_prediction,target_reference)
        b=pca[mapping['H']];reference=dca['H']
        result['binder_CA_rmsd_after_target_alignment']=float(np.sqrt(np.mean(np.sum((b@rotation+offset-reference)**2,axis=1))))
        r,o=align(b,reference)
        result['binder_self_CA_rmsd']=float(np.sqrt(np.mean(np.sum((b@r+o-reference)**2,axis=1))))
    return result


def main():
    manifest={r['name']:r for r in json.loads((RUN/'local-refold-manifest.json').read_text())}
    output=[]
    for model in ['openfold3','mol1','opendde-abag','af2ig']:
        folder=RUN/('design-initial-guess-af2ig-format-fix' if model=='af2ig' else 'local-refold-'+model)
        if not (folder/'results.json').exists():continue
        data=json.loads((folder/'results.json').read_text())
        for row in data.get('rows',[]):
            name=row['id'];entry=manifest[name]
            if row.get('status')!='ok':
                output.append({'name':name,'model':model,'status':row.get('status'),'error':row.get('error')});continue
            structures=[a for a in data['artifacts'] if a.get('type')=='structure' and a.get('target')==name]
            if len(structures)!=1:raise ValueError('Expected exactly one top structure per target')
            path=folder/'artifacts'/structures[0]['path'];result=evaluate(path,entry)
            result.update(name=name,candidate=entry['candidate'],context=entry['context'],model=model,
                status='ok',iptm=row.get('iptm'),ptm=row.get('ptm'),source_job=data['job_id'],
                interface_pae=row.get('interface_pae'),
                conditioning='supplied design pose' if model=='af2ig' else 'blind; no hotspot or template',
                structure=str(path.relative_to(ROOT)),structure_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                interpretation='Predicted evidence only; no measured affinity, competition or Tm')
            output.append(result)
    (RUN/'local-refold-evidence.json').write_text(json.dumps(output,indent=2))
    print(json.dumps([{'name':r['name'],'model':r['model'],'iptm':r.get('iptm'),
        'epitope_recall':r.get('epitope_recall_4.5'),'ca_nac':r.get('ca_nac'),
        'pose_rmsd':r.get('binder_CA_rmsd_after_target_alignment')} for r in output],indent=2))


if __name__=='__main__':main()
