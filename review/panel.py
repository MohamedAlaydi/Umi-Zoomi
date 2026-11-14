"""Propose a 20-slot order using the existing matched run 006 panel only."""
import csv
import hashlib
import json
import sys
from pathlib import Path


def hamming(left, right):
    if len(left) != len(right):
        raise ValueError("Expected equal-length CDRH3 loops")
    return sum(a != b for a,b in zip(left,right))


def prioritize(batch):
    ref, = [x for x in batch if x["query"] == "trastuzumab_wt"]
    pool = [x for x in batch if x["local_margin"] and x["source"] != "control"]
    free = [x for x in batch if x["local_margin"] and x["query"].startswith("r004_")]
    def seq(x):
        return (-x["blosum62"], -x["footprint"]["4.5"]["jaccard"], -x["metrics"]["VH_min"], x["query"])
    def geometry(x):
        return (-x["metrics"]["VH_min"], -x["footprint"]["4.5"]["jaccard"], -x["blosum62"],x["query"])
    above = [x for x in pool if x["metrics"]["VH_min"] > ref["metrics"]["VH_min"] + 1e-9]
    below = [x for x in pool if x["metrics"]["VH_min"] <= ref["metrics"]["VH_min"] + 1e-9]
    ordered = []
    def add(candidates, key, reason):
        for row in sorted(candidates,key=key):
            distances = [hamming(row["cdrh3"],item["cdrh3"]) for item in ordered]
            if distances and min(distances) < 3:
                continue
            ordered.append(dict(query=row["query"],cdrh3=row["cdrh3"],selection=reason,
                                source=row["source"],blosum62=row["blosum62"],
                                min_vh_pair=round(row["metrics"]["VH_min"],5),
                                delta_vh_pair=round(row["metrics"]["VH_min"]-ref["metrics"]["VH_min"],5),
                                footprint_jaccard_4_5=round(row["footprint"]["4.5"]["jaccard"],5),
                                local_distance=row["local_distance"],official_validation="pending",
                                min_distance_to_earlier=min(distances) if distances else None))
            return True
        return False
    choices = [(above, seq, "highest sequence score among candidates above WT pair score"),
               (below, seq, "sequence-led contrast at or below WT pair score"),
               (above, geometry, "geometry-led independent sequence"),
               (free, geometry, "free-loop generator comparator")]
    for candidates,key,reason in choices:
        if not add(candidates,key,reason):
            raise ValueError(f"No eligible candidate for predeclared slot: {reason}")
    while len(ordered) < 20:
        if not add(pool,seq,"sequence baseline then footprint and VH pair score"):
            break
    return ordered


def main():
    from assay_transfer import ROOT, sha256
    data = json.loads(Path(sys.argv[1]).read_text())
    panel = prioritize(data["batch"])
    if len(panel) != 20:
        raise ValueError(f"Only {len(panel)} slots filled")
    query_file, = (ROOT/"runs").glob("006-*/out/prepared/holo/queries.json")
    if sha256(query_file) != data["input_sha256"]:
        raise ValueError("The full chains must come from the same verified input batch")
    inputs = {query["query_id"]:query["chains"]
              for query in json.loads(query_file.read_text())["queries"]}
    for row in panel:
        pair = {chain["chain_id"]:chain["sequence"] for chain in inputs[row["query"]]}
        vh, vl = pair["B"], pair["A"]
        if vh[98:108] != row["cdrh3"] or len(vh) + len(vl) != 227:
            raise ValueError("Variable-chain sequences disagree with ranked record")
        row.update(format="Fab", heavy_variable=vh, light_variable=vl,
                   pair_sha256=hashlib.sha256(f"VH={vh}\nVL={vl}\n".encode("ascii")).hexdigest())
    writer = csv.DictWriter(sys.stdout,fieldnames=["rank",*panel[0]],lineterminator="\n")
    writer.writeheader()
    for rank,row in enumerate(panel,1):
        writer.writerow(dict(rank=rank,**row))


if __name__ == "__main__":
    main()
