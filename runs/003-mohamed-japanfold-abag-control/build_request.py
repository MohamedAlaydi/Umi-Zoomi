#!/usr/bin/env python3
"""Build the JapanFold opendde-abag request for the two baseline CDRH3 designs
plus a wild-type trastuzumab control, as one three-target job.

Sequences are read from the baseline run's refold_metrics.csv rather than typed
here, so the chains are exactly what Boltz-2 refolded.

Usage:  python3 build_request.py > request.json
"""
import csv
import json
import sys
from pathlib import Path

BASELINE = Path(
    "/home/hackathon/team14/runs/001-mohamed-her2-baseline/out/scored-boltz2/refold_metrics.csv"
)

# Trastuzumab's own CDRH3 (Kabat), the control arm. Everything else in the VH is
# untouched framework, so swapping this one loop isolates the design.
WT_CDRH3 = "WGGDGFYAMDY"

# The VH is framework + CDRH3 + framework. These two anchors bracket the loop in
# every design the HER2 checkpoint produces.
VH_PREFIX_END = "AVYYCSR"
VH_SUFFIX = "WGQGTLVTVSS"


def chains_of(row):
    """{'A': seq, 'B': seq, ...} from the 'sequences' column."""
    out = {}
    for part in row["sequences"].split(";"):
        cid, seq = part.split(":", 1)
        out[cid] = seq
    return out


def swap_cdrh3(vh, cdrh3):
    i = vh.index(VH_PREFIX_END) + len(VH_PREFIX_END)
    j = vh.rindex(VH_SUFFIX)
    return vh[:i] + cdrh3 + vh[j:]


def to_yaml(chains):
    lines = ["sequences:"]
    for cid in sorted(chains):
        lines.append("  - protein: {id: %s, sequence: %s}" % (cid, chains[cid]))
    return "\n".join(lines) + "\n"


def main():
    rows = list(csv.DictReader(BASELINE.open()))
    if not rows:
        sys.exit("no rows in %s" % BASELINE)

    targets = []

    # Control first: same four chains, trastuzumab's own loop back in chain B.
    wt = chains_of(rows[0])
    wt["B"] = swap_cdrh3(wt["B"], WT_CDRH3)
    targets.append({"name": "trastuzumab_wt", "content": to_yaml(wt)})

    for row in rows:
        targets.append({"name": row["query_id"], "content": to_yaml(chains_of(row))})

    req = {
        "model": "opendde-abag",
        "name": "tz-cdrh3-abag-control",
        "params": {"output_format": "pdb", "write_pae": True},
        "targets": targets,
    }
    json.dump(req, sys.stdout, indent=1)
    sys.stdout.write("\n")

    for t in targets:
        n_res = sum(
            len(line.split("sequence: ")[1].rstrip("}"))
            for line in t["content"].splitlines()
            if "sequence: " in line
        )
        print("%-16s %d residues" % (t["name"], n_res), file=sys.stderr)


if __name__ == "__main__":
    main()
