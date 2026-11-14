"""Check exact output chain identities and measure model contacts against the observed crystal footprint."""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from biotite.structure.io.pdbx import CIFFile


def score(root, run, prediction):
    sys.path.insert(0, str(root / 'review'))
    from structure_checks import REFERENCE, THREE_TO_ONE, atom_data, footprint
    atoms, chains = atom_data(next(iter(CIFFile.read(REFERENCE).values())))
    reference, _ = footprint(atoms, 4.5)
    reference = {n for _, n in reference}
    mapping = json.loads((root / 'review/denovo/target_preparation.json').read_text())
    assert reference == set(mapping['reference_epitope_entity_positions']) and len(reference) == 19
    observed = set(chains['C']) | set(chains['D'])
    expected = {q['query_id']: q['chains'] for q in json.loads((run/'queries.json').read_text())['queries']}
    base = run / prediction
    result = json.loads((base/'result.json').read_text())
    predictions = result['result']['predictions']
    settings = result['provenance']['resolved_config']
    assert settings['num_diffusion_samples'] == 1
    pairs = {(q,seed) for q in expected for seed in settings['seeds']}
    assert len(predictions) == len(pairs) and {(r['query_id'],r['seed']) for r in predictions} == pairs
    for r in predictions:
        query = r['query_id']
        src = base / r['path']
        tab = next(iter(CIFFile.read(src).values()))['atom_site']
        def col(name, dtype=str):
            return tab[name].as_array(dtype)
        active = (col('group_PDB') == 'ATOM') & (col('pdbx_PDB_model_num',int)==1) & (col('occupancy',float)>0)
        mask = active & ~np.isin(col('type_symbol'), ['H','D'])
        assert np.isin(col('label_alt_id')[mask], ['.','?','A']).all()
        ids, seqid = col('label_asym_id'), col('label_seq_id', int)
        roles = {}
        residue_map = {}
        for c in set(ids[mask]):
            ca = active & (ids == c) & (col('label_atom_id') == 'CA')
            ordered = sorted(zip(seqid[ca], col('label_comp_id')[ca], strict=True))
            sequence = ''.join(THREE_TO_ONE[aa] for i,aa in ordered)
            matched, = [v['chain_id'] for v in expected[query] if v['sequence'] == sequence]
            assert matched not in roles and len({i for i,aa in ordered}) == len(ordered)
            roles[matched] = c
            if matched == 'T':
                assert all(sequence[i-489] == aa for cid in ('C','D') for i,aa in chains[cid].items())
                residue_map = {idx: n for n,(idx,aa) in enumerate(ordered,489)}
        assert set(roles) == {ch['chain_id'] for ch in expected[query]}
        xyz = np.column_stack([col('Cartn_'+a,float) for a in 'xyz'])
        antigen = np.flatnonzero(mask & (ids == roles['T']))
        antibody = mask & (ids != roles['T'])
        tree = cKDTree(xyz[antibody])
        dist, _ = tree.query(xyz[antigen], k=1)
        contacted = {residue_map[k] for k in seqid[antigen[dist<=4.5]]}
        scores = json.loads((base/r['scores_path']).read_text())
        yield dict(query=query,seed=r['seed'],global_iptm=scores['interface_predicted_tm_score'],
                   crystal_hits=len(contacted & reference),crystal_contacts=19,predicted_contacts=len(contacted),
                   new_contacts_at_crystal_unresolved_positions=len(contacted-observed),
                   observed_jaccard=round(len(contacted&reference)/len((contacted&observed)|reference),5),
                   mapped_roles=' '.join(f'{k}={roles[k]}' for k in sorted(roles)),
                   her2_contact_positions=' '.join(map(str,sorted(contacted))),
                   model_sha256=hashlib.sha256(src.read_bytes()).hexdigest())


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('run', type=Path)
    p.add_argument('prediction', default='prediction', nargs='?')
    args = p.parse_args()
    rows = list(score(args.root.resolve(),args.run.resolve(),args.prediction))
    writer = csv.DictWriter(sys.stdout,fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
