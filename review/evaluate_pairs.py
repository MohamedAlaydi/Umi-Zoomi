"""Evaluate previously unseen Fab pairs in the reviewed trastuzumab background."""
import argparse
import csv
import sys

import numpy as np

from assay_transfer import WT, blosum_scores
from structure_checks import REFERENCE_SPR, rows, screen


AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")
FIELDS = ["query","assessment","cdrh3","blosum62","mutations_from_parent",
          "nearest_provided_distance","local_margin","official_validation"]


def evaluate(pair, ref, pool):
    row = dict.fromkeys(FIELDS,"")
    row.update(query=pair["query"],official_validation="pending")
    vh = (pair["heavy_variable"] or "").strip().upper()
    vl = (pair["light_variable"] or "").strip().upper()
    parent = ref["vh_sequence"]
    if not vh or not vl or set(vh+vl) - AMINO_ACIDS:
        row["assessment"] = "missing_or_nonstandard_sequence"
        return row
    if vl != ref["vl_sequence"] or len(vh) != len(parent) or vh[:98] != parent[:98] or vh[108:] != parent[108:]:
        row["assessment"] = "outside_reviewed_background"
        return row
    loop = vh[98:108]
    distance, margin = screen(loop,pool)
    row.update(assessment="reference" if loop==WT else "scored", cdrh3=loop,
               blosum62=blosum_scores([loop])[0],mutations_from_parent=sum(a!=b for a,b in zip(loop,WT)),
               nearest_provided_distance=distance,local_margin=margin)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pairs",help="CSV with query, heavy_variable and light_variable")
    args = parser.parse_args()
    ref = rows(REFERENCE_SPR)[0]
    if ref["cdrh3"] != WT or ref["vh_sequence"][98:108] != WT:
        raise ValueError("Reference chain mapping has changed")
    with np.load(REFERENCE_SPR.with_name("provided_cdrh3.npz"),allow_pickle=False) as archive:
        pool = {int(k.removeprefix("len")):archive[k] for k in archive.files}
    with open(args.pairs,newline="") as source:
        reader = csv.DictReader(source)
        if not {"query","heavy_variable","light_variable"} <= set(reader.fieldnames or []):
            parser.error("Required CSV columns: query,heavy_variable,light_variable")
        pairs = list(reader)
    names = [p["query"] for p in pairs]
    if not names or any(not n or not n.strip() for n in names) or len(set(names)) != len(names):
        parser.error("Provide at least one row, with a unique nonempty query ID on every row")
    writer = csv.DictWriter(sys.stdout,fieldnames=FIELDS,lineterminator="\n")
    writer.writeheader()
    writer.writerows(evaluate(p,ref,pool) for p in pairs)


if __name__ == "__main__":
    main()
