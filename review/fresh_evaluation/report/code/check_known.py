"""Independently recheck VHH identity against freshly retrieved PDB hit sequences."""
import json,subprocess
from biotite.sequence import ProteinSequence
from biotite.sequence.align import align_optimal,SubstitutionMatrix
from rapidfuzz.distance import Levenshtein
from prepare import RUN,write_csv


def main():
 entities=json.loads((RUN/'fresh-rcsb-hit-entities.json').read_text())['polymer_entities']
 entities+=json.loads((RUN/'fresh-rcsb-extra-hit-entities.json').read_text())['polymer_entities']
 entities+=json.loads((RUN.parent/'011-codex-denovo-vhh/expanded-antibody-references.json').read_text())['polymer_entities']
 entities=list({e['rcsb_id']:e for e in entities}.values())
 # Tags/constant domains are removed using the same public numbering library.
 code="import json,sys;from immunum import Annotator;a=Annotator(chains=['H'],scheme='imgt',min_confidence=.1);print(json.dumps([''.join(a.number(s).numbering.values()) for s in json.load(sys.stdin)]))"
 seqs=[r['entity_poly']['pdbx_seq_one_letter_code_can'] for r in entities]
 out=subprocess.run(['/home/hackathon/tools/abguard-venv/bin/python','-c',code],input=json.dumps(seqs),text=True,capture_output=True,check=True)
 numbered=json.loads(out.stdout);refs=[(e['rcsb_id'],e['rcsb_polymer_entity']['pdbx_description'],s) for e,s in zip(entities,numbered) if s]
 targets=[r for r in json.loads((RUN/'new-job-manifest.json').read_text())['targets'] if r['kind']=='vhh'];rows=[]
 matrix=SubstitutionMatrix.std_protein_matrix()
 for r in targets:
  q=r['heavy_sequence'];scores=[]
  for name,desc,s in refs:
   trace=align_optimal(ProteinSequence(q),ProteinSequence(s),matrix,gap_penalty=-10,terminal_penalty=True,max_number=1)[0].trace
   both=trace[(trace>=0).all(1)];identity=sum(q[i]==s[j] for i,j in both)/len(trace)
   edit_identity=1-Levenshtein.distance(q,s)/max(len(q),len(s))
   scores.append((max(identity,edit_identity),name,desc,identity,edit_identity))
  best=max(scores)
  rows.append(dict(sequence_id=r['sequence_id'],max_identity_conservative_two_definitions=best[0],nearest_entity=best[1],nearest_description=best[2],
   identity_alignment_columns_at_nearest=best[3],identity_normalized_edit_at_nearest=best[4],
   reference_entities=len(refs),under70_in_tested_reference_set=best[0]<.7,universal_known_antibody_novelty='not established; Adaptyv full database unavailable'))
 write_csv(RUN/'fresh-known-antibody-recheck.csv',rows)
 print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
