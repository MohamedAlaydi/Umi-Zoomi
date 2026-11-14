"""Reuse the official annotated VHH scaffold with the verified HER2 coordinate crop."""
import hashlib
import json
from pathlib import Path
import numpy as np
from biotite.structure.io.pdbx import CIFFile, CIFBlock, CIFCategory

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "runs/011-codex-denovo-vhh"
INPUT = RUN / "rfd4-antibody-her2"
SOURCE = ROOT / "data/rfd4-proteina/docs/Data/12-her2/her2_fv_1n8z.cif"


def main():
    INPUT.mkdir(exist_ok=True)
    original = next(iter(CIFFile.read(SOURCE).values()))
    atoms = original["atom_site"]
    mask = np.isin(atoms["label_asym_id"].as_array(str), ["C", "D"])
    entity_ids = set(atoms["label_entity_id"].as_array(str)[mask])
    block = CIFBlock()
    block["atom_site"] = CIFCategory({k:atoms[k].as_array(str)[mask] for k in atoms})
    for name, field in [("entity", "id"), ("entity_poly", "entity_id"),
                        ("entity_poly_seq", "entity_id"), ("struct_asym", "entity_id")]:
        if name in original:
            category = original[name]
            keep = np.isin(category[field].as_array(str), list(entity_ids))
            block[name] = CIFCategory({k:category[k].as_array(str)[keep] for k in category})
    for name in ("chem_comp", "chem_comp_atom", "chem_comp_bond"):
        if name in original:
            block[name] = original[name]
    output = CIFFile()
    output["her2_reference_crop"] = block
    output.write(INPUT / "her2-target.cif")
    spec = {"her2_caplacizumab_cdr123": {
        "input": ["../caplacizumab-example.cif", "her2-target.cif"],
        "input_as_annotated_cif": True,
        "contig": "H1-86, /0, C489-580, /0, D591-607",
        "conditions": {
            "C_CRDGRP": {
                "1": [{"select": "sel('H/*/[1-22,24-37,39-75,77-86]') and not has_nan_coord()"}],
                "2": [{"select": "sel('C/*/*/[N,CA,C,O]') and not has_nan_coord()"},
                      {"select": "sel('D/*/*/[N,CA,C,O]') and not has_nan_coord()"}]},
            "C_SEQ": {"true": [{"select": "sel('H/*/[1-22,24-37,39-75,77-86]')"},
                                  {"select": "sel('C')"}, {"select": "sel('D')"}]},
            "C_HOT": {"true": [{"select": "sel('D/*/593/NZ')"}, {"select": "sel('C/*/573/CD1')"},
                                  {"select": "sel('D/*/591/CG2')"}, {"select": "sel('C/*/572/CD')"}]},
            "C_CATH": {"2.60.40": [{"select": "sel('H')"}]}
        }}}
    (INPUT / "design.json").write_text(json.dumps(spec,indent=2))
    receipt = {"source_her2_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "source_framework":"Official Data/03-vhh/pmvk_caplacizumab.cif.zst; annotated H chain only; original PMVK chain A dropped by contig",
        "scaffold_sha256":hashlib.sha256((RUN/'caplacizumab-example.cif').read_bytes()).hexdigest(),
        "preserved_framework_compressed_positions":"H1-22,H24-37,H39-75,H77-86",
        "designed_loops":"Official expandable segments H23 length13; H38 length9-10; H76 length12-21",
        "epitope":"Same four atom hotspots as organiser HER2 task; target fragments held as one rigid group",
        "official_track":"UNVERIFIED; fixed known framework does not imply de novo eligibility",
        "target_atom_count":int(mask.sum())}
    (INPUT / "preparation.json").write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt,indent=2))


if __name__ == "__main__":
    main()
