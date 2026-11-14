import importlib.util,sys,unittest,io,contextlib,tempfile,json
from unittest.mock import patch
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import novelty
from multiseed_analysis import noninferiority_supported


class RegressionTests(unittest.TestCase):
 def test_same_length_shift_is_two_edits_not_ten_substitutions(self):
  pool={10:novelty._encode(['CDEFGHIKLA'])}
  self.assertEqual(novelty.min_distance('ACDEFGHIKL',pool),(2,'CDEFGHIKLA'))
 def test_different_lengths_and_equal_match(self):
  pool={9:novelty._encode(['ACDEFGHIK']),10:novelty._encode(['YYYYYYYYYY'])}
  self.assertEqual(novelty.min_distance('ACDEFGHIKL',pool),(1,'ACDEFGHIK'))
  self.assertEqual(novelty.min_distance('YYYYYYYYYY',pool),(0,'YYYYYYYYYY'))
 def test_upper_bound_cannot_establish_noninferiority(self):
  self.assertFalse(noninferiority_supported(-.08,-.03)) # CI [-.08,+.02] is inconclusive
  self.assertTrue(noninferiority_supported(-.02,-.03))
  self.assertFalse(noninferiority_supported(float('nan'),-.03))
 def test_reference_empty_is_not_a_passing_distance(self):
  with self.assertRaises(ValueError):novelty.min_distance('ACDEFGHIKL',{})
 def test_numeric_cli_uses_strict_PDF_boundaries(self):
  for distance,identity,expected in [(2,60.,1),(3,70.,1),(3,69.,0)]:
   with patch.object(novelty,'load',return_value={10:novelty._encode(['ACDEFGHIKL'])}),patch.object(novelty,'min_distance',return_value=(distance,'ACDEFGHIKL')),patch.object(novelty,'identity_to_trastuzumab',return_value=identity),contextlib.redirect_stdout(io.StringIO()):
    self.assertEqual(novelty.check(['WGGDGFYAMD']),expected)
 def test_collector_rejects_ambiguous_seeds(self):
  spec=importlib.util.spec_from_file_location('tested_collect_refold',ROOT/'people/anas/collect_refold.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  with tempfile.TemporaryDirectory() as tmp:
   run=Path(tmp)/'runs/demo';run.mkdir(parents=True);(run/'manifest.csv').write_text('query_id,cdrh3,p_high,n_mut,source\ncandidate,WGGDGFYAMD,.9,4,test\n')
   for seed in [1,42]:
    folder=run/f'out/boltz2/candidate/seed_{seed}';folder.mkdir(parents=True);(folder/'x_scores.json').write_text('{}')
   with patch.object(mod,'HOME',tmp),patch.object(sys,'argv',['collect_refold.py','demo']):
    with self.assertRaisesRegex(SystemExit,'select --seed'):mod.main()

if __name__=='__main__':unittest.main()
