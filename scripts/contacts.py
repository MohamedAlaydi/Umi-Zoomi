#!/usr/bin/env python3
"""Which HER2 residues does trastuzumab actually touch?

Reads the hackathon's own her2_fv_1n8z.cif and computes the real contact
map, so the epitope we must preserve is measured from the structure we are
designing against, not taken from a paper about a different numbering.

Chains in that file: A = light chain, B = heavy chain, C and D = HER2
domain IV (split at its unresolved loop 581-590).
"""
import math
import os
import sys
from collections import defaultdict

CIF = os.path.expanduser(
    "~/team14/data/rfd4-proteina/docs/Data/12-her2/her2_fv_1n8z.cif")

CUTOFF = 4.5           # heavy-atom contact, the usual interface cutoff
CDRH3 = range(99, 109)  # the residues the model redesigns, chain B

THREE_TO_ONE = {
    'ALA': 'A', 'ARG': 'R', 'ASN': 'N', 'ASP': 'D', 'CYS': 'C', 'GLN': 'Q',
    'GLU': 'E', 'GLY': 'G', 'HIS': 'H', 'ILE': 'I', 'LEU': 'L', 'LYS': 'K',
    'MET': 'M', 'PHE': 'F', 'PRO': 'P', 'SER': 'S', 'THR': 'T', 'TRP': 'W',
    'TYR': 'Y', 'VAL': 'V',
}


def read_atoms(path):
    """Minimal mmCIF atom_site reader: (chain, resnum, resname, atom, x,y,z)."""
    atoms = []
    cols, in_loop, header = {}, False, []
    with open(path) as fh:
        for line in fh:
            s = line.strip()
            if s.startswith("_atom_site."):
                if not in_loop:
                    in_loop, header = True, []
                header.append(s.split(".", 1)[1])
                continue
            if in_loop and header and not s.startswith("_"):
                if not cols:
                    cols = {name: i for i, name in enumerate(header)}
                if s.startswith("#") or not s:
                    if atoms:
                        break
                    continue
                if not s.startswith(("ATOM", "HETATM")):
                    continue
                f = s.split()
                try:
                    atoms.append((
                        f[cols["auth_asym_id"]],
                        int(f[cols["auth_seq_id"]]),
                        f[cols["label_comp_id"]],
                        f[cols["label_atom_id"]],
                        float(f[cols["Cartn_x"]]),
                        float(f[cols["Cartn_y"]]),
                        float(f[cols["Cartn_z"]]),
                    ))
                except (KeyError, ValueError, IndexError):
                    continue
    return atoms


def main():
    if not os.path.exists(CIF):
        sys.exit(f"missing {CIF}")
    atoms = [a for a in atoms_all if a[3] != "H"] if (atoms_all := read_atoms(CIF)) else []
    if not atoms:
        sys.exit("no atoms parsed")

    chains = defaultdict(list)
    for a in atoms:
        chains[a[0]].append(a)
    print("chains in the file:")
    for c, ats in sorted(chains.items()):
        res = sorted({a[1] for a in ats})
        print(f"  {c}: {len(ats):5d} atoms, residues {res[0]}-{res[-1]} ({len(res)} resolved)")
    print()

    antibody = [a for a in atoms if a[0] in ("A", "B")]
    target = [a for a in atoms if a[0] in ("C", "D")]
    if not antibody or not target:
        sys.exit("expected chains A/B (antibody) and C/D (HER2)")

    # bucket the target atoms into a grid so this stays fast
    cell = CUTOFF
    grid = defaultdict(list)
    for a in target:
        key = (int(a[4] // cell), int(a[5] // cell), int(a[6] // cell))
        grid[key].append(a)

    # her2 residue -> set of antibody residues touching it
    epitope = defaultdict(set)
    # antibody residue -> set of her2 residues
    paratope = defaultdict(set)
    cdrh3_contacts = defaultdict(set)

    for a in antibody:
        kx, ky, kz = int(a[4] // cell), int(a[5] // cell), int(a[6] // cell)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for b in grid.get((kx + dx, ky + dy, kz + dz), ()):
                        d = math.dist(a[4:7], b[4:7])
                        if d <= CUTOFF:
                            her2 = (b[0], b[1], b[2])
                            ab = (a[0], a[1], a[2])
                            epitope[her2].add(ab)
                            paratope[ab].add(her2)
                            if a[0] == "B" and a[1] in CDRH3:
                                cdrh3_contacts[her2].add(ab)

    one = lambda rn: THREE_TO_ONE.get(rn, "X")

    print(f"THE EPITOPE: HER2 residues within {CUTOFF} A of trastuzumab")
    print(f"{len(epitope)} residues\n")
    print(f"{'HER2':<12} {'contacts':>8}  touched by")
    print("-" * 72)
    for (ch, num, rn) in sorted(epitope, key=lambda k: (k[0], k[1])):
        partners = sorted(epitope[(ch, num, rn)], key=lambda p: (p[0], p[1]))
        tag = "  <-- CDRH3" if (ch, num, rn) in cdrh3_contacts else ""
        s = ", ".join(f"{p[0]}{p[1]}{one(p[2])}" for p in partners[:6])
        if len(partners) > 6:
            s += f", +{len(partners)-6} more"
        print(f"{one(rn)}{num} ({ch}){'':<3} {len(partners):>8}  {s}{tag}")

    print()
    print("WHAT CDRH3 ITSELF TOUCHES (the part we redesign)")
    if cdrh3_contacts:
        for (ch, num, rn) in sorted(cdrh3_contacts, key=lambda k: (k[0], k[1])):
            partners = sorted(cdrh3_contacts[(ch, num, rn)], key=lambda p: p[1])
            print(f"  HER2 {one(rn)}{num} ({ch})  <-  "
                  + ", ".join(f"H{p[1]}{one(p[2])}" for p in partners))
    else:
        print("  none: CDRH3 makes no contact with HER2 in this structure")

    print()
    print("PARATOPE: which antibody residues do the binding")
    by_chain = defaultdict(list)
    for (ch, num, rn), v in paratope.items():
        by_chain[ch].append((num, rn, len(v)))
    for ch in sorted(by_chain):
        label = "light chain" if ch == "A" else "heavy chain"
        rs = sorted(by_chain[ch])
        print(f"  {label} ({ch}): "
              + ", ".join(f"{one(rn)}{num}" for num, rn, _ in rs))

    print()
    print("THE CHECK TO AUTOMATE")
    core = sorted(
        (k for k in epitope if len(epitope[k]) >= 3),
        key=lambda k: -len(epitope[k]))[:10]
    print("  A design preserves the epitope if it still contacts most of:")
    print("  " + ", ".join(f"{one(rn)}{num}({ch})" for ch, num, rn in core))


if __name__ == "__main__":
    main()
