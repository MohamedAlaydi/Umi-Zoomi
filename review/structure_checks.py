"""Recompute chain-specific scores, reference footprints and eligibility-screen counts."""
import csv
import json
import re
import sys
from collections import Counter

import numpy as np
from biotite.structure.io.pdbx import CIFFile
from scipy.spatial import cKDTree

from assay_transfer import ROOT, WT, blosum_scores, sha256
sys.path.insert(0, str(ROOT / "scripts"))
import novelty
from contacts import THREE_TO_ONE

RUNS = ROOT / "runs"
REFERENCE = ROOT / "data/rfd4-proteina/docs/Data/12-her2/her2_fv_1n8z.cif"
REFERENCE_SPR = ROOT / "data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv"
CHAINS = {"A", "B", "C", "D"}
CUTOFFS = (4., 4.5, 5.)


def rows(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def unique_rows(items, field):
    result = {r[field]:r for r in items}
    if len(result) != len(items):
        raise ValueError(f"Duplicate {field}")
    return result


def atom_data(block):
    tab = block["atom_site"]
    def col(name, dtype=str):
        return tab[name].as_array(dtype)
    mask = ((col("group_PDB") == "ATOM") & ~np.isin(col("type_symbol"), ["H","D"])
            & (col("occupancy", float) > 0) & (col("pdbx_PDB_model_num", int) == 1))
    if not np.isin(col("label_alt_id")[mask], [".", "?", "A"]).all():
        raise ValueError("Resolve alternate conformers before comparing these structures")
    chain = col("auth_asym_id")[mask]
    if set(chain) != CHAINS:
        raise ValueError("Incomplete or unexpected coordinate chain set")
    positions = col("auth_seq_id", int)[mask]
    coords = np.column_stack([col("Cartn_"+v, float)[mask] for v in "xyz"])
    residues = {}
    ca = mask & (col("label_atom_id") == "CA")
    for cid,pos,aa in zip(col("auth_asym_id")[ca],col("auth_seq_id",int)[ca],col("auth_comp_id")[ca]):
        if int(pos) in residues.setdefault(str(cid),{}):
            raise ValueError("Ambiguous residue ID")
        residues[str(cid)][int(pos)] = THREE_TO_ONE[str(aa)]
    return (chain, positions, coords), residues


def footprint(atoms, cutoff):
    chain, pos, xyz = atoms
    ab = np.flatnonzero(np.isin(chain, ["A","B"]))
    ag = np.flatnonzero(np.isin(chain, ["C","D"]))
    hits = cKDTree(xyz[ag]).query_ball_point(xyz[ab], cutoff)
    epitope, loop = set(), set()
    for antibody_idx, target_indices in zip(ab,hits):
        for j in ag[target_indices]:
            epitope.add((str(chain[j]),int(pos[j])))
            if chain[antibody_idx] == "B" and 99 <= pos[antibody_idx] <= 108:
                loop.add(int(pos[antibody_idx]))
    return epitope, loop


def pair_scores(raw, order):
    m = np.asarray(raw, dtype=float)
    if len(order) != 4 or set(order) != CHAINS or m.shape != (4,4):
        raise ValueError("A four-chain matrix with mapped chain labels is required")
    if not np.isfinite(m).all() or (m < 0).any() or (m > 1).any():
        raise ValueError("Invalid pair confidence")
    m = (m + m.T)/2
    pairs = {a+b:float(m[order.index(a),order.index(b)]) for a in "AB" for b in "CD"}
    return dict(**pairs, VH_min=min(pairs["BC"],pairs["BD"]),
                Fv_mean=sum(pairs.values())/4)


def check_chains(chains, sequence, antibody, ref_residues):
    chain = unique_rows(chains, "chain_id")
    if set(chain) != CHAINS:
        raise ValueError("Query lacks the expected chain roles")
    expected = antibody["vh_sequence"][:98] + sequence + antibody["vh_sequence"][108:]
    if chain["A"]["sequence"] != antibody["vl_sequence"] or chain["B"]["sequence"] != expected:
        raise ValueError("Control, loop or antibody background mismatch")
    for cid in ["C","D"]:
        residues = ref_residues[cid]
        if chain[cid]["sequence"] != "".join(residues[i] for i in sorted(residues)):
            raise ValueError(f"Antigen fragment {cid} differs from reference")
        if "residue_ids" in chain[cid] and list(map(int,chain[cid]["residue_ids"])) != sorted(residues):
            raise ValueError(f"Antigen residue IDs changed for {cid}")
    return chain


def opendde_request_check(path, raw_metrics, antibody, ref_residues):
    # Parse only the simple protein-only YAML dialect actually emitted by the
    # checked-in builder. Refuse other forms instead of guessing their meaning.
    req = json.loads(path.read_text())
    baseline = unique_rows(raw_metrics, "query_id")
    targets = unique_rows(req["targets"], "name")
    if set(targets) != set(baseline) | {"trastuzumab_wt"} or req["model"] != "opendde-abag":
        raise ValueError("OpenDDE batch targets changed")
    for name,target in targets.items():
        head,*lines = target["content"].splitlines()
        if head != "sequences:":
            raise ValueError("Unexpected OpenDDE target format")
        parsed = []
        for line in lines:
            match = re.fullmatch(r"\s*- protein: \{id: ([ABCD]), sequence: ([A-Z]+)\}",line)
            if match is None:
                raise ValueError("Untested OpenDDE input form")
            parsed.append(dict(chain_id=match[1],sequence=match[2]))
        loop = WT if name == "trastuzumab_wt" else baseline[name]["binder_sequence"][98:108]
        check_chains(parsed,loop,antibody,ref_residues)
    return dict(request_sha256=sha256(path),model=req["model"],arms=list(targets),
                residues_per_arm=sum(len(c["sequence"]) for c in parsed),params=req["params"])


def screen(cdr, pool):
    distance, _ = novelty.min_distance(cdr,pool)
    identity = novelty.identity_to_trastuzumab(cdr)
    return distance, distance >= 3 and identity <= 60 and "C" not in cdr


def main():
    antibody = rows(REFERENCE_SPR)[0]
    if antibody["cdrh3"] != WT:
        raise ValueError("Wild-type SPR reference changed")
    ref_atoms, ref_residues = atom_data(CIFFile.read(REFERENCE).block)
    ref_contacts = {cutoff:footprint(ref_atoms,cutoff) for cutoff in CUTOFFS}
    cache = REFERENCE_SPR.with_name("provided_cdrh3.npz")
    with np.load(cache, allow_pickle=False) as archive:
        pool = {int(key.removeprefix("len")): archive[key] for key in archive.files}
    run, = RUNS.glob("006-*")
    run_out = run/"out"
    processed = json.loads((run_out/"boltz2/result.json").read_text())
    cfg = json.loads((run_out/"boltz2/config.json").read_text())
    query_path = run_out/"prepared/holo/queries.json"
    queries = unique_rows(json.loads(query_path.read_text())["queries"],"query_id")
    manifest = unique_rows(rows(run/"manifest.csv"),"query_id")
    predictions = unique_rows(processed["result"]["predictions"],"query_id")
    if set(queries) != set(manifest) or set(queries) != set(predictions) or "trastuzumab_wt" not in queries:
        raise ValueError("Manifest, inputs, outputs and WT must form one complete batch")
    if cfg["seeds"] != [42] or cfg["num_diffusion_samples"] != 1 or cfg["template_paths"] != ["../prepared/holo/template.cif"]:
        raise ValueError("Unexpected refold settings")
    results, objects = [], {}
    template = run_out/"prepared/holo/template.cif"
    rerun, = RUNS.glob("004-*")
    if sha256(template) != sha256(rerun/"out/prepared/holo/template.cif"):
        raise ValueError("Run 006 did not use the run 004 template")
    original_controls = {r["query_id"]:r["binder_sequence"][98:108] for r in rows(rerun/"out/scored-boltz2/refold_metrics.csv")}
    for name,meta in manifest.items():
        cdr = meta["cdrh3"]
        if name == "trastuzumab_wt" and cdr != WT:
            raise ValueError("Substituted WT control")
        if name.startswith("r004_") and original_controls.get(name.replace("r004_", "her2_")) != cdr:
            raise ValueError("Generator control disagrees with run 004")
        chain = check_chains(queries[name]["chains"],cdr,antibody,ref_residues)
        pred = predictions[name]
        if pred["seed"] != 42 or pred["sample"] != 1:
            raise ValueError("Unmatched seed/sample")
        model_path, scores_path = [run_out/"boltz2"/pred[k] for k in ("path","scores_path")]
        block = CIFFile.read(model_path).block
        atoms, residues = atom_data(block)
        for cid, expected in chain.items():
            if "".join(residues[cid][p] for p in sorted(residues[cid])) != expected["sequence"]:
                raise ValueError(f"Output sequence mismatch at {name}/{cid}")
            if cid in {"C","D"} and set(residues[cid]) != set(ref_residues[cid]):
                raise ValueError("Output lost antigen residue mapping")
        # Foundry queries, output entity order, and token order in the mmCIF
        # agree for this dataset. A disagreement requires explicit remapping.
        order = list(block["struct_asym"]["id"].as_array())
        token_order = list(dict.fromkeys(atoms[0]))
        if order != list(chain) or order != token_order:
            raise ValueError("Cannot establish output confidence matrix chain order")
        data = json.loads(scores_path.read_text())
        if data["num_chains"] != 4 or data["num_tokens"] != sum(len(c["sequence"]) for c in chain.values()):
            raise ValueError("Score dimensions disagree with the modeled chains")
        metrics = pair_scores(data["chain_chain_interface_predicted_tm_score"],order)
        metrics["global_ipTM"] = data["interface_predicted_tm_score"]
        geom = {}
        for cutoff,(baseline,_) in ref_contacts.items():
            contacts, loop = footprint(atoms,cutoff)
            geom[str(cutoff)] = dict(reference=len(baseline), intersection=len(baseline & contacts),
                                      predicted=len(contacts), jaccard=len(baseline & contacts)/len(baseline | contacts),
                                      contacting_loop_positions=sorted(loop))
        dist, margin = screen(cdr,pool)
        results.append(dict(query=name,source=meta["source"],cdrh3=cdr,local_distance=dist,
                            local_margin=margin,validation="unverified",p_high=float(meta["p_high"]) if meta["p_high"] else None,
                            blosum62=blosum_scores([cdr])[0],metrics=metrics,footprint=geom))
        objects[name] = dict(model=sha256(model_path),score=sha256(scores_path))
    runs = {}
    for tag in ["001","004","005","007"]:
        dirs = list(RUNS.glob(tag+"-*"))
        if not dirs or not (dirs[0]/"out/scored-boltz2/refold_metrics.csv").is_file():
            continue
        out = dirs[0]/"out"
        f = out/"scored-boltz2/refold_metrics.csv"
        rs = rows(f)
        sequences = [row["binder_sequence"][98:108] for row in rs]
        passes = [screen(s,pool) for s in sequences]
        _,tmpl = atom_data(CIFFile.read(out/"prepared/holo/template.cif").block)
        runs[tag] = dict(refolded=len(rs),unique_loops=len(set(sequences)),
                         numeric_margin_pass=sum(p[1] for p in passes),
                         distance_distribution=dict(Counter(p[0] for p in passes)),
                         all_four_identities=sum(all(s[i] == WT[i] for i in [0,4,5,6]) for s in sequences),
                         template_H3_positions=sorted(set(range(99,109)) & set(tmpl["B"])),
                         target_labels=sorted({row["target_chains"] for row in rs}),
                         inputs={name:sha256(out/name) for name in ["prepared/holo/template.cif","scored-boltz2/refold_metrics.csv","design/config.json","boltz2/config.json"]})
    r003, = RUNS.glob("003-*")
    r001, = RUNS.glob("001-*")
    report = dict(reference_sha256=sha256(REFERENCE),spr_reference_sha256=sha256(REFERENCE_SPR),
                  novelty_cache_sha256=sha256(cache),config_sha256=sha256(run_out/"boltz2/config.json"),
                  manifest_sha256=sha256(run/"manifest.csv"),
                  input_sha256=sha256(query_path),template_sha256=sha256(template),
                  result_sha256=sha256(run_out/"boltz2/result.json"),config=cfg,objects=objects,
                  reference_footprint={str(k):dict(epitope=len(v[0]),loop=sorted(v[1])) for k,v in ref_contacts.items()},
                  generation_runs=runs,
                  open_dde_request=opendde_request_check(r003/"request.json",rows(r001/"out/scored-boltz2/refold_metrics.csv"),antibody,ref_residues),
                  batch=results)
    print(json.dumps(report,indent=2,allow_nan=False))


if __name__ == "__main__":
    main()
