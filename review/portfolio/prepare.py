"""Freeze an explicit18-Fab/2-VHH proposal and fill missing common cofold coverage."""
import csv,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/012-codex-18plus2'
PREVIOUS=ROOT/'runs/011-codex-denovo-vhh'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pair_hash(h,l):return hashlib.sha256(f'VH={h}\nVL={l}\n'.encode()).hexdigest()
def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    RUN.mkdir(exist_ok=True)
    if (RUN/'manifest.json').exists():raise ValueError('Frozen portfolio already exists; do not silently replace it')
    source=ROOT/'review/pitch_her2/Rangering_begrunnet.csv'
    opts=list(csv.DictReader(source.open()))[:18]
    old=json.loads((PREVIOUS/'local-refold-manifest.json').read_text())
    candidates=[]
    for r in opts:
        assert pair_hash(r['heavy_variable'],r['light_variable'])==r['pair_sha256']
        candidates.append(dict(query=r['query'],requested_track='optimisation',format='Fab',
            heavy_variable=r['heavy_variable'],light_variable=r['light_variable'],pair_sha256=r['pair_sha256'],
            prior_optimization_rank=int(r['rank']),selection_reason=r['reason']))
    for name in ['novel2','novel3']:
        row=next(r for r in old if r['name']==name+'_crop119');h=row['antibody_sequences']['H']
        candidates.append(dict(query=row['candidate'],requested_track='de_novo',format='VHH',
            heavy_variable=h,light_variable='',pair_sha256=pair_hash(h,''),prior_optimization_rank=None,
            selection_reason=('novel2: strongest independent monomer fold; docking unsupported' if name=='novel2' else
            'novel3: strongest Mol1 epitope-recovery hypothesis across two target contexts; large CDRH3 uncertainty'),
            short_name=name))
    assert len(candidates)==20 and len({r['pair_sha256'] for r in candidates})==20
    assert all(len(r['heavy_variable'])+len(r['light_variable'])<=250 for r in candidates)
    target=next(r for r in old if r['context']=='crop119')['target_sequence']
    manifest=[]
    for r in candidates:
        seqs={'H':r['heavy_variable']}
        if r['light_variable']:seqs['L']=r['light_variable']
        previous=next((x for x in old if x['candidate']==r['query'] and x['context']=='crop119'),None)
        entry=dict(name=r['query'],candidate=r['query'],context='crop119',antibody_sequences=seqs,target_sequence=target,
            requested_track=r['requested_track'],format=r['format'],pair_sha256=r['pair_sha256'])
        if previous:entry.update(design_structure=previous['design_structure'],reuse_target_name=previous['name'])
        manifest.append(entry)
    wt=next(r for r in old if r['name']=='trastuzumab_wt_control')
    manifest.append(dict(name='trastuzumab_wt_control',candidate='trastuzumab_wt',context='crop119',
        antibody_sequences=wt['antibody_sequences'],target_sequence=target,requested_track='control',format='Fab',
        pair_sha256=pair_hash(wt['antibody_sequences']['H'],wt['antibody_sequences']['L']),reuse_target_name=wt['name']))
    for model in ['mol1','opendde-abag']:
        folder=RUN/('common-'+model);folder.mkdir(exist_ok=False)
        previous=json.loads((PREVIOUS/('local-refold-'+model)/'request.json').read_text())
        targets=[dict(name=r['name'],content=''.join(f'>{c}|protein\n{s}\n' for c,s in {**r['antibody_sequences'],'T':r['target_sequence']}.items())) for r in manifest if not r.get('reuse_target_name')]
        request=dict(model=model,name='team14-18plus2-common-blind-'+model,params=previous['params'],targets=targets)
        assert len(targets)==18 and request['params']['seed']==42 and request['params']['diffusion_samples']==1
        (folder/'request.json').write_text(json.dumps(request,indent=2))
    (RUN/'manifest.json').write_text(json.dumps(manifest,indent=2))
    (RUN/'candidates.json').write_text(json.dumps(candidates,indent=2))
    for label,order in [('both-tracks-top4',candidates[:2]+candidates[18:]+candidates[2:18]),
                        ('optimization-top4',candidates[:4]+candidates[18:]+candidates[4:18])]:
        rows=[]
        for index,r in enumerate(order,1):
            rows.append(dict(rank=index,query=r['query'],requested_track=r['requested_track'],format=r['format'],
                heavy_variable=r['heavy_variable'],light_variable=r['light_variable'],pair_sha256=r['pair_sha256'],
                role='provisional proposal; track assigned by validator; not submitted to laboratory',reason=r['selection_reason']))
        write_csv(RUN/(label+'.csv'),rows)
    rows=[dict(sequence_id=r['query'],kind='paired' if r['format']=='Fab' else 'vhh',heavy_sequence=r['heavy_variable'],
               light_sequence=r['light_variable'],design_description=r['selection_reason']) for r in candidates]
    write_csv(RUN/'submission.csv',rows)
    (RUN/'predeclared.json').write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),
        source_rank_file=str(source.relative_to(ROOT)),source_rank_sha256=sha(source),
        selected_optimization_ranks=list(range(1,19)),de_novo_names=['novel2','novel3'],
        purpose='Complete common blind-prediction coverage before offering final18+2 prioritization; current rank is provisional.',
        controls='Reuse exact-sequence crop119 WT and VHH jobs from011 with identical models and settings; do not rerun identical work.',
        endpoints=['reference-epitope Jaccard and recall at4/4.5/5A','target-specific pair ipTM from actual chain mapping','severe cross-chain clashes','antibody regional confidence'],
        interpretation='Compare within format, retain disagreement and source provenance; no average across raw different-model scores, no calibrated S-tier probability.'),indent=2))
    print(json.dumps({'designs':len(candidates),'optimisations':18,'VHHs':2,'new_targets_per_model':18,'reused_per_model':3,
        'source_ranking_sha256':sha(source)},indent=2))

if __name__=='__main__':main()
