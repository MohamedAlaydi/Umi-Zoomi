# What the second model actually returned

These are docking predictions, not binding measurements.

| Design | Mol1: known-site contacts | OpenDDE: known-site contacts |
|---|---:|---:|
| Trastuzumab control |19/19|2/19|
| Pick01 |19/19|15/19|
| Pick02 |19/19|0/19|
| Pick03 |19/19|Not delivered|
| Pick04 |19/19|18/19|

For Pick02, OpenDDE predicted contact with21 different HER2 residues outside the19-residue reference site. Zero here means zero overlap with that site, not zero contact with HER2 and not a measured failure to bind.

For Pick03, the original OpenDDE job reported an internal device error for the structure. The retry job also failed. A missing result has no biological interpretation.

OpenDDE recovered only2 of19 reference-site residues for trastuzumab. Because the positive control is weak, its negative docking predictions are inconclusive. The main results figure therefore presents Mol1 site recovery, with the second-model limitation explicitly noted. The complete comparison is retained in MODEL_CONTROL.svg and MODEL_CONTROL.png.

All four Mol1 predictions recover the19 native site residues. This is contact recall: it does not require every predicted contact to match the native interface, and it cannot rank binding strength or establish competition or thermal stability.
