"""Collect exact-sequence common cofold evidence and coverage for a frozen18+2 panel."""
import csv,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
from biotite.structure.io.pdbx import CIFFile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'denovo'))
from collect_refolds import evaluate
from collect_campaign import coordinates
from prepare import ROOT,RUN,PREVIOUS,pair_hash,write_csv


def read(path):return json.loads(path.read_text())
def table(path):return list(csv.DictReader(path.open()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def contact_pae(path,roles):
    sidecar=path.with_name(path.stem+'_pae.json');archive=path.with_name(path.stem+'_pae.npz')
    info=read(sidecar)
    assert info['token_order']=='tokens of the written structure, in file order'
    assert info['arrays']['pae']['units']=='angstrom'
    tab=next(iter(CIFFile.read(path).values()))['atom_site'];col=lambda n,d=str:tab[n].as_array(d)
    keep=(col('label_atom_id')=='CA')&(col('pdbx_PDB_model_num',int)==1)
    tokens=list(zip(col('label_asym_id')[keep],col('label_seq_id',int)[keep]));assert len(tokens)==len(set(tokens))
    with np.load(archive) as npz:pae=npz['pae']
    assert pae.shape==(len(tokens),len(tokens)) and len(tokens)==info['n_tokens'] and np.isfinite(pae).all()
    mapping={p:i for i,p in enumerate(tokens)}
    chains,(chain,pos,xyz)=coordinates(path);ab=np.flatnonzero(np.isin(chain,[v for k,v in roles.items() if k!='T']));ag=np.flatnonzero(chain==roles['T'])
    tree=cKDTree(xyz[ag]);pairs={(mapping[(chain[i],int(pos[i]))],mapping[(chain[ag[j]],int(pos[ag[j]]))])
        for i,group in zip(ab,tree.query_ball_point(xyz[ab],4.5)) for j in group}
    # One symmetric PAE per contacting residue pair; no-contact results remain null.
    values=[(float(pae[i,j])+float(pae[j,i]))/2 for i,j in pairs]
    return dict(contact_residue_pairs_4_5=len(pairs),mean_contact_pair_symmetric_PAE_A=float(np.mean(values)) if values else None,
                pae_sha256=sha(archive),pae_sidecar_sha256=sha(sidecar))


def main():
    manifest=read(RUN/'manifest.json');evidence=[]
    for model in ['mol1','opendde-abag']:
        for entry in manifest:
            folder=PREVIOUS/('local-refold-'+model) if entry.get('reuse_target_name') else RUN/('common-'+model)
            if not (folder/'results.json').exists():continue
            data=read(folder/'results.json');name=entry.get('reuse_target_name',entry['name'])
            rows=[r for r in data['rows'] if r['id']==name]
            assert len(rows)==1
            row=rows[0]
            if row['status']!='ok':
                evidence.append(dict(candidate=entry['candidate'],model=model,status=row['status'],error=row.get('error')));continue
            artifact=[a for a in data['artifacts'] if a['type']=='structure' and a.get('target')==name];assert len(artifact)==1
            path=folder/'artifacts'/artifact[0]['path'];value=evaluate(path,entry)
            value.update(contact_pae(path,value['chain_roles']))
            value.update(candidate=entry['candidate'],model=model,format=entry['format'],requested_track=entry['requested_track'],
                pair_sha256=entry['pair_sha256'],global_iptm=row.get('iptm'),status='ok',source_job=data['job_id'],
                row_target=name,source_reused=bool(entry.get('reuse_target_name')),structure=str(path.relative_to(ROOT)),
                structure_sha256=sha(path),raw_chain_pair_iptm=row.get('pair_chains_iptm'),
                interpretation='Shared native-sequence crop119; no input structural template or hotspot; one seed42 per model. No experimental binding or temperature.')
            evidence.append(value)
    (RUN/'common-evidence.json').write_text(json.dumps(evidence,indent=2))
    # Existing6-seed Foundry model poses are immutable evidence; verify raw hashes first.
    previous=read(ROOT/'review/pitch_her2/final_evidence.json')
    for name,digest in previous['raw_file_digests'].items():assert sha(ROOT/name)==digest
    facs={r['query_id']:r for r in table(ROOT/'runs/006-anas-enumerated-top40/manifest.csv')}
    ddg=[r for r in table(ROOT/'people/anas/stabddg-joined.csv') if r['role']=='candidate'];ddg={r['cdrh3']:r for r in ddg}
    parent=table(ROOT/'data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv')[0];left,right=parent['vh_sequence'].split(parent['cdrh3'])
    all_liabilities=read(PREVIOUS/'abguard-final/liabilities.json')
    liabilities={pair_hash(r['heavy_sequence'],r.get('light_sequence') or ''):r for r in all_liabilities}
    nbb={r['candidate']:r for r in read(PREVIOUS/'nanobodybuilder-evidence.json')}
    af2={r['candidate']:r for r in read(PREVIOUS/'local-refold-evidence.json') if r['model']=='af2ig'}
    coverage=[]
    for row in read(RUN/'candidates.json'):
        q=row['query'];poses=previous['panel_poses'].get(q,{})
        if poses:assert set(poses)=={'1','2','3','4','5','42'}
        core=row['heavy_variable'][len(left):-len(right)] if row['format']=='Fab' else None
        if core:assert row['heavy_variable']==left+core+right and row['light_variable']==parent['vl_sequence']
        binding=ddg.get(core,{})
        old=liabilities[row['pair_sha256']]
        nbb_final=next((r for r in nbb.get(q,{}).get('models',[]) if r['native_file']=='final_model.pdb'),{})
        r=dict(query=q,requested_track=row['requested_track'],format=row['format'],heavy_variable=row['heavy_variable'],
            light_variable=row['light_variable'],pair_sha256=row['pair_sha256'],installed_abguard_valid=old['is_valid'],
            local_Boltz2_seed_count=len(poses),local_Boltz2_seeds=';'.join(sorted(poses,key=int)),
            FACS_model_p_high=facs.get(q,{}).get('p_high') or None,
            binding_ddG_kcal_mol=float(binding['ddg']) if binding else None,
            binding_ddG_MC_SE_kcal_mol=float(binding['se']) if binding else None,
            binding_ddG_alias=binding.get('id'),
            n_high_severity_motifs=old['n_high_severity'],liabilities=';'.join(x['tag']+':'+x['motif'] for x in old['liabilities']),
            NBB2_final_CA_rmsd=nbb_final.get('all_CA_rmsd_after_self_fit'),
            AF2IG_global_iptm=af2.get(q,{}).get('iptm'),AF2IG_interface_PAE_A=af2.get(q,{}).get('interface_pae'),
            Adaptyv_new_lab_measurements=False,direct_Tm_measurement=None,expression_prediction='not run: no SoluProt/NetSolP/Aggrescan3D result',
            uncertainty='computational evidence only; final sequence-track acceptance subject to organisers')
        for model in ['mol1','opendde-abag']:
            values=[v for v in evidence if v['candidate']==q and v['model']==model]
            value=values[0] if values else {}
            for field in ['status','global_iptm','epitope_recall_4.5','epitope_jaccard_4.5','mean_contact_pair_symmetric_PAE_A','clashing_cross_chain_atom_pairs_2A']:
                r[model+'_'+field]=value.get(field)
        coverage.append(r)
    write_csv(RUN/'score-coverage.csv',coverage)
    controls=[r for r in table(ROOT/'people/anas/stabddg-joined.csv') if r['role']=='control']
    stat=spearmanr([float(r['log2_vs_wt']) for r in controls],[float(r['ddg']) for r in controls])
    metrics=dict(candidate_count=len(coverage),optimization_count=sum(r['format']=='Fab' for r in coverage),
        de_novo_count=sum(r['format']=='VHH' for r in coverage),completed_common_rows=sum(r['status']=='ok' for r in evidence),
        target_common_rows=42,new_common_predictions=sum(r['status']=='ok' and not r['source_reused'] for r in evidence),
        reused_common_predictions=sum(r['status']=='ok' and r['source_reused'] for r in evidence),
        verified_previous_raw_files=len(previous['raw_file_digests']),
        previous_binding_ddg_candidates=sum(r['binding_ddG_kcal_mol'] is not None for r in coverage),
        binding_ddg_controls=dict(n=len(controls),spearman_rho=float(stat.statistic),p=float(stat.pvalue),
            scope='Small selected historical control panel. Monte Carlo SE is not predictive error. Binding-ddG is not thermal stability.'),
        Adaptyv_new_lab_measurements=0,
        validation=read(RUN/'validation/explicit-reference-receipt.json')['validation_report'])
    (RUN/'coverage-summary.json').write_text(json.dumps(metrics,indent=2))
    print(json.dumps(metrics,indent=2))

if __name__=='__main__':main()
