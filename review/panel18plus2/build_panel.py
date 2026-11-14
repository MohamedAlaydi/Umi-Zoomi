"""Export the frozen ranked CSV and separate evidence table, preserving the order in the submission input."""
import argparse
import csv
import json
from pathlib import Path


def read(path):
    with path.open(newline='') as handle:
        return list(csv.DictReader(handle))


def write(path, rows):
    with path.open('w', newline='') as h:
        w = csv.DictWriter(h,fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def build(root, folder, order):
    baseline = {r['query']:r for r in read(root/'review/pitch_her2/Rangering_begrunnet.csv')}
    denovo = root/'runs/011-codex-denovo-vhh'
    receipt = {r['sequence_id']:r for r in json.loads((denovo/'abguard-final/liabilities.json').read_text())}
    manifest = {r['name'].split('_')[0]:r for r in json.loads((denovo/'local-refold-manifest.json').read_text()) if r['name'].endswith('_crop119')}
    prior = json.loads((denovo/'local-refold-evidence.json').read_text())
    provided = {r['candidate']:r['min_distance_provided_imgt'] for r in json.loads((denovo/'provided-HER2-reference-check.json').read_text())['candidates']}
    ddg = {r['cdrh3']:r for r in read(root/'people/anas/stabddg-joined.csv') if r['role']=='candidate'}
    direct = read(root/'data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv')
    submitted, evidence = [], []
    for slot,(name,reason) in enumerate(order,1):
        is_vhh = name in manifest
        if is_vhh:
            r = manifest[name]
            key = source = r['candidate']
            heavy, light = r['antibody_sequences']['H'], ''
        else:
            r = baseline[name]
            key, source = name, 'existing_'+name
            heavy, light = r['heavy_variable'], r['light_variable']
        old = receipt[source]
        assert old['is_valid'] and (old['heavy_sequence'],old['light_sequence'] or '')==(heavy,light)
        assert len(heavy)+len(light)<=250
        assert not any((m['vh_sequence'],m['vl_sequence'] or '')==(heavy, light) for m in direct)
        loop_liabilities = [f"{b['name']} ({b['motif']})" for b in old['liabilities'] if b['region']=='cdr3' and b['severity']=='high']
        kind = 'vhh' if is_vhh else 'paired'
        submitted.append(dict(sequence_id=key,kind=kind,heavy_sequence=heavy,light_sequence=light,
                              design_description=(f'Experimental de novo HER2 VHH ({name})' if is_vhh else 'Trastuzumab Fab optimisation')))
        def hits(model, context):
            vals = [round(v['epitope_recall_4.5']*19) for v in prior if v['name']==name+'_'+context and v['model']==model]
            return vals[0] if vals else ''
        sta = ddg.get(heavy[98:108],{}) if not is_vhh else {}
        evidence.append(dict(rank=slot,alias=name,sequence_id=key,track='de_novo' if is_vhh else 'optimisation',
                             selection_reason=reason,blosum62=r.get('blosum62',''),boltz_all_four_of_six=r.get('all_four_of_six',''),
                             boltz_exact_surface_of_six=r.get('exact_surface_of_six',''),
                             stabddg_binding_estimate=sta.get('ddg',''),stabddg_reported_se=sta.get('se',''),
                             mol1_hits_short_of19=hits('mol1','crop119'),mol1_hits_long_of19=hits('mol1','ectodomain607'),
                             opendde_hits_short_of19=hits('opendde-abag','crop119'),opendde_hits_long_of19=hits('opendde-abag','ectodomain607'),
                             validator_reference_imgt_distance=old['cdrh3_min_distance'],provided_data_imgt_distance=provided.get(key,''),
                             cdr3_high_severity_motifs=' | '.join(loop_liabilities) or 'none flagged',
                             historical_exact_construct_spr_rows=0,adaptyv_spr_kd='pending',adaptyv_competition='pending',
                             adaptyv_thermal='pending',official_tier='unknown'))
    assert len(order)==len(set(r['sequence_id'] for r in submitted))==len(set((r['heavy_sequence'],r['light_sequence']) for r in submitted))==20
    assert sum(r['kind']=='vhh' for r in submitted)==2
    write(folder/'RANKED_18_PLUS_2.csv',submitted)
    write(folder/'KANDIDATBEVIS.csv',evidence)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('root',type=Path)
    p.add_argument('folder',type=Path)
    args=p.parse_args()
    order=json.loads((args.folder/'order.json').read_text())
    build(args.root,args.folder,order)
