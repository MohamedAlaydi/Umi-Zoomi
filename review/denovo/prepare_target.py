"""Prepare a native-sequence pilot target, without inventing missing coordinates."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from biotite.structure.io.pdbx import CIFFile
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REFERENCE = ROOT / "data/rfd4-proteina/docs/Data/12-her2/her2_fv_1n8z.cif"
MAPPING = HERE / "rcsb_1n8z_her2_mapping.json"
AA = dict(zip("ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL".split(),
              "ARNDCQEGHILKMFPSTWYV"))


def main():
    mapping = json.loads(MAPPING.read_text())
    sequence = mapping["query_sequence"]
    alignment = mapping["target_alignments"][0]
    region = alignment["aligned_regions"]
    if alignment["target_id"] != "P04626" or region != [dict(query_begin=1,query_end=607,
            target_begin=23,target_end=629,exon_shift=None)]:
        raise ValueError("Revisit the HER2 residue map before preparing inputs")
    block = next(iter(CIFFile.read(REFERENCE).values()))
    tab = block["atom_site"]
    col = lambda name, dtype=str: tab[name].as_array(dtype)
    chain, position = col("auth_asym_id"), col("auth_seq_id", int)
    atom = (col("group_PDB") == "ATOM") & (col("pdbx_PDB_model_num", int) == 1)
    ca = atom & (col("label_atom_id") == "CA") & np.isin(chain, ["C", "D"])
    resolved = {}
    for cid, pos, name in zip(chain[ca], position[ca], col("auth_comp_id")[ca]):
        if sequence[pos - 1] != AA[name]:
            raise ValueError(f"Local coordinate/sequence mapping disagrees at {cid}:{pos}")
        resolved[int(pos)] = str(cid)
    if len(resolved) != 109:
        raise ValueError("Reference crop changed; check intended antigen extent")
    xyz = np.column_stack([col("Cartn_" + ax, float) for ax in "xyz"])
    heavy = atom & ~np.isin(col("type_symbol"), ["H", "D"]) & (col("occupancy", float) > 0)
    antibody = heavy & np.isin(chain, ["A", "B"])
    antigen = heavy & np.isin(chain, ["C", "D"])
    ag_indices = np.flatnonzero(antigen)
    hits = cKDTree(xyz[antigen]).query_ball_point(xyz[antibody], 4.5)
    footprint = {int(position[ag_indices[j]]) for group in hits for j in group}
    if len(footprint) != 19:
        raise ValueError("Reference contact definition changed")
    # Explicit proposal: the original coordinate crop's native sequence span.
    # The ten unresolved residues receive sequence only, no artificial coordinates.
    begin, end = min(resolved), max(resolved)
    target = sequence[begin - 1:end]
    (HERE / "her2_pilot_target.fasta").write_text(
        f">HER2_1N8Z_entity3_{begin}_{end}_UniProt_P04626_{begin+22}_{end+22}\n{target}\n")
    with (HERE / "her2_pilot_residue_map.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["pilot_index_1based", "residue", "pdb_entity_position",
                                  "uniprot_position", "reference_auth_chain", "reference_resolved",
                                  "reference_contact_4_5A"])
        writer.writeheader()
        for index, pos in enumerate(range(begin, end + 1), 1):
            writer.writerow(dict(pilot_index_1based=index, residue=sequence[pos-1],
                pdb_entity_position=pos, uniprot_position=pos+22,
                reference_auth_chain=resolved.get(pos, ""), reference_resolved=pos in resolved,
                reference_contact_4_5A=pos in footprint))
    result = dict(source="RCSB 1N8Z_3 -> UniProt P04626", pilot_length=len(target),
        source_coordinate_sha256=hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
        source_mapping_sha256=hashlib.sha256(MAPPING.read_bytes()).hexdigest(),
        matched_coordinate_residues=len(resolved),
        unresolved_positions=[p for p in range(begin,end+1) if p not in resolved],
        reference_epitope_entity_positions=sorted(footprint),
        reference_epitope_pilot_indices=[p-begin+1 for p in sorted(footprint)],
        scope="native sequence pilot only; no missing coordinates reconstructed; context/glycan checks pending")
    (HERE / "target_preparation.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
