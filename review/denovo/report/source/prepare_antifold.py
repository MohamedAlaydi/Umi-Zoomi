"""Freeze one 16-sequence CDR optimization around the most self-consistent novel VHH."""
import hashlib,json,re,tarfile
from pathlib import Path
from biotite.structure.io.pdb import PDBFile
from biotite.structure.io.pdbx import CIFFile,get_structure
from immunum import Annotator
from collect_campaign import ROOT,RUN


def main():
    source=RUN/'design-initial-guess-af2ig/novel2_crop119.cif'
    target=ROOT/'nebius/nebius-runs/inputs/run011/antifold';target.mkdir(exist_ok=True)
    atoms=get_structure(CIFFile.read(source),model=1,use_author_fields=False)
    seq=next(r for r in json.loads((RUN/'local-refold-manifest.json').read_text()) if r['name']=='novel2_crop119')['antibody_sequences']['H']
    ann=Annotator(chains=['H'],scheme='imgt').number(seq)
    assert ''.join(ann.numbering.values())==seq
    for old,label in enumerate(ann.numbering,1):
        match=re.fullmatch(r'(\d+)([A-Z]?)',label);assert match
        mask=(atoms.chain_id=='H')&(atoms.res_id==old)
        # Number ascending old positions through a frozen mask array to avoid collisions.
    original_ids=atoms.res_id.copy()
    for old,label in enumerate(ann.numbering,1):
        match=re.fullmatch(r'(\d+)([A-Z]?)',label);mask=(atoms.chain_id=='H')&(original_ids==old)
        atoms.res_id[mask]=int(match[1]);atoms.ins_code[mask]=match[2]
    pdb=PDBFile();pdb.set_structure(atoms);pdb.write(target/'structure.pdb')
    check=PDBFile.read(target/'structure.pdb').get_structure(model=1)
    assert len(check[check.chain_id=='H'])==4*len(seq)
    archive=target/'workload.tar'
    with tarfile.open(archive,'w') as tf:tf.add(target/'structure.pdb',arcname='structure.pdb')
    params=dict(pdb_file='structure.pdb',nanobody_chain='H',nanobody_mode=True,antigen_chain='T',
        custom_chain_mode=True,skip_anarcii_numbering=True,regions='CDRH1 CDRH2 CDRH3',
        num_seq_per_target=16,sampling_temp='0.20',limit_variation=False,seed=20261114)
    receipt=dict(parent='rfd4-variable-sequence-k1__her2_variable_sequence_12_generated',
        selection_reason='Lowest independent NanoBodyBuilder2 monomer CA RMSD of three novelty-screened candidates',
        parent_ca_rmsd=1.1362108922697696,numbering='IMGT via immunum2.1; sequence and insertion codes frozen',
        parameters=params,source_structure=str(source.relative_to(ROOT)),
        source_structure_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        tar_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        scope='CDR inverse folding conditioned on supplied backbone and target; no measured improvement promised')
    (target/'params.json').write_text(json.dumps(params))
    (RUN/'antifold-input-receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
