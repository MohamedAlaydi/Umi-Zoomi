"""Audit frozen campaign artifacts without network access or job submission."""
import csv,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from collect_campaign import ROOT,RUN,coordinates


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((RUN/name).read_text())
def table(path):return list(csv.DictReader(path.open()))


def main():
    checks=[]
    def check(name,condition,detail):
        checks.append(dict(check=name,passed=bool(condition),detail=detail))
        if not condition:raise AssertionError(name+': '+str(detail))
    local=read('local-candidates.json');pilot=read('pilot-candidates.json');anti=read('antifold-candidates.json')
    diagnostic=read('canonical-cys-variants.json')
    check('design counts',len(local)==64 and len(pilot)==16 and len(anti)==16,{'backbone_designs':80,'sequence_optimization':16,'cysteine_diagnostics':len(diagnostic)})
    check('unique campaign sequence IDs',len({r['query'] for r in local+pilot+anti+diagnostic})==111,111)
    for row in local+pilot:
        path=ROOT/row['structure'];assert digest(path)==row['structure_sha256']
        chains,_=coordinates(path);assert sum(v['sequence']==row['heavy_variable'] for v in chains.values())==1
    check('generated structure hashes and exact binder sequences',True,80)
    verified_artifacts=0
    for file in RUN.glob('*/download_receipt.json'):
        receipt=json.loads(file.read_text())
        assert digest(file.parent/'artifacts.zip')==receipt['archive_sha256']
        for item in receipt['artifacts']:
            assert digest(file.parent/'artifacts'/item['path'])==item['sha256'];verified_artifacts+=1
    check('downloaded archive and artifact hashes',True,verified_artifacts)
    sub=table(RUN/'abguard-final/submission.csv');receipt=read('abguard-final/explicit-reference-receipt.json')
    check('reference-checked input hash',digest(RUN/'abguard-final/submission.csv')==receipt['input_sha256'],len(sub))
    novelty=table(RUN/'abguard-final/novelty-reference-checked.csv')
    check('reference lookup has no missing novelty verdict',len(novelty)==131 and all(r['is_novel_enough'] in ['true','false'] for r in novelty),131)
    raw=table(RUN/'abguard-final/novelty.csv')
    check('CLI report skip was explicitly caught',any(not r['is_novel_enough'] for r in raw),'Raw CLI report contains unknown verdicts; never counted as passes')
    cli=table(RUN/'abguard-final/validated.csv');direct=table(RUN/'abguard-final/validated-reference-checked.csv')
    check('CLI team validation equals explicit-reference adapter', {r['sequence_id'] for r in cli}=={r['sequence_id'] for r in direct} and len(cli)==127,127)
    check('existing optimization controls preserved',sum(r['sequence_id'].startswith('existing_') for r in cli)==20,20)
    liability={r['sequence_id']:r for r in read('abguard-final/liabilities.json')}
    selected=read('nanobodybuilder-inputs.json');ids={r['candidate'] for r in selected}
    check('selected candidates pass installed validator',all(liability[q]['is_valid'] and liability[q]['novelty_class']=='de_novo' and liability[q]['cdrh3_min_distance']>=2 for q in ids),sorted(ids))
    searches=read('variable-rcsb-sequence-searches.json');zero={r['value']['query'] for r in searches if r['status']=='fulfilled' and r['value']['result']['total_count']==0}
    check('selected RCSB zero-hit receipts',ids==zero,'70% RCSB threshold; limited database scope')
    ident={r['query']:r for r in read('local-final-known-identity.json')}
    check('selected small-reference global identity <70%',all(ident[q]['best']['identity_over_alignment']<.7 for q in ids),{q:ident[q]['best'] for q in ids})
    provided=read('provided-HER2-reference-check.json')
    for name,expected in provided['source_hashes'].items():assert digest(ROOT/name)==expected
    check('all525063 provided HER2 CDRH3s checked independently',
        provided['unique_IMGT_CDRH3']==525063 and {r['candidate'] for r in provided['candidates']}==ids and
        all(r['passes_two_mutations'] and r['cdrh3_imgt']==liability[r['candidate']]['cdrh3'] for r in provided['candidates']),
        {r['candidate']:r['min_distance_provided_imgt'] for r in provided['candidates']})
    anti_ident=read('antifold-final-known-identity.json')
    check('optimized variants with known matches held back',all(r['best']['identity_over_alignment']>=.7 for r in anti_ident),16)
    evidence=read('local-refold-evidence.json');check('completed complex predictions',len(evidence)==32 and all(r['status']=='ok' for r in evidence),{'blind':27,'initial_guess':5})
    for row in evidence:
        assert digest(ROOT/row['structure'])==row['structure_sha256']
        assert len(set(row['chain_roles'].values()))==len(row['chain_roles'])
    check('cofold role maps and artifact hashes',True,len(evidence))
    # First AF2-IG transport failed; fixed inputs preserve every coordinate value.
    for path in (RUN/'design-initial-guess-af2ig-format-fix').glob('*.cif'):
        a,aa=coordinates(path);b,bb=coordinates(RUN/'design-initial-guess-af2ig'/path.name)
        assert a==b and np.array_equal(aa[2],bb[2])
        assert 'pdbx_PDB_ins_code' in path.read_text()
    check('format correction preserves atoms, residues and coordinates',True,5)
    nbb=read('nanobodybuilder-evidence.json');n_models=0
    for row in nbb:
        assert row['exact_sequence_verified']
        for model in row['models']:
            assert digest(ROOT/model['path'])==model['sha256'];n_models+=1
    check('monomer ensemble sequence and hash receipts',n_models==15,{'sequences':3,'structures':n_models,'not_independent_experimental_samples':True})
    calibration=read('regional-calibration.json')
    for name,sha in calibration['input_hashes'].items():assert digest(ROOT/name)==sha
    rows=table(RUN/'regional-calibration.csv')
    check('calibration sample units',len(rows)==30 and calibration['n_structures']==90 and calibration['statistics']['ca_nac']['n_constructs']==25 and all(int(r['n_seeds'])==3 for r in rows),{'constructs':30,'quantified_KD':25,'structures':90})
    check('calibration superiority remains unproven',calibration['paired_NAC_minus_ipTM']['paired_bootstrap_ci95'][0]<0<calibration['paired_NAC_minus_ipTM']['paired_bootstrap_ci95'][1],calibration['paired_NAC_minus_ipTM'])
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'passed','n_checks':len(checks),'checks':checks,
       'scope':'Computational and provenance audit. No new expression, binding, competition or Tm measurements.'}
    (RUN/'quality-audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
