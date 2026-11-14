"""Verify all prediction receipts, construct tables and produce the package evidence summary."""
from collections import Counter
from datetime import datetime
import argparse
import hashlib
import json
from pathlib import Path
from build_panel import read, write
from score_openfold import score


def finish(root, dest):
    run = root/'runs/review-apheris-of3-panel'
    allrows, receipts = [], []
    for batch in ['.', 'extension', 'pair-repeats']:
        folder = run/batch
        for pred, condition in [('prediction','no_template'),('prediction-her2-template','HER2_only_template')]:
            path = folder/pred/'result.json'
            doc = json.loads(path.read_text())
            provenance = doc['provenance']
            settings = provenance['resolved_config']
            assert provenance['module']=={'name':'apheris-openfold3','version':'1.3.0'}
            assert bool(settings['template_paths'])==(condition=='HER2_only_template')
            duration=(datetime.fromisoformat(provenance['ended_at'])-datetime.fromisoformat(provenance['started_at'])).total_seconds()
            receipts.append(dict(batch=batch,condition=condition,seconds=duration,structures=len(doc['result']['predictions']),
                                 seeds=settings['seeds'],input_sha256=hashlib.file_digest((folder/'queries.json').open('rb'),'sha256').hexdigest(),
                                 result_sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest()))
            for x in score(root,folder,pred):
                allrows.append(dict(batch=batch,condition=condition,**x))
    panel=read(dest/'RANKED_18_PLUS_2.csv')
    val=read(dest/'validator-output.csv')
    to_map=lambda rows:{r['sequence_id']:r for r in rows}
    assert len(panel)==len(val)==20 and to_map(panel)==to_map(val)
    liab=json.loads((dest/'liabilities.json').read_text())
    assert all(r['is_valid'] and r['is_novel_enough'] for r in liab)
    assert Counter(r['novelty_class'] for r in liab)=={'novel':18,'de_novo':2}
    assert {r['sequence_id'] for r in liab}==set(to_map(panel))
    wt_loop='SRWGGDGFYAMDY'
    for r in liab:
        if r['kind']=='paired':
            assert sum(a==b for a,b in zip(wt_loop,r['cdrh3'],strict=True))/len(wt_loop) < 0.70
            assert r['cdrh3_min_distance'] >= 3
    evid=read(dest/'KANDIDATBEVIS.csv')
    assert [r['sequence_id'] for r in panel]==[r['sequence_id'] for r in evid]
    assert len(allrows)==60
    look={(r['query'],r['seed'],r['condition']):r for r in allrows}
    assert len(look)==60
    for r in evid:
        for cond in ['no_template','HER2_only_template']:
            r['of3_seed42_'+cond+'_hits_of19']=look[r['alias'],42,cond]['crystal_hits']
        assert r['official_tier']=='unknown'
    write(dest/'KANDIDATBEVIS.csv',evid)
    write(dest/'OPENFOLD_RESULTS.csv',allrows)
    pairs=['trastuzumab_wt','anas_007','anas_015','anas_009']
    allseeds=[{'query':q,'no_template':[look[q,s,'no_template']['crystal_hits'] for s in [42,7,101]],
               'HER2_only_template':[look[q,s,'HER2_only_template']['crystal_hits'] for s in [42,7,101]]} for q in pairs]
    output={'image_digest':'sha256:1a35dfce17b3b8cf8994388104642fc6b04afc72ec01e2bffba488f9115e81c1',
            'receipts':receipts,'structures':60,'unique_complexes':len({r['query'] for r in allrows}),
            'elapsed_module_minutes':round(sum(r['seconds'] for r in receipts)/60,2),
            'four_repeats_seed_order':[42,7,101],'four_repeats_hits_of19':allseeds,
            'abguard_valid':len(val),'validated_partition_order_differs_from_rank':val!=panel,'lab_measured':0,
            'no_order_receipt':True,'official_tiers_pending':20}
    (dest/'VERIFICATION.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('dest',type=Path)
    args=p.parse_args();finish(args.root.resolve(),args.dest.resolve())
