"""Check local antibody-model designs, preserving the split-antigen residue map."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from biotite.structure.io.pdbx import CIFFile
from immunum import Annotator
from collect_campaign import coordinates, AA, EPITOPE, ROOT, RUN, TARGET


def rmsd_rigid(a,b):
    a=a-a.mean(axis=0);b=b-b.mean(axis=0)
    u,_,vt=np.linalg.svd(a.T@b)
    rotation=u@np.diag([1,1,np.linalg.det(u@vt)])@vt
    return float(np.sqrt(np.mean(np.sum((a@rotation-b)**2,axis=1))))


def ca_target(path):
    tab=next(iter(CIFFile.read(path).values()))['atom_site']
    col=lambda n,d=str:tab[n].as_array(d)
    mask=(col('label_atom_id')=='CA')&(col('pdbx_PDB_model_num',int)==1)
    xyz=np.column_stack([col('Cartn_'+a,float) for a in 'xyz'])
    return np.concatenate([xyz[mask&(col('label_asym_id')==c)] for c in ['C','D']])


def inspect_local(path,arm,metrics,reference):
    chains,atoms=coordinates(path)
    if set(chains)!={'H','C','D'}:raise ValueError('Unexpected local design chain set')
    if chains['C']['sequence']!=TARGET[:92] or chains['D']['sequence']!=TARGET[102:]:
        raise ValueError('Antigen changed; cannot compare footprint')
    sequence=chains['H']['sequence']
    number=Annotator(chains=['H','K','L'],scheme='imgt',min_confidence=.1).number(sequence)
    regions=Annotator(chains=['H'],scheme='imgt',min_confidence=.1).segment(sequence)
    chain,pos,xyz=atoms
    ab=np.flatnonzero(chain=='H');ag=np.flatnonzero(np.isin(chain,['C','D']))
    tree=cKDTree(xyz[ag]);footprints={}
    for cutoff in [4.,4.5,5.]:
        footprint={int(pos[ag[j]])+(0 if chain[ag[j]]=='C' else 102)
                   for group in tree.query_ball_point(xyz[ab],cutoff) for j in group}
        footprints[str(cutoff)]={'recall':len(footprint&EPITOPE)/19,
            'jaccard':len(footprint&EPITOPE)/len(footprint|EPITOPE),'n_target_residues':len(footprint)}
    canonical=not number.error and all(number.numbering.get(k)=='C' for k in ['23','104'])
    query=(arm+'__'+path.stem) if arm.startswith('rfd4-variable-sequence') else path.stem
    return dict(query=query,generation_id=path.stem,source_arm=arm,format='VHH',heavy_variable=sequence,light_variable='',
        length=len(sequence),numbering_confidence=number.confidence,detected_chain=number.chain,
        canonical_cysteines=canonical,cysteine_count=sequence.count('C'),cdrh3_imgt=regions.cdr3,
        footprint=footprints,cross_chain_pairs_under_2A=sum(len(x) for x in tree.query_ball_point(xyz[ab],2.)),
        antigen_rigid_rmsd=rmsd_rigid(ca_target(path),reference),
        hotspot_obedience=metrics.get('hotspot_obedience.hotspot_obedience'),
        sequence_adherence=metrics.get('sequence_adherence.sequence_adherence'),
        requested_seed=20261114,recorded_seed=metrics.get('seed'),
        checkpoint=metrics.get('ckpt_name'),structure=str(path.relative_to(ROOT)),
        structure_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        sequence_sha256=hashlib.sha256(sequence.encode()).hexdigest(),official_validation='pending')


def main():
    reference=ca_target(ROOT/'data/rfd4-proteina/docs/Data/12-her2/her2_fv_1n8z.cif')
    rows=[]
    for arm in ['rfd4-antibody-her2','rfd4-antibody-her2-longH3',
                'rfd4-variable-sequence-k1','rfd4-variable-sequence-k2']:
        folder=RUN/arm/'design'
        path=folder/'generation/inference_metrics/per_example_metrics.csv'
        if not path.exists():continue
        metrics={r['example_id']:r for r in csv.DictReader(path.open())}
        for structure in sorted(folder.rglob('*generated.cif')):
            example=structure.stem.removesuffix('_generated')
            if example not in metrics:continue # preserve incomplete generation until metric receipt exists
            rows.append(inspect_local(structure,arm,metrics[example],reference))
    if len({row['query'] for row in rows})!=len(rows):
        raise ValueError('Duplicate candidate IDs across generation arms')
    (RUN/'local-candidates.json').write_text(json.dumps(rows,indent=2))
    if rows:
        with (RUN/'local-candidates.csv').open('w',newline='') as handle:
            fields=[k for k in rows[0] if k!='footprint']+['epitope_recall_4_5','epitope_jaccard_4_5']
            writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader()
            for row in rows:
                writer.writerow({**{k:v for k,v in row.items() if k!='footprint'},
                    'epitope_recall_4_5':row['footprint']['4.5']['recall'],
                    'epitope_jaccard_4_5':row['footprint']['4.5']['jaccard']})
    print(json.dumps({'n':len(rows),'numbered_H':sum(r['detected_chain']=='H' for r in rows),
          'canonical_cysteines':sum(r['canonical_cysteines'] for r in rows),
          'max_antigen_rigid_rmsd':max((r['antigen_rigid_rmsd'] for r in rows),default=None)},indent=2))


if __name__=='__main__':main()
