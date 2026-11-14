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

# Trastuzumab's own CDRH3, positions 99-108.
WILD_TYPE = "WGGDGFYAMD"

# The four positions that actually contact HER2, measured from 1N8Z by
# scripts/contacts.py. Changing one risks binding and the epitope.
CONTACT = {99: "W", 103: "G", 104: "F", 105: "Y"}

# The two documented chemical liabilities, neither of which contacts HER2.
# D102 isomerization, tied to the low-potency form (Harris 2001, PMID 11270864).
# M107 oxidation, measured in the CT-P6 biosimilar (Hensel 2011, PMID 21390239).
LIABILITY = {102: "D", 107: "M"}

COLS = ["query_id", "min_ipae", "iptm", "binder_plddt", "binder_ptm",
        "target_aligned_binder_rmsd", "backbone_rmsd"]


def hypothesis(cdr):
    """Does this design follow our design hypothesis? -> (verdict, detail)."""
    if len(cdr) != len(WILD_TYPE):
        return "?", f"length {len(cdr)}, expected {len(WILD_TYPE)}"

    kept = [p for p, aa in CONTACT.items() if cdr[p - CDRH3_FROM] == aa]
    lost = [f"{CONTACT[p]}{p}->{cdr[p - CDRH3_FROM]}"
            for p in sorted(CONTACT) if cdr[p - CDRH3_FROM] != CONTACT[p]]
    fixed = [f"{LIABILITY[p]}{p}->{cdr[p - CDRH3_FROM]}"
             for p in sorted(LIABILITY) if cdr[p - CDRH3_FROM] != LIABILITY[p]]

    bits = [f"{len(kept)}/4 contacts kept"]
    if lost:
        bits.append("lost " + ", ".join(lost))
    bits.append(f"{len(fixed)}/2 liabilities fixed"
                + (" (" + ", ".join(fixed) + ")" if fixed else ""))

    if len(kept) == 4 and len(fixed) == 2:
        verdict = "IDEAL"
    elif len(kept) == 4:
        verdict = "grip kept"
    elif len(kept) == 3:
        verdict = "partial"
    else:
        verdict = "grip lost"
    return verdict, "; ".join(bits)


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
    print(f"wild type CDRH3: {WILD_TYPE}   "
          f"contacts HER2 at {', '.join(f'{a}{p}' for p, a in sorted(CONTACT.items()))}   "
          f"liabilities {', '.join(f'{a}{p}' for p, a in sorted(LIABILITY.items()))}\n")
    print(f"{'query':<16} {'CDRH3':<14} {'minDist':>7} {'%idTz':>6}  "
          f"{'novelty':<10} hypothesis")
    print("-" * 86)

    tally = {}
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
            note += f" +Cys"
        verdict, detail = hypothesis(cdr)
        tally[verdict] = tally.get(verdict, 0) + 1
        print(f"{r.get('query_id',''):<16} {cdr:<14} {d:>7} {idt:>5.0f}%  "
              f"{note:<10} {verdict}")
        print(f"{'':<16} {detail}")
        if d < 2:
            print(f"{'':<16} nearest provided: {nearest}")
        print(f"{'':<16} full binder, {len(seq)} aa: {seq}")
        print()

    if tally:
        print("hypothesis tally: "
              + ", ".join(f"{v} {k}" for k, v in sorted(tally.items())))
        print("IDEAL = all four contact residues kept and both liabilities "
              "changed. That is the design we are looking for.")


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
        "~/team14/data/rfd4-proteina/docs/runs/her2-baseline/scored-boltz2/refold_metrics.csv")
    main(p)
