"""Inspect generated chains by sequence identity, not assumed output chain letters."""
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from biotite.structure.io.pdbx import CIFFile
from immunum import Annotator

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "runs/011-codex-denovo-vhh"
TARGET = ''.join((ROOT/'review/denovo/her2_pilot_target.fasta').read_text().splitlines()[1:])
EPITOPE = set(json.loads((ROOT/'review/denovo/target_preparation.json').read_text())['reference_epitope_pilot_indices'])
AA = dict(zip("ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL".split(),"ARNDCQEGHILKMFPSTWYV"))


def coordinates(path):
    tab = next(iter(CIFFile.read(path).values()))['atom_site']
    col = lambda key,dtype=str:tab[key].as_array(dtype)
    mask = (col('label_atom_id')=='CA') & (col('pdbx_PDB_model_num',int)==1)
    chains={}
    for c in set(col('label_asym_id')[mask]):
        cmask=mask&(col('label_asym_id')==c)
        ids=col('label_seq_id',int)[cmask]
        names=col('label_comp_id')[cmask]
        if len(set(ids)) != len(ids):raise ValueError('Ambiguous residue IDs')
        chains[str(c)]={'sequence':''.join(AA[a] for a in names),'ids':ids.tolist()}
    heavy=(col('pdbx_PDB_model_num',int)==1)&~np.isin(col('type_symbol'),['H','D'])&(col('occupancy',float)>0)
    return chains,(col('label_asym_id')[heavy],col('label_seq_id',int)[heavy],
                   np.column_stack([col('Cartn_'+axis,float)[heavy] for axis in 'xyz']))


def inspect(name, sequence, structure):
    chains,atoms=coordinates(structure)
    targets=[c for c,v in chains.items() if v['sequence']==TARGET]
    binders=[c for c,v in chains.items() if v['sequence']==sequence]
    if len(targets)!=1 or len(binders)!=1 or targets[0]==binders[0]:
        raise ValueError('Cannot uniquely map target and designed sequence')
    binder,target=binders[0],targets[0]
    annotator=Annotator(chains=['H','K','L'],scheme='imgt',min_confidence=.1)
    number=annotator.number(sequence)
    result={'query':name,'format':'VHH','heavy_variable':sequence,'light_variable':'',
       'length':len(sequence),'structure':str(structure.relative_to(ROOT)),
       'structure_sha256':hashlib.sha256(structure.read_bytes()).hexdigest(),
       'binder_chain':binder,'target_chain':target,'cysteines':sequence.count('C'),
       'detected_chain':number.chain,'numbering_confidence':number.confidence,
       'canonical_disulfide_cysteines':False,'official_validation':'pending'}
    if not number.error:
        result['canonical_disulfide_cysteines']=all(number.numbering.get(k)=='C' for k in ['23','104'])
        result['numbered_fraction']=(number.query_end-number.query_start+1)/len(sequence)
        result['prefix_length']=number.query_start
        result['postfix_length']=len(sequence)-number.query_end-1
    chain,pos,xyz=atoms
    ab=np.flatnonzero(chain==binder);ag=np.flatnonzero(chain==target)
    tree=cKDTree(xyz[ag]); dist,_=tree.query(xyz[ab],k=1)
    result['cross_chain_atom_pairs_under_2A']=sum(len(g) for g in tree.query_ball_point(xyz[ab],2.))
    for cutoff in [4.,4.5,5.]:
        contacted={int(pos[ag[j]]) for group in tree.query_ball_point(xyz[ab],cutoff) for j in group}
        # CIF generated target numbering is mapped explicitly to its sequence order.
        mapping=dict(zip(chains[target]['ids'],range(1,len(TARGET)+1)))
        footprint={mapping[p] for p in contacted}
        result[f'epitope_recall_{cutoff}']=len(footprint&EPITOPE)/len(EPITOPE)
        result[f'epitope_jaccard_{cutoff}']=len(footprint&EPITOPE)/len(footprint|EPITOPE)
        result[f'target_contacts_{cutoff}']=len(footprint)
    # Missing Cys is a design warning, not an invented official rejection rule.
    result['screen_status']='REVIEW_MISSING_CANONICAL_CYS' if not result['canonical_disulfide_cysteines'] else 'REVIEW_PENDING_REFOLD'
    if number.error or number.chain!='H':result['screen_status']='REJECT_LOCAL_NOT_HEAVY_DOMAIN'
    return result


def main():
    records=[]
    for directory in sorted(RUN.glob('pilot-*')):
        path=directory/'results.json'
        if not path.exists():continue
        data=json.loads(path.read_text())
        metrics_path=directory/'artifacts/all_designs_metrics.csv'
        metrics={r['id']:r for r in csv.DictReader(metrics_path.open())}
        for row in data.get('designs',[]):
            name=directory.name+'__'+row['id']
            result=inspect(name,row['designed_sequence'],directory/'artifacts'/row['structure'])
            result.update(arm='directed' if directory.name.startswith('pilot-directed') else 'unconditioned',
                source_job=data['job_id'],source_rank=row.get('final_rank'),
                model_iptm=float(row['design_to_target_iptm']),model_pae=float(row['min_design_to_target_pae']),
                provider_pass_filters=metrics[row['id']]['pass_filters']=='True',
                provider_refold_rmsd=float(metrics[row['id']]['filter_rmsd']))
            records.append(result)
    (RUN/'pilot-candidates.json').write_text(json.dumps(records,indent=2))
    if records:
        with (RUN/'pilot-candidates.csv').open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    summary={'n':len(records),'by_arm':dict(Counter(r['arm'] for r in records)),
        'detected_chain':dict(Counter(r['detected_chain'] for r in records)),
        'canonical_disulfide_cysteines':sum(r['canonical_disulfide_cysteines'] for r in records),
        'provider_filter_passes':{arm:sum(r['provider_pass_filters'] for r in records if r['arm']==arm)
                                 for arm in ['directed','unconditioned']},
        'screen_status':dict(Counter(r['screen_status'] for r in records))}
    (RUN/'pilot-summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
