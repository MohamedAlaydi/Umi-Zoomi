"""Verify every sampled framework and compute explicit CDR negative log-likelihood."""
import csv,hashlib,json,re
import numpy as np
from immunum import Annotator,regions_for
from collect_campaign import ROOT,RUN
from known_identity import comparisons


def main():
    folder=RUN/'antifold-novel2';native=json.loads((folder/'result.json').read_text())
    assert native['status']=='succeeded'
    paths={hashlib.sha256(p.read_bytes()).hexdigest():p for p in folder.iterdir() if p.is_file()}
    metadata=json.loads(paths[native['native_result']['files'][0]['file']['sha256']].read_text())
    fasta=paths[metadata['files']['structure_HT.fasta']['sha256']]
    table=paths[metadata['files']['structure_HT.csv']['sha256']]
    with table.open() as f:score_rows=[r for r in csv.DictReader(f) if r['pdb_chain']=='H']
    parent=next(r for r in json.loads((RUN/'local-candidates.json').read_text()) if r['query']=='rfd4-variable-sequence-k1__her2_variable_sequence_12_generated')
    sequence=parent['heavy_variable'];ann=Annotator(chains=['H'],scheme='imgt').number(sequence)
    assert len(score_rows)==len(sequence)
    assert ''.join(r['pdb_res'] for r in score_rows)==sequence
    assert [r['pdb_posins'] for r in score_rows]==list(ann.numbering)
    regions=regions_for('imgt','H')
    mask=np.array([any(regions[r][0]<=int(re.match(r'\d+',label).group())<=regions[r][1] for r in ['cdr1','cdr2','cdr3']) for label in ann.numbering])
    records=[]
    for block in fasta.read_text().split('>')[1:]:
        header,*lines=block.splitlines();seq=''.join(lines).strip()
        if not header.startswith('seq'):assert seq==sequence;continue
        assert len(seq)==len(sequence) and set(seq)<=set('ARNDCQEGHILKMFPSTWYV')
        assert all(a==b for a,b,is_cdr in zip(seq,sequence,mask) if not is_cdr),'Framework mutation outside selected regions'
        nll=-float(np.mean([float(row[aa]) for row,aa,is_cdr in zip(score_rows,seq,mask) if is_cdr]))
        item=dict(query='antifold-novel2-'+header.split()[0],format='VHH',heavy_variable=seq,light_variable='',
            source_arm='AntiFold-CDR-optimization',source_operation=native['operation_id'],
            parent_candidate=parent['query'],framework_preserved=True,parent_backbone=parent['structure'],
            cysteine_count=seq.count('C'),conditional_cdr_nll=nll,
            parent_conditional_cdr_nll=-float(np.mean([float(row[aa]) for row,aa,is_cdr in zip(score_rows,sequence,mask) if is_cdr])),
            sequence_sha256=hashlib.sha256(seq.encode()).hexdigest(),native_header=header,
            scope='Backbone-conditioned inverse folding score; no calibrated binding or thermal prediction')
        records.append(item)
    assert len(records)==16 and len({r['heavy_variable'] for r in records})==16
    (RUN/'antifold-candidates.json').write_text(json.dumps(records,indent=2))
    refs=json.loads((RUN/'local-nearest-reference-sequences.json').read_text())['polymer_entities']
    identity=comparisons(records,refs)
    (RUN/'antifold-known-identity.json').write_text(json.dumps(identity,indent=2))
    with (RUN/'antifold-candidates.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    print(json.dumps({'n':len(records),'frameworks_preserved':True,'unique_sequences':len(records),
        'parent_CDR_NLL':records[0]['parent_conditional_cdr_nll'],
        'variant_CDR_NLL_range':[min(r['conditional_cdr_nll'] for r in records),max(r['conditional_cdr_nll'] for r in records)],
        'subset_identity_below70':[r['query'] for r in identity if r['best']['identity_over_alignment']<.7]},indent=2))

if __name__=='__main__':main()
