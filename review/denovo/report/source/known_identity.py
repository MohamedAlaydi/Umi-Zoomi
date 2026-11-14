"""Small-reference diagnostic; this is NOT the competition's database search."""
import argparse
import json
from pathlib import Path
from immunum import Annotator
from biotite.sequence import ProteinSequence
from biotite.sequence.align import align_optimal, SubstitutionMatrix


def comparisons(items,refs):
    ann=Annotator(chains=['H'],scheme='imgt',min_confidence=.1)
    matrix=SubstitutionMatrix.std_protein_matrix()
    def domain(seq):
        result=ann.number(seq)
        if result.error:raise ValueError('Cannot extract a heavy variable domain')
        return seq[result.query_start:result.query_end+1]
    references=[(r['rcsb_id'],domain(r['entity_poly']['pdbx_seq_one_letter_code_can'])) for r in refs]
    output=[]
    for item in items:
        seq=domain(item['heavy_variable']);scores=[]
        for name,ref in references:
            alignment=align_optimal(ProteinSequence(seq),ProteinSequence(ref),matrix,
                gap_penalty=-10,terminal_penalty=True,max_number=1)[0]
            trace=alignment.trace;present=(trace>=0).all(axis=1)
            matches=sum(seq[i]==ref[j] for i,j in trace[present])
            scores.append(dict(reference=name,identity_over_alignment=matches/len(trace),
                query_coverage=int(present.sum())/len(seq),alignment_columns=len(trace)))
        output.append(dict(query=item['query'],best=max(scores,key=lambda x:x['identity_over_alignment']),
            comparisons=scores,scope=f'{len(references)} known PDB antibody references only; not official validation'))
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidates',type=Path)
    parser.add_argument('references',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    items=json.loads(args.candidates.read_text())
    refs=json.loads(args.references.read_text())['polymer_entities']
    rows=comparisons(items,refs)
    args.output.write_text(json.dumps(rows,indent=2))
    print(json.dumps({'n':len(rows),'matches_at_least_70pct':sum(r['best']['identity_over_alignment']>=.7 for r in rows),
        'min_best_identity':min((r['best']['identity_over_alignment'] for r in rows),default=None),
        'max_best_identity':max((r['best']['identity_over_alignment'] for r in rows),default=None)},indent=2))


if __name__=='__main__':main()
