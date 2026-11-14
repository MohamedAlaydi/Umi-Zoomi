"""Replay the saved review in a temporary directory using its frozen inputs."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
EVIDENCE = HERE/"evidence"


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle,"sha256").hexdigest()


def verify_files():
    for line in (EVIDENCE/"SHA256SUMS").read_text().splitlines():
        recorded, name = line.split("  ",1)
        if digest(EVIDENCE/name) != recorded:
            raise ValueError(f"Changed evidence file: {name}")


def unpack(scratch):
    inputs = json.loads((EVIDENCE/"replay-inputs.json").read_text())
    late_inputs = json.loads((EVIDENCE/"late-inputs.json").read_text())
    if set(inputs) & set(late_inputs):
        raise ValueError("Duplicate paths across input snapshots")
    inputs.update(late_inputs)
    for name in sorted({r["archive"] for r in inputs.values()}):
        expected = {p for p,v in inputs.items() if v["archive"] == name}
        with tarfile.open(EVIDENCE/name) as arc:
            members = arc.getmembers()
            if (len(members) != len(expected) or {m.name for m in members} != expected
                or not all(m.isfile() for m in members)):
                raise ValueError(f"Unexpected archive contents: {name}")
            arc.extractall(scratch,filter="data")
    for rel, rec in inputs.items():
        if digest(scratch/rel) != rec["sha256"]:
            raise ValueError(f"Changed replay input: {rel}")
    return len(inputs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluate",type=Path,metavar="PAIRED_CSV",
                        help="Apply the frozen sequence baseline to a new Fab CSV")
    args = parser.parse_args()
    verify_files()
    env = dict(os.environ, OPENBLAS_NUM_THREADS="2", OMP_NUM_THREADS="2", MKL_NUM_THREADS="2",
               MPLBACKEND="Agg", PYTHONDONTWRITEBYTECODE="1")
    with tempfile.TemporaryDirectory(prefix="team14-review-") as temp:
        root = Path(temp)
        env["MPLCONFIGDIR"] = str(root/".matplotlib")
        count = unpack(root)
        code = root/"review"
        code.mkdir()
        for script in HERE.glob("*.py"):
            shutil.copyfile(script,code/script.name)
        results = root/"results"
        results.mkdir()
        def run(*args, stdout=None):
            subprocess.run([sys.executable,*map(str,args)],cwd=root,env=env,stdout=stdout,check=True)
        if args.evaluate is not None:
            run(code/"evaluate_pairs.py",args.evaluate.resolve())
            return
        run("-m","unittest","discover","-s",code,"-p","test_*.py")
        reports = ["assay_transfer","split_check","structure_checks","vhh_controls","completed_batches"]
        for name in reports:
            with (results/(name+".json")).open("xb") as handle:
                run(code/(name+".py"),stdout=handle)
        with (results/"panel.csv").open("xb") as handle:
            run(code/"panel.py",results/"structure_checks.json",stdout=handle)
        with (results/"late_comparison.json").open("xb") as handle:
            run(code/"late_comparison.py",results/"structure_checks.json",results/"panel.csv",stdout=handle)
        run(code/"plot_evidence.py",results,results/"assay-and-contacts.png")
        for output in sorted(results.iterdir()):
            if digest(output) != digest(EVIDENCE/output.name):
                raise ValueError(f"Replay differs from frozen evidence: {output.name}")
            print(f"Identical  {output.name}",flush=True)
        print(f"Verified {count} original inputs in isolation.",flush=True)


if __name__ == "__main__":
    main()
