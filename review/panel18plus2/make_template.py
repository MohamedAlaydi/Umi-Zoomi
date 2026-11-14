"""Export a HER2-only mmCIF template with observed coordinates and native residue numbering."""
import argparse
import json
from pathlib import Path
import numpy as np
from biotite.structure.io.pdbx import CIFBlock, CIFCategory, CIFFile

AA = dict(zip('ACDEFGHIKLMNPQRSTVWY','ALA CYS ASP GLU PHE GLY HIS ILE LYS LEU MET ASN PRO GLN ARG SER THR VAL TRP TYR'.split(),strict=True))


def make(run, output):
    original = next(iter(CIFFile.read(run/'native_template.cif').values()))['atom_site']
    q = json.loads((run/'queries.json').read_text())['queries']
    seq, = {chain['sequence'] for entry in q for chain in entry['chains'] if chain['chain_id']=='T'}
    select = np.isin(original['auth_asym_id'].as_array(str),['C','D'])
    columns = {k: col.as_array(str)[select] for k,col in original.items()}
    n = len(columns['id'])
    pos = columns['auth_seq_id'].astype(int)
    columns.update(label_asym_id=['T']*n, auth_asym_id=['T']*n, label_entity_id=['1']*n,
                   label_seq_id=pos-488, id=np.arange(1,n+1))
    ca = np.asarray(columns['label_atom_id'])=='CA'
    assert set(pos[ca]) == set(range(489,581)) | set(range(591,608))
    assert all(AA[seq[p-489]]==name for p,name in zip(pos,columns['label_comp_id'],strict=True))
    block = CIFBlock()
    block['entity'] = CIFCategory({'id':['1'],'type':['polymer'],'pdbx_description':['HER2']})
    block['entity_poly'] = CIFCategory({'entity_id':['1'],'type':['polypeptide(L)'],'pdbx_seq_one_letter_code':[seq],
                                        'pdbx_seq_one_letter_code_can':[seq],'pdbx_strand_id':['T']})
    block['struct_asym'] = CIFCategory({'id':['T'],'entity_id':['1']})
    block['entity_poly_seq'] = CIFCategory({'entity_id':['1']*len(seq),'num':np.arange(1,len(seq)+1),
                                             'mon_id':[AA[a] for a in seq],'hetero':['n']*len(seq)})
    block['atom_site'] = CIFCategory(columns)
    result = CIFFile(); result['her2'] = block; result.write(output)
    check = next(iter(CIFFile.read(output).values()))['atom_site']
    for col in ['Cartn_x','Cartn_y','Cartn_z','auth_seq_id','label_comp_id','label_atom_id']:
        assert np.array_equal(check[col].as_array(str),original[col].as_array(str)[select])


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    make(args.run,args.output)
