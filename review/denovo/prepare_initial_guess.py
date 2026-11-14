"""Prepare explicit model-completed target backbones for design-conditioned AF2-IG.

The ten missing target residues come from an independent Mol-1 crop prediction.
All 109 experimentally resolved target CAs determine rigid superposition. Binder
coordinates are unchanged. This checks a supplied pose, not blind docking.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from biotite.structure.io.pdbx import CIFFile, get_structure
from collect_refolds import align,ca
from collect_campaign import ROOT,RUN,coordinates


def backbone(path,chain):
    tab=next(iter(CIFFile.read(path).values()))['atom_site']
    col=lambda n,d=str:tab[n].as_array(d)
    keep=(col('label_asym_id')==chain)&(col('pdbx_PDB_model_num',int)==1)&np.isin(col('label_atom_id'),['N','CA','C','O'])
    return [(a,r,int(p),np.array([float(x),float(y),float(z)]))
        for a,r,p,x,y,z in zip(col('label_atom_id')[keep],col('label_comp_id')[keep],col('label_seq_id')[keep],
            col('Cartn_x')[keep],col('Cartn_y')[keep],col('Cartn_z')[keep])]


def compact_cif(atoms):
    fields=['group_PDB','id','type_symbol','label_atom_id','label_comp_id','label_asym_id','label_seq_id',
            'Cartn_x','Cartn_y','Cartn_z','occupancy','B_iso_or_equiv','pdbx_PDB_ins_code','pdbx_PDB_model_num']
    lines=['data_initial_guess','#','loop_']+['_atom_site.'+f for f in fields]
    for i,(chain,name,res,pos,xyz) in enumerate(atoms,1):
        lines.append(f'ATOM {i} {name[0]} {name} {res} {chain} {pos} '+ ' '.join(f'{x:.2f}'.rstrip('0').rstrip('.') for x in xyz)+' 1 0 ? 1')
    return '\n'.join(lines)+'\n#\n'


def main():
    entries=json.loads((RUN/'local-refold-manifest.json').read_text())
    evidence=json.loads((RUN/'local-refold-evidence.json').read_text())
    folder=RUN/'design-initial-guess-af2ig';folder.mkdir(exist_ok=True)
    if (folder/'submission.json').exists():raise ValueError('Freeze already submitted inputs; do not recreate')
    receipt=[];targets=[]
    for entry in entries:
        if entry['context']!='crop119' or not entry.get('design_structure'):continue
        name=entry['name']
        model=next(r for r in evidence if r['name']==name and r['model']=='mol1' and r['status']=='ok')
        model_path=ROOT/model['structure'];design_path=ROOT/entry['design_structure']
        mca=ca(model_path);dca=ca(design_path);resolved=np.array(list(range(92))+list(range(102,119)))
        ref=np.concatenate([dca['C'],dca['D']]);moving=mca[model['chain_roles']['T']][resolved]
        rotation,offset=align(moving,ref)
        rmsd=float(np.sqrt(np.mean(np.sum((moving@rotation+offset-ref)**2,axis=1))))
        atoms=[('T',n,r,p,xyz@rotation+offset) for n,r,p,xyz in backbone(model_path,model['chain_roles']['T'])]
        atoms += [('H',n,r,p,xyz) for n,r,p,xyz in backbone(design_path,'H')]
        structure=folder/(name+'.cif');structure.write_text(compact_cif(atoms))
        # Independent parser and exact-sequence tests, all four backbone atoms required.
        parsed=get_structure(CIFFile.read(structure),model=1,use_author_fields=False)
        assert len(parsed)==len(atoms)
        seqs,_=coordinates(structure)
        assert seqs['T']['sequence']==entry['target_sequence'] and seqs['H']['sequence']==entry['antibody_sequences']['H']
        for ch in ['T','H']:
            residues={p:[] for c,n,r,p,x in atoms if c==ch}
            for c,n,r,p,x in atoms:
                if c==ch:residues[p].append(n)
            assert all(sorted(a)==['C','CA','N','O'] for a in residues.values())
        content=json.dumps({'target':{'structure':structure.read_text(),'chain':'T'},
                            'binder':{'sequence':entry['antibody_sequences']['H'],'chain':'H'}},separators=(',',':'))
        if len(content)>50000:raise ValueError('Content allowance exceeded')
        targets.append(dict(name=name,content=content))
        receipt.append(dict(name=name,candidate=entry['candidate'],design_structure=entry['design_structure'],
            target_completion_source=model['structure'],target_completion_source_sha256=model['structure_sha256'],
            target_resolved_CA_rmsd_to_design=rmsd,input_sha256=hashlib.sha256(structure.read_bytes()).hexdigest(),
            input_structure=str(structure.relative_to(ROOT)),
            interpretation='Model-completed native-sequence target; supplied design pose, not blind docking'))
    (folder/'request.json').write_text(json.dumps(dict(model='af2ig',name='team14-her2-design-pose-consistency',
        params={'output_format':'cif','write_pae':True},targets=targets),indent=2))
    (RUN/'initial-guess-input-receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
