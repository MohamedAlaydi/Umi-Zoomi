"""Fresh source-level cohort: raw sequences and assays only, no previous rank/scores."""
import csv,hashlib,io,json,sys,tarfile,zipfile
from collections import defaultdict,Counter
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from biotite.structure.io.pdbx import CIFFile,get_structure
from biotite.structure.io.pdb import PDBFile
from rapidfuzz import process
from rapidfuzz.distance import Levenshtein
ROOT=Path(__file__).resolve().parents[2];RUN=ROOT/'runs/014-codex-fresh-evaluation'
AA=dict(zip('ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL'.split(),'ARNDCQEGHILKMFPSTWYV'))


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(p):return list(csv.DictReader(p.open()))
def write_csv(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
 from immunum import Annotator
 RUN.mkdir(exist_ok=True)
 if (RUN/'pool.json').exists():raise ValueError('Frozen raw-input pool already exists')
 ann=Annotator(chains=['H','K','L'],scheme='imgt',min_confidence=.1)
 sprpath=ROOT/'data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv';spr=table(sprpath);parent=spr[0]
 H,L=parent['vh_sequence'],parent['vl_sequence'];prefix,suffix=H.split(parent['cdrh3'])
 records={};sources={str(sprpath.relative_to(ROOT)):sha(sprpath)}
 def add(h,l,source,alias):
  key=hashlib.sha256(f'VH={h}\nVL={l}\n'.encode()).hexdigest()
  if key not in records:records[key]=dict(sequence_id=('fab_' if l else 'vhh_')+key[:12],kind='paired' if l else 'vhh',heavy_sequence=h,light_sequence=l,pair_sha256=key,aliases=[],sources=[])
  records[key]['aliases'].append(alias);records[key]['sources'].append(source)
 for number in ['001','004','005','006','007','010']:
  for p in sorted(ROOT.glob('runs/'+number+'-*/out/prepared/holo/queries.json')):
   doc=json.loads(p.read_text());sources[str(p.relative_to(ROOT))]=sha(p)
   for q in doc['queries']:
    seqs=[c['sequence'] for c in q['chains']]
    hs=[s for s in seqs if s.startswith(prefix) and s.endswith(suffix)]
    if len(hs)!=1 or seqs.count(L)!=1:raise ValueError('Unknown antibody background in raw queries')
    add(hs[0],L,str(p.relative_to(ROOT)),number+':'+q['query_id'])
 # Include every locally generated VHH sequence; later eligibility is freshly checked.
 for p in sorted((ROOT/'runs/011-codex-denovo-vhh').glob('rfd4-*/design/generation/inference_samples/*/*generated.cif')):
  t=next(iter(CIFFile.read(p).values()))['atom_site'];col=lambda n:t[n].as_array(str)
  m=(col('label_asym_id')=='H')&(col('label_atom_id')=='CA')&(col('pdbx_PDB_model_num')=='1')
  if not m.any():raise ValueError('Missing H CAs')
  h=''.join(AA[v] for v in col('label_comp_id')[m]);add(h,'',str(p.relative_to(ROOT)),p.stem);sources[str(p.relative_to(ROOT))]=sha(p)
 # Hash-stratified unseen sequence-only proposals, independent of saved FACS scores.
 p=ROOT/'people/anas/legal-scored.csv';legal=table(p);sources[str(p.relative_to(ROOT))]=sha(p)
 chosen=sorted(legal,key=lambda r:hashlib.sha256(('fresh20261114:'+r['cdrh3']).encode()).hexdigest())[:16]
 for r in chosen:add(prefix+r['cdrh3']+suffix,L,str(p.relative_to(ROOT)),'new_hash_sample:'+r['cdrh3'])
 # Reconstruct every provided IMGT H3 from full VH, proving the core/flank convention.
 loops=set();raw=set();facs=ROOT/'data/her2-trastuzumab/tz_her2_facs_3classes_524346.csv.zip';sources[str(facs.relative_to(ROOT))]=sha(facs)
 with zipfile.ZipFile(facs) as z:
  name,=[n for n in z.namelist() if n.endswith('.csv') and '__MACOSX' not in n]
  for r in csv.DictReader(io.TextIOWrapper(z.open(name))):
   assert r['vh_sequence']==prefix+r['cdrh3']+suffix
   loops.add('SR'+r['cdrh3']+'Y');raw.add(r['cdrh3'])
 for r in spr:loops.add(ann.segment(r['vh_sequence']).cdr3);raw.add(r['cdrh3'])
 assert len(loops)==len(raw)==525063
 loops=sorted(loops);raw=sorted(raw);n_other_seq=0
 for r in records.values():
  result=ann.number(r['heavy_sequence']);seg=ann.segment(r['heavy_sequence']);h3=seg.cdr3
  reasons=[]
  if result.error or result.chain!='H' or result.confidence<.1:reasons.append('not_numberable_heavy')
  if len(r['heavy_sequence'])+len(r['light_sequence'])>250:reasons.append('length')
  if r['heavy_sequence'].count('C')%2 or r['light_sequence'].count('C')%2:reasons.append('unpaired_cysteine_count')
  nearest=process.extractOne(h3,loops,scorer=Levenshtein.distance)
  wt=ann.segment(H).cdr3;distance=Levenshtein.distance(h3,wt);identity=1-distance/max(len(h3),len(wt))
  if r['kind']=='paired':
   if nearest[1]<3:reasons.append('provided_h3_distance_lt3')
   if identity>=.7:reasons.append('wt_imgt_h3_identity_ge70')
  else:
   if nearest[1]<2:reasons.append('provided_h3_distance_lt2')
   if distance<2:reasons.append('wt_imgt_h3_distance_lt2')
  # Do not hard-filter grip, p_high, removal of D/M, or any model confidence.
  r.update(cdrh3_imgt=h3,imgt_h3_distance_to_provided=nearest[1],imgt_h3_nearest_provided=nearest[0],
   imgt_h3_identity_to_wt=identity,numbering_confidence=result.confidence,local_numeric_reasons=reasons,
   local_numeric_pass=not reasons,canonical_cysteines=all(result.numbering.get(i)=='C' for i in ['23','104']),
   old_grip_conserved=(sum(a==b for a,b in zip(r['heavy_sequence'][98:108],parent['cdrh3'])) if r['kind']=='paired' else None))
 (RUN/'pool.json').write_text(json.dumps(list(records.values()),indent=2))
 write_csv(RUN/'pool-submission.csv',[{**{k:r[k] for k in ['sequence_id','kind','heavy_sequence','light_sequence']},'design_description':'Fresh raw-input pool; unranked'} for r in records.values()])
 (RUN/'source-input-hashes.json').write_text(json.dumps(sources,indent=2))
 (RUN/'predeclared.json').write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),
  intent='Fresh evaluation from raw generation inputs and original assays, with new full-ectodomain cofold and native-reference binding-ddG. No old ranking or saved model score used to build pool.',
  candidate_universe='All available raw Fab holo-query files from001/004/005/006/007/010, all64 local VHHs, plus16 deterministic hash-sampled legal proposals.',
  hard_numeric_policy='Conservative published constraints; explicit abguard reference next. Global VHH nearest-known check additional; no claim universal database completeness.',
  measured_endpoints=['KD relative to contemporaneous WT; historical WT sensitivity','competition remains unmeasured','thermal stability remains unmeasured for these constructs'],
  new_cofold=dict(model='mol1',seed=271828,target='full607-residue HER2 ectodomain, native sequence',samples=1,template=False,hotspots=False),
  forbidden_shortcuts=['No best-seed winner selection','No no-fit=proven-negative claim','No confidence=affinity or Tm','No NONINFERIOR declaration using upper CI','No pS without thermal evidence'],
  controls='WT plus fresh historical measured affinity controls not in the old8 StaB control list. Historical outcomes supplied only to evaluator, not model.'),indent=2))
 print(json.dumps({'unique_pool':len(records),'kinds':dict(Counter(r['kind'] for r in records.values())),
   'numeric_pass':dict(Counter(r['kind'] for r in records.values() if r['local_numeric_pass'])),'source_files':len(sources)},indent=2))

if __name__=='__main__':main()
