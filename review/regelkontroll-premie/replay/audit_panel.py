"""Reconcile the two panels by full sequence, and backtest what the strict lab rule can identify."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import median
from zipfile import ZipFile
import io


def read(path):
    with path.open(newline='',encoding='utf-8-sig') as handle:
        return list(csv.DictReader(handle))


def write(path, rows):
    with path.open('w',newline='') as handle:
        w=csv.DictWriter(handle,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(r):
    return r['heavy_sequence'],r['light_sequence']


def main(root,work):
    src=root/'review/panel18plus2'
    panel=read(src/'RANKED_18_PLUS_2.csv')
    details={r['sequence_id']:r for r in read(src/'KANDIDATBEVIS.csv')}
    by_name={details[r['sequence_id']]['alias']:r for r in panel}
    common_run=root/'runs/012-codex-18plus2'
    snapshot=work/'common-panel-snapshot.csv'
    other=read(snapshot)
    original_set={key(r) for r in panel}
    assert len(original_set)==20 and len(original_set&{key(r) for r in other})==19
    order=['anas_007','anas_003','r004_cdrh3_3','anas_016','anas_015','anas_009','anas_028','novel3',
           'anas_004','anas_038','anas_036','novel1','anas_026','anas_031','anas_021','anas_014','anas_010','anas_002','anas_039','anas_040']
    assert set(order)==set(by_name)
    revised=[by_name[name] for name in order]
    for n in [20,10]:
        write(work/f'PRIZE_TOP{n}.csv',revised[:n])
    pre=root/'runs/011-codex-denovo-vhh'
    poses=json.loads((common_run/'common-evidence.json').read_text())
    prior=json.loads((pre/'local-refold-evidence.json').read_text())
    sources=[(v,'012/common-evidence.json') for v in poses]
    sources.extend((v,'011/local-refold-evidence.json') for v in prior if v['name']=='novel1_crop119' and v['model'] in ('mol1','opendde-abag'))
    models={(v['candidate'],v['model']):(v,file) for v,file in sources}
    geometry=read(work/'ECTODOMAIN.csv')
    summary=[]
    for rank,(alias,item) in enumerate(zip(order,revised,strict=True),1):
        ident=item['sequence_id'];old=details[ident]
        row=dict(rank=rank,sequence_id=ident,alias=alias,prior_rank=old['rank'],kind=item['kind'],
                 boltz_four_contacts_of6=old['boltz_all_four_of_six'],blosum62=old['blosum62'],
                 binding_ddg_kcal_mol=old['stabddg_binding_estimate'],ddg_MC_SE=old['stabddg_reported_se'],
                 flagged_high_cdr3_motif=old['cdr3_high_severity_motifs'],
                 of3_seed42_no_template_hits_of19=old['of3_seed42_no_template_hits_of19'],
                 of3_seed42_target_template_hits_of19=old['of3_seed42_HER2_only_template_hits_of19'])
        for model in ['mol1','opendde-abag']:
            v,file=models[ident,model]
            seq={k:v['regional_chains'][c]['sequence'] for k,c in v['chain_roles'].items() if k in ('H','L')}
            assert seq['H']==item['heavy_sequence'] and seq.get('L','')==item['light_sequence']
            row.update({model+'_hits_of19':round(19*v['epitope_recall_4.5']),model+'_jaccard':round(v['epitope_jaccard_4.5'],3),
                        model+'_contact_PAE_A':round(v['mean_contact_pair_symmetric_PAE_A'],3) if 'mean_contact_pair_symmetric_PAE_A' in v else '',
                        model+'_structure_sha256':v['structure_sha256'],model+'_source':file})
        geom=[v for v in geometry if v['query']==alias]
        row['overlay_poses']=len(geom)
        row['overlay_both_fits_any_under2A']=sum(all(int(v[col+'_Ab_atoms_within_2A_of_omitted_HER2'])>0 for col in ('whole_crop','native_patch')) for v in geom)
        row.update(measured_kd_nM='',measured_competition='',measured_thermal='',official_tier='unknown')
        summary.append(row)
    write(work/'RANK_AND_EVIDENCE.csv',summary)
    wt_entries=[v for v in poses if v['candidate']=='trastuzumab_wt']
    assert len(wt_entries)==2
    control={v['model']:round(19*v['epitope_recall_4.5']) for v in wt_entries}
    fab=[r for r in summary if r['kind']=='paired']
    assert len(fab)==18
    # Evaluate the same physical constructs exactly once, whether or not the FACS screen saw them.
    spr=root/'data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv'
    facs=root/'data/her2-trastuzumab/tz_her2_facs_3classes_524346.csv.zip'
    with ZipFile(facs) as archive:
        member,=[n for n in archive.namelist() if n.endswith('.csv') and '__MACOSX' not in n]
        with archive.open(member) as f:
            seen={r['cdrh3'] for r in csv.DictReader(io.TextIOWrapper(f))}
    assays=read(spr)
    parent=assays[0];h=parent['vh_sequence'];l=parent['vl_sequence'];wt=parent['cdrh3']
    kdwt=[float(x['kd_nM']) for x in assays if x['vh_sequence']==h and x['vl_sequence']==l]
    assert len(kdwt)==8
    groups={}
    for x in assays:
        c=x['cdrh3']
        if len(c)==len(wt) and 4<=sum(a!=b for a,b in zip(wt,c,strict=True))<=6 and x['vl_sequence']==l and x['vh_sequence']==h[:98]+c+h[108:]:
            groups.setdefault(c,[]).append(x)
    historical={}
    for cohort,group in [('all',groups),('FACS_unseen',{c:v for c,v in groups.items() if c not in seen})]:
        outcomes=Counter(); values={}
        for c,rows in group.items():
            result,={r['binding_result'] for r in rows}
            outcomes[result]+=1
            if result=='quantified_binding': values[c]=median(float(v['kd_nM']) for v in rows)
        historical[cohort]={'n_unique':len(group),'outcome_counts':dict(outcomes),'min_quantified_nM':min(values.values()),
                            'strictly_below_median_wt':sum(v<median(kdwt) for v in values.values()),
                            'strictly_below_weakest_wt':sum(v<max(kdwt) for v in values.values()),
                            'within_25pct_of_median_wt_or_better':sum(v<=1.25*median(kdwt) for v in values.values()),
                            'within_2x_median_wt_or_better':sum(v<=2*median(kdwt) for v in values.values())}
    assert historical['FACS_unseen']['n_unique']==255 and historical['FACS_unseen']['strictly_below_median_wt']==0
    source=read(src/'original_reference.csv')
    flags={r['sequence_id']:r for r in json.loads((work/'thermal-flags.json').read_text())}
    def num(x):return float(x.replace('\u200b','').strip())
    def high_cdr3(id):
        return sum(f['region']=='cdr3' and f['severity']=='high' for f in flags['original_'+id]['liabilities'])
    wtrow,=[r for r in source if r['Candidate']=='Trastuzumab']
    k='Fab KD (nM) (hHER2)';t1='DSF - IP #1 (oC)';t2='DSF - IP #2 (oC)'
    baseline,f1,f2=map(num,[wtrow[k],wtrow[t1],wtrow[t2]])
    variants=[r for r in source if r is not wtrow]
    noflag=[r for r in variants if high_cdr3(r['Candidate'])<high_cdr3(wtrow['Candidate'])]
    external={'n':len(variants),'strictly_tighter_Fab':sum(num(r[k])<baseline for r in variants),
              'higher_IP1':sum(num(r[t1])>f1 for r in variants),'higher_IP2':sum(num(r[t2])>f2 for r in variants),
              'less_high_cdr3_flags_than_parent':len(noflag),'less_flags_and_higher_IP1':sum(num(r[t1])>f1 for r in noflag),
              'observed_both_strict_fab_kd_and_IP1':sum(num(r[k])<baseline and num(r[t1])>f1 for r in variants)}
    source_files=[src/'RANKED_18_PLUS_2.csv',src/'KANDIDATBEVIS.csv',common_run/'common-evidence.json',pre/'local-refold-evidence.json',spr,facs,src/'original_reference.csv']
    report={'input_sha256':{str(p.relative_to(root)):digest(p) for p in source_files},'cross_panel_exact_pair_overlap':19,'common_panel_snapshot_sha256':digest(snapshot),
            'matched_common_control_hits_of19':control,'mol1_full_recall_for_fabs':sum(r['mol1_hits_of19']==19 for r in fab),
            'historical':historical,'wt_median_nM':median(kdwt),'wt_range_nM':[min(kdwt),max(kdwt)],
            'historical_conditional_upper_one_sided_95':1-.05**(1/82),'external_matched_fab_and_thermal':external,
            'geometry_prediction_count':len(geometry),'native_reference_sha256':digest(work/'1n8z.cif'),
            'capture_guide_sha256':digest(work/'field-guide.html'),'conservative_planning_count_first_four':0,'estimated_joint_probability':None}
    (work/'ANALYSIS.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['input_sha256']},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('team',type=Path);p.add_argument('work',type=Path)
    a=p.parse_args();main(a.team,a.work)
