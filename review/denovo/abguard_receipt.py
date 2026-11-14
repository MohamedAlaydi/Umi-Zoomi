"""Explicit-reference receipt using the installed abguard public Python functions.

The restored build's novelty-report CLI calls _reference() with skipped=True by
default. This adapter supplies a reference object explicitly; it does not patch
the validator or change its thresholds. Run with the abguard interpreter.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
from datetime import datetime, timezone

from abguard.annotate import normalize
from abguard.config import PipelineConfig
from abguard.io import read_table
from abguard.novelty import with_novelty, NOVELTY_COLUMNS
from abguard.pipeline import validate_file, flatten
from abguard.reference import cdrh3_reference


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('submission',type=Path)
    parser.add_argument('--reference',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();args.output.mkdir(exist_ok=True)
    config=PipelineConfig()
    reference=cdrh3_reference(args.reference,config=config)
    data=normalize(read_table(args.submission))
    graded=with_novelty(data.lazy(),reference=reference,config=config).collect()
    columns=['sequence_id',*NOVELTY_COLUMNS]
    graded.select(columns).write_csv(args.output/'novelty-reference-checked.csv')
    graded.write_parquet(args.output/'novelty-reference-checked.parquet')
    library,report=validate_file(args.submission,config=config,drop=True,reference=reference)
    flatten(library).write_csv(args.output/'validated-reference-checked.csv')
    counts=graded['is_novel_enough'].value_counts().to_dicts()
    receipt={'utc':datetime.now(timezone.utc).isoformat(),
        'abguard_version':importlib.metadata.version('abguard'),
        'immunum_version':importlib.metadata.version('immunum'),
        'input_sha256':hashlib.sha256(args.submission.read_bytes()).hexdigest(),
        'reference_manifest_sha256':hashlib.sha256((args.reference/'manifest.json').read_bytes()).hexdigest(),
        'reference_manifest':json.loads((args.reference/'manifest.json').read_text()),
        'novelty_verdict_counts':counts,'validation_report':report.model_dump(mode='json'),
        'scope':'Installed-build decisions. Its identity classification compares to trastuzumab, not every known full antibody; task-PDF nearest-known identity remains an additional check.'}
    (args.output/'explicit-reference-receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps({'input':data.height,'validated':report.n_valid,'novelty_verdict_counts':counts},indent=2))


if __name__=='__main__':main()
