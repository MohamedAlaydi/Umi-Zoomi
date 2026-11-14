"""Regression tests for role-specific interface PAE and absent-contact semantics."""
import json,sys,tempfile,unittest
from pathlib import Path
import numpy as np
from biotite.structure.io.pdbx import CIFBlock,CIFCategory,CIFFile
sys.path.insert(0,str(Path(__file__).resolve().parent))
from collect import contact_pae


class ContactTests(unittest.TestCase):
    def fixture(self,path,distance):
        # Antigen first, antibody second: role mapping cannot rely on chain order.
        n=4;block=CIFBlock();block['atom_site']=CIFCategory(dict(label_atom_id=['CA']*n,
            label_comp_id=['ALA','ALA','GLY','GLY'],label_asym_id=['Z','Z','X','X'],
            label_seq_id=[8,9,21,22],pdbx_PDB_model_num=[1]*n,type_symbol=['C']*n,occupancy=[1]*n,
            Cartn_x=[0,30,distance,70],Cartn_y=[0]*n,Cartn_z=[0]*n))
        cif=CIFFile();cif['test']=block;cif.write(path)
        matrix=np.full((4,4),99.);matrix[0,2]=4.;matrix[2,0]=8.
        np.savez(path.with_name('test_pae.npz'),pae=matrix)
        path.with_name('test_pae.json').write_text(json.dumps(dict(n_tokens=4,token_order='tokens of the written structure, in file order',arrays={'pae':{'units':'angstrom'}})))

    def test_antigen_first_nonsequential_ids_map_to_one_symmetric_contact(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'test.cif';self.fixture(path,3.)
            result=contact_pae(path,{'H':'X','T':'Z'})
        self.assertEqual(result['contact_residue_pairs_4_5'],1)
        self.assertEqual(result['mean_contact_pair_symmetric_PAE_A'],6.)

    def test_missing_interface_is_unknown_not_zero_error(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'test.cif';self.fixture(path,15.)
            result=contact_pae(path,{'H':'X','T':'Z'})
        self.assertEqual(result['contact_residue_pairs_4_5'],0)
        self.assertIsNone(result['mean_contact_pair_symmetric_PAE_A'])


if __name__=='__main__':unittest.main()
