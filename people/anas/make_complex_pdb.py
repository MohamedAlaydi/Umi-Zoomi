#!/usr/bin/env python3
"""Write the 1N8Z Fv-HER2 complex as a PDB for StaB-ddG, and verify the mutation sites.

StaB-ddG takes one wild-type PDB plus typed partner sets and variants. The contract
requires that wild_type matches the structure and that every mutation site carries
N/CA/C/O, so this checks both before anything is uploaded.

  py people/anas/make_complex_pdb.py /tmp/complex.pdb
"""
from __future__ import annotations

import sys

import numpy as np
import biotite.structure as struc
import biotite.structure.io.pdb as pdb
import biotite.structure.io.pdbx as pdbx

CIF = "/home/hackathon/team14/data/rfd4-proteina/docs/Data/12-her2/her2_fv_1n8z.cif"
WT_CDRH3 = "WGGDGFYAMD"
CDR_FROM, CDR_TO = 99, 108
BACKBONE = {"N", "CA", "C", "O"}

THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
    "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
    "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
    "TYR": "Y", "VAL": "V",
}


def main() -> int:
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/complex.pdb"

    arr = pdbx.get_structure(pdbx.CIFFile.read(CIF), model=1)
    arr = arr[struc.filter_amino_acids(arr) & (arr.element != "H")]
    print(f"kept {arr.array_length()} heavy protein atoms, chains {sorted(set(arr.chain_id))}")

    for ch in sorted(set(arr.chain_id)):
        m = arr.chain_id == ch
        ids = np.unique(arr.res_id[m])
        seq = "".join(THREE_TO_ONE.get(arr.res_name[m][arr.res_id[m] == i][0], "X") for i in ids)
        print(f"  chain {ch}: {len(ids)} residues, {ids.min()}-{ids.max()}")
        if ch == "B":
            vh = seq
    cdr = "".join(
        THREE_TO_ONE.get(arr.res_name[(arr.chain_id == "B") & (arr.res_id == i)][0], "X")
        for i in range(CDR_FROM, CDR_TO + 1)
    )
    print(f"\nchain B {CDR_FROM}-{CDR_TO}: {cdr}")
    if cdr != WT_CDRH3:
        sys.exit(f"MISMATCH: expected {WT_CDRH3}, structure has {cdr}. Do not submit.")
    print("matches trastuzumab's CDRH3")

    missing = []
    for i in range(CDR_FROM, CDR_TO + 1):
        m = (arr.chain_id == "B") & (arr.res_id == i)
        have = set(arr.atom_name[m])
        if not BACKBONE <= have:
            missing.append((i, sorted(BACKBONE - have)))
    if missing:
        sys.exit(f"missing backbone atoms: {missing}. Do not submit.")
    print(f"all {CDR_TO - CDR_FROM + 1} sites carry N/CA/C/O")

    f = pdb.PDBFile()
    f.set_structure(arr)
    f.write(out)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
