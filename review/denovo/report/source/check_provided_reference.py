"""Exact novelty distance to both provided HER2 tables, with consistent IMGT loops."""
import csv,hashlib,io,json,zipfile
from collections import Counter
from datetime import datetime,timezone
from immunum import Annotator
from rapidfuzz import process
from rapidfuzz.distance import Levenshtein
from collect_campaign import ROOT,RUN


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    folder=ROOT/'data/her2-trastuzumab';spr=folder/'trastuzumab_her2_spr_all_768.csv';facs=folder/'tz_her2_facs_3classes_524346.csv.zip'
    sprrows=list(csv.DictReader(spr.open()));parent=sprrows[0]
    prefix,suffix=parent['vh_sequence'].split(parent['cdrh3']);ann=Annotator(chains=['H'],scheme='imgt',min_confidence=.1)
    full=ann.segment(parent['vh_sequence']).cdr3;assert full=='SR'+parent['cdrh3']+'Y'
    raw=set();loops=set();sources=Counter();cache={}
    def add(row,source):
        core=row['cdrh3'];seq=row['vh_sequence'];raw.add(core);sources[source]+=1
        if seq==prefix+core+suffix:loop='SR'+core+'Y'
        else:
            if seq not in cache:cache[seq]=ann.segment(seq).cdr3
            loop=cache[seq]
        if not loop:raise ValueError('No IMGT H3 for provided VH')
        loops.add(loop)
    with zipfile.ZipFile(facs) as z:
        paths=[n for n in z.namelist() if n.endswith('.csv') and not n.startswith('__MACOSX/')];assert len(paths)==1
        with io.TextIOWrapper(z.open(paths[0])) as f:
            for row in csv.DictReader(f):add(row,'FACS')
    for row in sprrows:add(row,'SPR')
    loops=sorted(loops);raw=sorted(raw);candidates=[]
    for entry in json.loads((RUN/'nanobodybuilder-inputs.json').read_text()):
        candidate=next(r for r in json.loads((RUN/'local-candidates.json').read_text()) if r['query']==entry['candidate'])
        loop=ann.segment(candidate['heavy_variable']).cdr3
        best=process.extractOne(loop,loops,scorer=Levenshtein.distance);rawbest=process.extractOne(loop,raw,scorer=Levenshtein.distance)
        candidates.append(dict(candidate=entry['candidate'],cdrh3_imgt=loop,min_distance_provided_imgt=best[1],
            closest_provided_imgt=best[0],min_distance_raw_column=rawbest[1],closest_raw_column=rawbest[0],
            passes_two_mutations=best[1]>=2))
    result=dict(utc=datetime.now(timezone.utc).isoformat(),source_rows=dict(sources),unique_raw_CDRH3=len(raw),
        unique_IMGT_CDRH3=len(loops),IMGT_lengths=dict(Counter(map(len,loops))),
        normalization='Verified FACS/trastuzumab VH equals fixed prefix+core+suffix; full IMGT CDRH3 is SR+core+Y. Non-trastuzumab SPR domains numbered directly.',
        source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [facs,spr]},candidates=candidates,
        scope='Exact Levenshtein against all rows in the two local provided tables; independent of installed abguard bundle. Not full-sequence novelty.')
    (RUN/'provided-HER2-reference-check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()
