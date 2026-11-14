import unittest
import numpy as np
from geometry import fit,map_roles,interface_pae,native_reference


class GeometryTests(unittest.TestCase):
 def test_chain_roles_follow_sequence_under_permutation(self):
  chains={'renamed3':{'sequence':'TARGET'},'renamed1':{'sequence':'HEAVY'},'renamed2':{'sequence':'LIGHT'}}
  self.assertEqual(map_roles(chains,{'L':'LIGHT','T':'TARGET','H':'HEAVY'}),{'L':'renamed2','T':'renamed3','H':'renamed1'})
  with self.assertRaises(ValueError):map_roles({**chains,'duplicate':{'sequence':'HEAVY'}},{'H':'HEAVY','L':'LIGHT','T':'TARGET'})
 def test_alignment_recovers_rotation_and_translation(self):
  x=np.array([[0.,0,0],[1,0,0],[0,1,0],[0,0,1]]);r=np.array([[0.,-1,0],[1,0,0],[0,0,1]])
  rot,off,rmsd=fit(x,x@r+[4,8,2]);self.assertLess(rmsd,1e-10);self.assertGreater(np.linalg.det(rot),.999)
 def test_mirror_cannot_be_hidden_by_alignment(self):
  x=np.array([[0.,0,0],[1,0,0],[0,1,0],[0,0,1]]);y=x*np.array([-1,1,1])
  self.assertGreater(fit(x,y)[2],.1)
 def test_pae_is_symmetric_per_residue_pair_and_empty_is_missing(self):
  a,b=('H',9),('T',14);tokens={a:1,b:0};pae=np.array([[0.,8.],[4.,0.]])
  self.assertEqual(interface_pae({(a,b)},tokens,pae),6.)
  self.assertIsNone(interface_pae(set(),tokens,pae))
  with self.assertRaises(ValueError):interface_pae({(a,b)},tokens,np.zeros((3,3)))
 def test_experimental_reference_footprint_is_recomputed(self):
  native,fp,digest=native_reference();self.assertEqual(len(fp['4.5']),19)
  self.assertEqual(len(native['chains']['C']['ids']),581);self.assertEqual(len(digest),64)

if __name__=='__main__':unittest.main()
