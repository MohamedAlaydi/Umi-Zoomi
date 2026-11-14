"""Run the installed validator on exact frozen input sequences; preserve its scope."""
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/011-codex-denovo-vhh'
PACKAGE=Path('/home/hackathon/tools/abguard-venv/lib/python3.12/site-packages/abguard')
REFERENCE=PACKAGE/'reference_data'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    name=sys.argv[1] if len(sys.argv)>1 else 'initial'
    out=RUN/('abguard-'+name);out.mkdir(exist_ok=False)
    rows=[]
    for file in ['pilot-candidates.json','canonical-cys-variants.json','local-candidates.json','antifold-candidates.json']:
        path=RUN/file
        if not path.exists():continue
        for row in json.loads(path.read_text()):
            rows.append(dict(sequence_id=row['query'],kind='vhh',heavy_sequence=row['heavy_variable'],
                             light_sequence='',design_description='run011 '+file))
    for row in csv.DictReader((ROOT/'review/evidence/panel.csv').open()):
        rows.append(dict(sequence_id='existing_'+row['query'],kind='paired',
                         heavy_sequence=row['heavy_variable'],light_sequence=row['light_variable'],
                         design_description='Existing review panel control; not a new design'))
    with (out/'submission.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    receipt={'utc':datetime.now(timezone.utc).isoformat(),'input_rows':len(rows),
        'input_sha256':sha(out/'submission.csv'),
        'package_hashes':{str(p.relative_to(PACKAGE)):sha(p) for p in sorted(PACKAGE.glob('*.py'))},
        'reference_hashes':{p.name:sha(p) for p in sorted(REFERENCE.iterdir()) if p.is_file()},
        'reference_manifest':json.loads((REFERENCE/'manifest.json').read_text()),
        'scope':'Installed restored abguard build, version0.1.0; hash identifies actual code. It classifies against trastuzumab, whereas task PDF describes nearest known antibody. Preserve this discrepancy; do not claim universal nearest-antibody validation.'}
    environment={**os.environ,'POLARS_MAX_THREADS':'4','OMP_NUM_THREADS':'2'}
    steps=[('novelty-report',['novelty-report',str(out/'submission.csv'),'--reference-db',str(REFERENCE),'-o',str(out/'novelty.csv')]),
           ('team-validate',['team-validate',str(out/'submission.csv'),'--reference-db',str(REFERENCE),'--drop','-o',str(out/'validated.csv')]),
           ('all-liabilities',['team-validate',str(out/'submission.csv'),'--all-liabilities','--reference-db',str(REFERENCE),'-o',str(out/'liabilities.json')])]
    receipt['commands']=[]
    for label,args in steps:
        with (out/(label+'.log')).open('w') as log:
            result=subprocess.run(['/home/hackathon/.local/bin/abguard',*args],env=environment,
                                  stdout=log,stderr=subprocess.STDOUT)
        receipt['commands'].append(dict(name=label,args=args,exit_code=result.returncode))
        (out/'receipt.json').write_text(json.dumps(receipt,indent=2))
        print(label,'exit',result.returncode,flush=True)
    print(out,flush=True)


if __name__=='__main__':main()
