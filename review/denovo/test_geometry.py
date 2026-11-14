"""Regression checks for rigid superposition and the AF2-IG input contract."""
import tempfile,unittest
from pathlib import Path
import numpy as np
from biotite.structure.io.pdbx import CIFFile,get_structure
from collect_refolds import align
from prepare_initial_guess import compact_cif


class GeometryTests(unittest.TestCase):
    def test_superposition_is_rigid_and_preserves_chirality(self):
        a=np.array([[0.,0.,0.],[1.,0.,0.],[0.,2.,0.],[0.,0.,3.]])
        rotation=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
        b=a@rotation+np.array([3.,-2.,1.]);r,o=align(a,b)
        np.testing.assert_allclose(a@r+o,b,atol=1e-12)
        self.assertAlmostEqual(np.linalg.det(r),1.)
        reflected=a*np.array([-1.,1.,1.]);r,o=align(a,reflected)
        self.assertGreater(np.linalg.norm(a@r+o-reflected),.1)

    def test_compact_structure_preserves_backbone_and_required_insertion_field(self):
        atoms=[('H',name,'ALA',1,np.array([x,0.,0.])) for name,x in [('N',0.),('CA',1.4),('C',2.8),('O',3.7)]]
        content=compact_cif(atoms)
        self.assertIn('_atom_site.pdbx_PDB_ins_code',content)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'backbone.cif';p.write_text(content)
            structure=get_structure(CIFFile.read(p),model=1,use_author_fields=False)
        self.assertEqual(list(structure.atom_name),['N','CA','C','O'])
        np.testing.assert_allclose(structure.coord[:,0],[0,1.4,2.8,3.7],atol=1e-6)


if __name__=='__main__':unittest.main()
