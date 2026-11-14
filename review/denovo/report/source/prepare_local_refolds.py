"""Freeze no-template, no-hotspot cofolds of novel candidates and explicit controls."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/011-codex-denovo-vhh'


def main():
    rows={r['query']:r for r in json.loads((RUN/'local-candidates.json').read_text())}
    searches=json.loads((RUN/'variable-rcsb-sequence-searches.json').read_text())
    no_hits={r['value']['query'] for r in searches if r['status']=='fulfilled' and r['value']['result']['total_count']==0}
    selected=sorted([rows[q] for q in no_hits],key=lambda r:-r['footprint']['4.5']['recall'])
    target=''.join((ROOT/'review/denovo/her2_pilot_target.fasta').read_text().splitlines()[1:])
    full=json.loads((ROOT/'review/denovo/rcsb_1n8z_her2_mapping.json').read_text())['query_sequence']
    assert full[488:607]==target
    parent=next(csv.DictReader((ROOT/'data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv').open()))
    manifest=[]
    for index,row in enumerate(selected,1):
        for context,antigen in [('crop119',target),('ectodomain607',full)]:
            manifest.append(dict(name=f'novel{index}_{context}',candidate=row['query'],
                role='novelty-screened exploratory VHH; zero RCSB hits at 70% cutoff, not universal database clearance',
                context=context,antibody_sequences={'H':row['heavy_variable']},target_sequence=antigen,
                design_structure=row['structure'],generation_epitope=row['footprint']['4.5'],
                official_validation='pending final installed-validator receipt'))
    for name,query in [('high_footprint_known_hit','rfd4-variable-sequence-k1__her2_variable_sequence_4_generated'),
                       ('fixed_framework_control','her2_caplacizumab_cdr123_3_generated')]:
        row=rows[query]
        manifest.append(dict(name=name,candidate=query,role='computational comparator; known-antibody similarity warning',
            context='crop119',antibody_sequences={'H':row['heavy_variable']},target_sequence=target,
            design_structure=row['structure'],generation_epitope=row['footprint']['4.5'],official_validation='pending'))
    manifest.append(dict(name='trastuzumab_wt_control',candidate='trastuzumab_wt',
        role='sequence-verified Fab baseline; do not directly equate Fab/VHH global ipTM',context='crop119',
        antibody_sequences={'H':parent['vh_sequence'],'L':parent['vl_sequence']},target_sequence=target,
        official_validation='reference, not a novel submission'))
    for row in manifest:
        row['sequence_hashes']={c:hashlib.sha256(seq.encode()).hexdigest() for c,seq in row['antibody_sequences'].items()}
        row['target_sha256']=hashlib.sha256(row['target_sequence'].encode()).hexdigest()
    (RUN/'local-refold-manifest.json').write_text(json.dumps(manifest,indent=2))
    for model in ['openfold3','mol1']:
        folder=RUN/('local-refold-'+model);folder.mkdir(exist_ok=False)
        targets=[]
        for row in manifest:
            sequences={**row['antibody_sequences'],'T':row['target_sequence']}
            fasta=''.join(f'>{chain}|protein\n{sequence}\n' for chain,sequence in sequences.items())
            targets.append(dict(name=row['name'],content=fasta))
        request=dict(model=model,name='team14-her2-variable-designs-context-'+model,
            params=dict(output_format='cif',write_pae=True,seed=42,diffusion_samples=1),targets=targets)
        (folder/'request.json').write_text(json.dumps(request,indent=2))
    print(json.dumps({'no_close_PDB_hits':len(selected),'targets_per_model':len(manifest),
                       'selected':[r['query'] for r in selected]},indent=2))


if __name__=='__main__':main()
