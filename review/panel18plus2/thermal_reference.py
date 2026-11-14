"""Audit observed endpoints on a public HER2 design panel and check exact sequence overlap."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def read(path):
    with path.open(encoding='utf-8-sig',newline='') as h:
        return list(csv.DictReader(h))


def value(token):
    try:
        return float(token.replace('\u200b','').strip())
    except ValueError:
        return None


def audit(root,folder):
    authors = read(folder/'original_reference.csv')
    sources = [folder/'original_reference.csv',folder/'DSF1.csv',folder/'DSF2.csv']
    thermal = [{(r['heavy'],r['light']):value(r['fitness']) for r in read(p)} for p in sources[1:]]
    assert len(authors)==len(thermal[0])==len(thermal[1])==13 and thermal[0].keys()==thermal[1].keys()
    parent = read(root/'data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv')[0]
    wt = (parent['vh_sequence'],parent['vl_sequence'])
    assert wt in thermal[0]
    official = {(r['heavy_sequence'],r['light_sequence']) for r in read(folder/'RANKED_18_PLUS_2.csv')}
    overlaps=len(official & set(thermal[0]))
    data=[]
    for key in thermal[0]:
        matched, = [r for r in authors if r['HCDR3'] in key[0]]
        raw=[value(matched[f'DSF - IP #{n} (oC)']) for n in (1,2)]
        assert raw==[x[key] for x in thermal]
        data.append((key==wt,raw,value(matched['Fab KD (nM) (hHER2)'])))
    (_, parent_temps, parent_kd), = [x for x in data if x[0]]
    variants=[r for r in data if not r[0]]
    assert all(r[1][0] is not None and r[1][1] is not None for r in variants)
    return {'reference':'AbSciBio public HER2 design study, functionality-developability-cross_reactivity-data.csv',
            'primary_revision':(folder/'original_commit.txt').read_text().strip(),
            'curation_revision':(folder/'flab_commit.txt').read_text().strip(),
            'sha256':{p.name:hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in sources},
            'tested_variants':len(variants),'control_thermal_transitions_celsius':parent_temps,
            'variant_first_thermal_point_above_control':sum(r[1][0]>parent_temps[0] for r in variants),
            'variant_second_thermal_point_above_control':sum(r[1][1]>parent_temps[1] for r in variants),
            'exact_heavy_light_matches_in_our_20':overlaps,
            'historical_control_fab_kd_nM_in_this_study':parent_kd,
            'fab_kd_available':sum(r[2] is not None for r in variants),
            'these_are_two_thermal_transitions':'Different reported inflection points. Point comparisons only, uncertainty and assay format matter. No measured thermal effect inferred for our designs.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path);parser.add_argument('folder',type=Path)
    args=parser.parse_args();print(json.dumps(audit(args.root,args.folder),indent=2))
