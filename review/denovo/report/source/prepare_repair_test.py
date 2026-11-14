"""Prepare an explicit paired test of restoring the canonical IMGT Cys23/Cys104."""
import json
import hashlib
from pathlib import Path
from immunum import Annotator

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/011-codex-denovo-vhh'
TARGET=''.join((ROOT/'review/denovo/her2_pilot_target.fasta').read_text().splitlines()[1:])


def main():
    records=json.loads((RUN/'pilot-candidates.json').read_text())
    annotator=Annotator(chains=['H','K','L'],scheme='imgt',min_confidence=.1)
    repaired=[]
    for record in records:
        seq=record['heavy_variable'];number=annotator.number(seq)
        if number.error or number.chain!='H':continue
        if ''.join(number.numbering.values())!=seq[number.query_start:number.query_end+1]:
            raise ValueError('Numbered residues do not map to sequence in order')
        indices={label:number.query_start+i for i,label in enumerate(number.numbering)}
        if not all(pos in indices for pos in ['23','104']):continue
        new=list(seq);changes=[]
        for pos in ['23','104']:
            i=indices[pos]
            if seq[i]!='C':
                changes.append({'imgt':pos,'sequence_position_1based':i+1,'from':seq[i],'to':'C'})
                new[i]='C'
        if not changes:continue
        repaired.append({**record,'query':record['query']+'__canonicalCys',
            'parent_query':record['query'],'heavy_variable':''.join(new),'changes':changes,
            'sequence_sha256':hashlib.sha256(''.join(new).encode()).hexdigest(),
            'hypothesis':'Restoring the canonical antibody disulfide may improve fold; no affinity or Tm claim',
            'official_validation':'pending'})
    (RUN/'canonical-cys-variants.json').write_text(json.dumps(repaired,indent=2))
    selected=[]
    for arm in ['directed','unconditioned']:
        eligible=[r for r in repaired if r['arm']==arm]
        selected.extend(sorted(eligible,key=lambda r:-r['model_iptm'])[:2])
    original={r['query']:r for r in records}
    panel=[]
    for repaired_row in selected:
        panel.extend([original[repaired_row['parent_query']],repaired_row])
    (RUN/'paired-refold-panel.json').write_text(json.dumps(panel,indent=2))
    for model in ['openfold3','mol1']:
        destination=RUN/('paired-refold-'+model);destination.mkdir(exist_ok=False)
        targets=[]
        for i,row in enumerate(panel):
            name=f'p{i:02d}'+('_repaired' if row.get('parent_query') else '_original')
            content=f">A|protein\n{row['heavy_variable']}\n>B|protein\n{TARGET}\n"
            targets.append({'name':name,'content':content})
            row.setdefault('refold_names',{})[model]=name
        request={'model':model,'name':'team14-her2-paired-canonical-cys-'+model,
                 'targets':targets,'params':{'output_format':'cif','write_pae':True}}
        (destination/'request.json').write_text(json.dumps(request,indent=2))
    (RUN/'paired-refold-panel.json').write_text(json.dumps(panel,indent=2))
    print(json.dumps({'variants_prepared':len(repaired),'selected_pairs':len(selected),
                      'structures_per_model':len(panel),'models':['openfold3','mol1']},indent=2))


if __name__=='__main__':main()
