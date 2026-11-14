"""Place fragment predictions on the experimental HER2 ectodomain and flag impossible overlaps."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from biotite.structure.io.pdbx import CIFFile
from scipy.spatial import cKDTree


def load(path):
    tab = next(iter(CIFFile.read(path).values()))['atom_site']
    def col(key):
        return tab[key].as_array(str)
    keep = ((col('pdbx_PDB_model_num') == '1') & ~np.isin(col('type_symbol'), ['H','D'])
            & (col('occupancy').astype(float) > 0) & np.isin(col('label_alt_id'), ['.','?','A']))
    return {key: col(key)[keep] for key in ['label_asym_id','label_seq_id','label_atom_id','label_comp_id']} | {
        'xyz': np.column_stack([col('Cartn_'+key)[keep].astype(float) for key in 'xyz'])}


def ca(data, chain, offset):
    select = (data['label_asym_id']==chain) & (data['label_atom_id']=='CA')
    pos = data['label_seq_id'][select].astype(int)+offset
    assert len(pos)==len(set(pos))
    return {n:(aa,xyz) for n,aa,xyz in zip(pos,data['label_comp_id'][select],data['xyz'][select],strict=True)}


def fit(a,b):
    x,y=a-a.mean(0),b-b.mean(0)
    u,_,v=np.linalg.svd(x.T@y)
    rot=u@np.diag([1.,1.,np.linalg.det(u@v)])@v
    trans=b.mean(0)-a.mean(0)@rot
    rms=float(np.sqrt(np.sum((a@rot+trans-b)**2,axis=1).mean()))
    return rot,trans,rms


def run(root, reference):
    ref=load(reference)
    observed=ca(ref,'C',0)
    indices=sorted(k for k in observed if 489<=k<=607)
    assert len(indices)==109
    # The block discarded by the 119-residue crop. Omitted carbohydrates and unresolved atoms stay unknown.
    c_mask=ref['label_asym_id']=='C'
    outside=ref['xyz'][c_mask][ref['label_seq_id'][c_mask].astype(int)<489]
    tree=cKDTree(outside)
    raw_ab=ref['xyz'][np.isin(ref['label_asym_id'],['A','B'])]
    assert tree.query(raw_ab)[0].min()>2
    first=next(iter(CIFFile.read(reference).values()))
    native_target=''.join(first['entity_poly']['pdbx_seq_one_letter_code_can'].as_array(str)[2].split())
    short_target=json.loads((root/'runs/011-codex-denovo-vhh/local-refold-manifest.json').read_text())[0]['target_sequence']
    assert native_target[488:607]==short_target
    # Derive the local-fit landmarks directly from native contacts, using the same variable segments as the organiser crop.
    mask=np.zeros(len(raw_ab),dtype=bool)
    ab_xyz=[]
    for chain, last in [('A',107),('B',120)]:
        hits=ref['label_asym_id']==chain
        ab_xyz.extend(ref['xyz'][hits][ref['label_seq_id'][hits].astype(int)<=last])
    d,_=cKDTree(ab_xyz).query(ref['xyz'][c_mask])
    patch=sorted(set(ref['label_seq_id'][c_mask][d<=4.5].astype(int)) & set(indices))
    assert patch==json.loads((root/'review/denovo/target_preparation.json').read_text())['reference_epitope_entity_positions']
    native=np.array([observed[k][1] for k in indices])
    twist=np.array([[0.,1,0],[-1,0,0],[0,0,1]])
    transform,delta,rms=fit(native@twist+np.array([1.,2,3]),native)
    assert rms<1e-8 and np.allclose((raw_ab@twist+[1.,2,3])@transform+delta,raw_ab)

    rows=[]
    def add(q,model,seed,scheme,path,digest,roles):
        assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
        data=load(path)
        lookup=ca(data,roles['T'],488)
        assert set(lookup)==set(range(489,608)) and all(lookup[k][0]==observed[k][0] for k in indices)
        mask=np.isin(data['label_asym_id'],[v for k,v in roles.items() if k!='T'])
        ab=data['xyz'][mask]
        assert len(ab)>0
        row=dict(query=q,model=model,seed=seed,template=scheme,structure_sha256=digest)
        for label,landmarks in [('whole_crop',indices),('native_patch',patch)]:
            a=np.array([lookup[i][1] for i in landmarks]);b=np.array([observed[i][1] for i in landmarks])
            transform,delta,rms=fit(a,b)
            distances=tree.query(ab@transform+delta)[0]
            row[label+'_fit_rmsd_A']=round(rms,4)
            row[label+'_Ab_atoms_within_2A_of_omitted_HER2']=int((distances<2).sum())
            row[label+'_closest_A']=round(float(distances.min()),4)
        rows.append(row)
    r=root/'runs/review-apheris-of3-panel'
    for sub in [r,r/'extension',r/'pair-repeats']:
        for d,scheme in [('prediction','none'),('prediction-her2-template','HER2')]:
            for x in json.loads((sub/d/'result.json').read_text())['result']['predictions']:
                q=x['query_id'];roles={'T':'T','H':'H'}
                if not q.startswith('novel'):roles['L']='L'
                match,=[v for v in csv.DictReader((root/'review/panel18plus2/OPENFOLD_RESULTS.csv').open()) if
                        v['query']==q and int(v['seed'])==x['seed'] and v['condition']==('no_template' if scheme=='none' else 'HER2_only_template')]
                add(q,'apheris-openfold3',x['seed'],scheme,sub/d/x['path'],match['model_sha256'],roles)
    pre=root/'runs/011-codex-denovo-vhh'
    aliases={v['candidate']:v['name'].split('_')[0] for v in json.loads((pre/'local-refold-manifest.json').read_text()) if v['name'].endswith('_crop119')}
    common=json.loads((root/'runs/012-codex-18plus2/common-evidence.json').read_text())
    extra=[v for v in json.loads((pre/'local-refold-evidence.json').read_text()) if v['name']=='novel1_crop119' and v['model'] in ('mol1','opendde-abag')]
    for v in common+extra:
        q=aliases.get(v['candidate'],v['candidate'])
        add(q,v['model'],42,'none',root/v['structure'],v['structure_sha256'],v['chain_roles'])
    assert len(rows)==104 and len({(r['query'],r['model'],r['seed'],r['template']) for r in rows})==104
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('root',type=Path);p.add_argument('reference',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args()
    results=run(args.root,args.reference)
    with args.output.open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
