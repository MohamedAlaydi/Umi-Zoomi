#!/usr/bin/env python3
"""Summarise a refold_metrics.csv: the ranking numbers, the designed CDRH3,
and whether each design would survive the novelty filter.

CDRH3 is residues 99-108 of the designed chain (1-based), per
Data/12-her2/her2_cdrh3.yaml, which fixes B/*/[1-98, 109-120] and lets the
model generate 99-108.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.expanduser("~/team14/scripts"))
import novelty  # noqa: E402

CDRH3_FROM, CDRH3_TO = 99, 108  # 1-based, inclusive

COLS = ["query_id", "min_ipae", "iptm", "binder_plddt", "binder_ptm",
        "target_aligned_binder_rmsd", "backbone_rmsd"]


def main(path):
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
    if not rows:
        sys.exit("no rows")

    print(f"{len(rows)} refolded design(s) from {path}\n")

    print("ranking numbers (the pass column is empty for HER2, so rank on these)")
    hdr = f"{'query':<16}" + "".join(f"{c.replace('_',' '):>26}" for c in COLS[1:])
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        line = f"{r.get('query_id',''):<16}"
        for c in COLS[1:]:
            v = r.get(c, "")
            try:
                v = f"{float(v):.3f}"
            except (TypeError, ValueError):
                v = v or "-"
            line += f"{v:>26}"
        print(line)

    print("\ndesigned CDRH3 and novelty")
    pool = novelty.load()
    total = sum(a.shape[0] for a in pool.values())
    print(f"(checked against {total:,} provided CDRH3)\n")
    print(f"{'query':<16} {'CDRH3':<14} {'minDist':>7} {'%idTz':>6}  verdict")
    print("-" * 60)
    for r in rows:
        seq = (r.get("binder_sequence") or "").strip()
        if not seq:
            print(f"{r.get('query_id',''):<16} (no binder_sequence in the csv)")
            continue
        cdr = seq[CDRH3_FROM - 1:CDRH3_TO]
        d, nearest = novelty.min_distance(cdr, pool)
        idt = novelty.identity_to_trastuzumab(cdr)
        bad = d < 2 or idt > 70.0
        note = "REJECTED" if bad else "ok"
        if "C" in cdr:
            note += f" (has {cdr.count('C')} Cys)"
        print(f"{r.get('query_id',''):<16} {cdr:<14} {d:>7} {idt:>5.0f}%  {note}")
        if d < 2:
            print(f"{'':<16} nearest provided: {nearest}")
        print(f"{'':<16} full binder, {len(seq)} aa: {seq}")


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
        "~/team14/data/rfd4-proteina/docs/runs/her2-baseline/scored-boltz2/refold_metrics.csv")
    main(p)
