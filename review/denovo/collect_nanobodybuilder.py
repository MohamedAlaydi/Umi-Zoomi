"""Inspect hash-verified NanoBodyBuilder2 ensembles, keeping uncertainty units explicit."""
import hashlib
import json
import re
import numpy as np
from biotite.structure.io.pdb import PDBFile
from immunum import Annotator,regions_for
from collect_campaign import ROOT,RUN,AA
from collect_refolds import ca,align


def rmsd(a,b,fit_indices=None):
    r,o=align(a if fit_indices is None else a[fit_indices],b if fit_indices is None else b[fit_indices])
    return np.sqrt(np.sum((a@r+o-b)**2,axis=1))


def main():
    manifest=json.loads((RUN/'nanobodybuilder-inputs.json').read_text())
    candidates={r['query']:r for r in json.loads((RUN/'local-candidates.json').read_text())}
    results=[]
    for entry in manifest:
        folder=RUN/('nanobodybuilder2-'+entry['name'])
        native=json.loads((folder/'result.json').read_text())
        if native.get('status')!='succeeded':continue
        paths={hashlib.sha256(p.read_bytes()).hexdigest():p for p in folder.iterdir() if p.is_file()}
        metadata_path=paths[native['native_result']['files'][0]['file']['sha256']]
        metadata=json.loads(metadata_path.read_text());candidate=candidates[entry['candidate']]
        seq=candidate['heavy_variable'];ann=Annotator(chains=['H'],scheme='imgt').number(seq)
        domain=''.join(ann.numbering.values());assert domain==seq
        regionmap=regions_for('imgt','H');indices={'framework':[],'cdr1':[],'cdr2':[],'cdr3':[]}
        for i,label in enumerate(ann.numbering):
            pos=int(re.match(r'\d+',label).group());region=next((r for r in ['cdr1','cdr2','cdr3'] if regionmap[r][0]<=pos<=regionmap[r][1]),'framework')
            indices[region].append(i)
        design_ca=ca(ROOT/candidate['structure'])['H'];models=[]
        for filename,detail in metadata['files'].items():
            if not filename.endswith('.pdb'):continue
            path=paths[detail['sha256']]
            atoms=PDBFile.read(path).get_structure(model=1,extra_fields=['b_factor'])
            alpha=atoms[atoms.atom_name=='CA'];modelseq=''.join(AA[a] for a in alpha.res_name)
            assert modelseq==seq, 'NBB2 selected domain differs from exact design'
            errors=rmsd(alpha.coord,design_ca,indices['framework'])
            sg=atoms[(atoms.res_name=='CYS')&(atoms.atom_name=='SG')]
            distance=float(np.linalg.norm(sg.coord[0]-sg.coord[1])) if len(sg)==2 else None
            models.append(dict(native_file=filename,path=str(path.relative_to(ROOT)),sha256=detail['sha256'],
                all_CA_rmsd_after_self_fit=float(np.sqrt(np.mean(rmsd(alpha.coord,design_ca)**2))),
                CA_rmsd_after_framework_fit={r:float(np.sqrt(np.mean(errors[idx]**2))) for r,idx in indices.items()},
                cysteine_SG_distance=distance,
                native_B_factor_mean=float(np.mean(alpha.b_factor)),
                B_factor_interpretation='Native ensemble coordinate uncertainty; not pLDDT and not temperature stability'))
        results.append(dict(name=entry['name'],candidate=entry['candidate'],operation_id=native['operation_id'],
            model_version=metadata['model_version'],source_revision=metadata['source_revision'],
            checkpoint_sha256=metadata['checkpoint_sha256'],exact_sequence_verified=True,models=models,
            scope='Monomer sequence-fold consistency only. No antigen, measured affinity, competition or Tm.'))
    (RUN/'nanobodybuilder-evidence.json').write_text(json.dumps(results,indent=2))
    print(json.dumps([dict(name=r['name'],candidate=r['candidate'],models=[
        {'file':m['native_file'],'rmsd':m['all_CA_rmsd_after_self_fit'],'regions':m['CA_rmsd_after_framework_fit'],
        'SG':m['cysteine_SG_distance']} for m in r['models']]) for r in results],indent=2))

if __name__=='__main__':main()
