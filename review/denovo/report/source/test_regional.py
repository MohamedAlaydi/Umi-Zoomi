import tempfile
import unittest
from pathlib import Path
import numpy as np
from biotite.structure.io.pdbx import CIFFile,CIFBlock,CIFCategory
from regional_confidence import confidence,AA


class RegionalTests(unittest.TestCase):
    def test_framework_average_excludes_cdrs_and_antigen_confidence(self):
        # Trastuzumab VH IMGT: FR lengths25/17/38/11; CDR lengths8/8/13.
        seq='EVQLVESGGGLVQPGGSLRLSCAASGFNIKDTYIHWVRQAPGKGLEWVARIYPTNGYTRYADSVKGRFTISADTSKNTAYLQMNSLRAEDTAVYYCSRWGGDGFYAMDYWGQGTLVTVSS'
        levels=sum(([.9]*fr+[.2]*cdr for fr,cdr in [(25,8),(17,8),(38,13),(11,0)]),[])
        self.assertEqual(len(levels),len(seq))
        three={v:k for k,v in AA.items()}
        block=CIFBlock();n=len(seq)+1
        block['atom_site']=CIFCategory({'label_atom_id':['CA']*n,
            'label_comp_id':[three[a] for a in seq]+['ALA'],
            'auth_asym_id':['H']*len(seq)+['T'],'pdbx_PDB_model_num':['1']*n,
            'B_iso_or_equiv':[100*x for x in levels]+[1.]})
        cif=CIFFile();cif['test']=block
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'confidence.cif';cif.write(path);result=confidence(path,['H'])
        self.assertAlmostEqual(result['ca_nac'],.9)
        self.assertAlmostEqual(result['cdr_ca_plddt'],.2)
        self.assertEqual(result['chains']['H']['n_framework'],91)
        self.assertEqual(result['chains']['H']['n_cdr'],29)

    def test_ambiguous_confidence_units_are_rejected(self):
        block=CIFBlock();block['atom_site']=CIFCategory({'label_atom_id':['CA'],
            'label_comp_id':['ALA'],'auth_asym_id':['H'],'pdbx_PDB_model_num':['1'],
            'B_iso_or_equiv':[.9]})
        cif=CIFFile();cif['test']=block
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'confidence.cif';cif.write(path)
            with self.assertRaisesRegex(ValueError,'scale'):
                confidence(path,['H'])


if __name__=='__main__':unittest.main()
