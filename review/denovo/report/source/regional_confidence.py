"""Residue-mapped CA pLDDT summaries, inspired by NAC (arXiv:2610.23136v2).

This is a CA-based adaptation: IMGT regions, exact chain roles, 0..100 CIF
confidence, domain residues only. It is not RIC, an affinity or a Tm predictor.
"""
import re
from collections import defaultdict
import numpy as np
from biotite.structure.io.pdbx import CIFFile
from immunum import Annotator, regions_for

AA=dict(zip('ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL'.split(),
            'ARNDCQEGHILKMFPSTWYV'))


def confidence(path, antibody_chains):
    table=next(iter(CIFFile.read(path).values()))['atom_site']
    col=lambda key,dtype=str:table[key].as_array(dtype)
    chain=col('auth_asym_id') if 'auth_asym_id' in table else col('label_asym_id')
    ca=(col('label_atom_id')=='CA')&(col('pdbx_PDB_model_num',int)==1)
    confidence_values=col('B_iso_or_equiv',float)
    if not np.isfinite(confidence_values[ca]).all() or confidence_values[ca].min()<0 or confidence_values[ca].max()>100:
        raise ValueError('CIF does not contain finite 0..100 CA confidence')
    if confidence_values[ca].max()<=1:
        raise ValueError('Confidence scale or confidence-vs-B-factor provenance unresolved')
    framework=[];cdr=[];whole=[];chains={}
    annotator=Annotator(chains=['H','K','L'],scheme='imgt',min_confidence=.1)
    for cid in antibody_chains:
        mask=ca&(chain==cid)
        if not mask.any():raise ValueError('Missing antibody chain '+cid)
        seq=''.join(AA[a] for a in col('label_comp_id')[mask])
        plddt=confidence_values[mask]
        numbering=annotator.number(seq)
        if numbering.error:raise ValueError('Unnumberable antibody domain '+cid)
        if ''.join(numbering.numbering.values())!=seq[numbering.query_start:numbering.query_end+1]:
            raise ValueError('IMGT numbering order does not map to coordinate sequence')
        regions=regions_for('imgt',numbering.chain)
        fr=[];loop=[]
        for index,label in enumerate(numbering.numbering):
            number=int(re.match(r'\d+',label).group())
            value=float(plddt[numbering.query_start+index])/100
            is_cdr=any(regions[name][0]<=number<=regions[name][1] for name in ['cdr1','cdr2','cdr3'])
            (loop if is_cdr else fr).append(value)
        framework.extend(fr);cdr.extend(loop);whole.extend(fr+loop)
        chains[cid]={'sequence':seq,'detected_type':numbering.chain,'n_framework':len(fr),'n_cdr':len(loop),
                     'framework_ca_plddt':float(np.mean(fr)),'cdr_ca_plddt':float(np.mean(loop))}
    return {'ca_nac':float(np.mean(framework)),'cdr_ca_plddt':float(np.mean(cdr)),
            'antibody_ca_plddt':float(np.mean(whole)),'chains':chains}
