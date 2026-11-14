#!/usr/bin/env python3
"""Check a CDRH3 against the novelty filter, locally.

abguard is not installed on our VM, so this reimplements the two numeric
rules the organisers published, to catch designs that would be rejected at
submission before we waste a refold on them. It is NOT the official tool:
treat a pass here as "worth refolding", not as "accepted".

The rules, from the task PDF and the Apheris slides:
  optimisation  CDRH3 identity to trastuzumab at most 70 %
                AND at least 2 mutations away from every sequence in the
                provided HER2 data (525,063 CDRH3s)
  de novo       under 70 % identity to any known antibody, checked against
                Adaptyv's database, which we do not have. Not checked here.

Usage
  novelty.py build                         cache the provided CDRH3s
  novelty.py check WGHCCLYQLG [more...]    check sequences
  novelty.py check --file designs.txt      one CDRH3 per line, or a FASTA
  novelty.py check --csv designs.csv --col cdrh3
"""
from __future__ import annotations

import argparse
import csv
import io
import os
import sys
import zipfile

import numpy as np

DATA = os.path.expanduser("~/team14/data/her2-trastuzumab")
FACS_ZIP = os.path.join(DATA, "tz_her2_facs_3classes_524346.csv.zip")
SPR_CSV = os.path.join(DATA, "trastuzumab_her2_spr_all_768.csv")
CACHE = os.path.join(DATA, "provided_cdrh3.npz")

# Trastuzumab's own CDRH3, the first row of the SPR table (KD 0.152 nM).
TRASTUZUMAB_CDRH3 = "WGGDGFYAMD"


def _encode(seqs: list[str]) -> np.ndarray:
    """(n, L) uint8 of equal-length sequences."""
    L = len(seqs[0])
    arr = np.frombuffer("".join(seqs).encode("ascii"), dtype=np.uint8)
    return arr.reshape(len(seqs), L)


def build() -> None:
    seen: set[str] = set()

    with zipfile.ZipFile(FACS_ZIP) as z:
        name = next(n for n in z.namelist() if n.endswith(".csv") and "MACOSX" not in n)
        with z.open(name) as fh:
            r = csv.DictReader(io.TextIOWrapper(fh, "utf-8"))
            for row in r:
                s = (row.get("cdrh3") or "").strip().upper()
                if s:
                    seen.add(s)
    print(f"FACS table: {len(seen):,} unique CDRH3")

    n_before = len(seen)
    with open(SPR_CSV, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            s = (row.get("cdrh3") or "").strip().upper()
            if s:
                seen.add(s)
    print(f"SPR table added: {len(seen) - n_before:,} more")

    by_len: dict[int, list[str]] = {}
    for s in seen:
        by_len.setdefault(len(s), []).append(s)

    out = {}
    for L, group in sorted(by_len.items()):
        group.sort()
        out[f"len{L}"] = _encode(group)
        print(f"  length {L}: {len(group):,}")
    np.savez_compressed(CACHE, **out)
    print(f"total {len(seen):,} unique CDRH3 -> {CACHE}")


def load() -> dict[int, np.ndarray]:
    if not os.path.exists(CACHE):
        sys.exit(f"no cache yet, run: {sys.argv[0]} build")
    z = np.load(CACHE)
    return {int(k[3:]): z[k] for k in z.files}


def _levenshtein(a: str, b: str, cap: int) -> int:
    """Edit distance, abandoned once it certainly exceeds cap."""
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        best = cur[0]
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            best = min(best, cur[j])
        if best > cap:
            return cap + 1
        prev = cur
    return prev[-1]


def min_distance(query: str, pool: dict[int, np.ndarray]) -> tuple[int, str]:
    """Smallest distance from query to anything in the provided data."""
    best, best_seq = 10**9, ""

    # same length: vectorised Hamming
    same = pool.get(len(query))
    if same is not None:
        q = np.frombuffer(query.encode("ascii"), dtype=np.uint8)
        d = (same != q).sum(axis=1)
        i = int(d.argmin())
        best = int(d[i])
        best_seq = same[i].tobytes().decode("ascii")

    # other lengths: only those close enough to still beat `best`
    for L, arr in pool.items():
        if L == len(query) or abs(L - len(query)) >= best:
            continue
        for row in arr:
            s = row.tobytes().decode("ascii")
            d = _levenshtein(query, s, best - 1)
            if d < best:
                best, best_seq = d, s
                if best == 0:
                    return best, best_seq
    return best, best_seq


def identity_to_trastuzumab(query: str) -> float:
    t = TRASTUZUMAB_CDRH3
    if len(query) == len(t):
        same = sum(a == b for a, b in zip(query, t))
        return 100.0 * same / len(t)
    d = _levenshtein(query, t, max(len(query), len(t)))
    return 100.0 * (max(len(query), len(t)) - d) / max(len(query), len(t))


def check(queries: list[str]) -> int:
    pool = load()
    total = sum(a.shape[0] for a in pool.values())
    print(f"provided data: {total:,} unique CDRH3\n")

    hdr = f"{'cdrh3':<24} {'len':>3} {'minDist':>7} {'%idTz':>6}  verdict"
    print(hdr)
    print("-" * len(hdr))

    worst = 0
    for q in queries:
        q = q.strip().upper()
        if not q:
            continue
        d, nearest = min_distance(q, pool)
        idt = identity_to_trastuzumab(q)

        reasons = []
        if d < 2:
            reasons.append(f"only {d} mutation(s) from a provided seq ({nearest})")
        if idt > 70.0:
            reasons.append(f"{idt:.0f} % identical to trastuzumab")
        if "C" in q:
            # not a hard rule on its own, but unpaired cysteines are rejected
            reasons.append(f"contains {q.count('C')} cysteine(s), check pairing")

        hard = d < 2 or idt > 70.0
        verdict = "REJECTED" if hard else ("ok, check C" if "C" in q else "ok")
        worst = max(worst, 1 if hard else 0)
        print(f"{q:<24} {len(q):>3} {d:>7} {idt:>5.0f}%  {verdict}")
        for r in reasons:
            print(f"{'':<24} {'':>3} {'':>7} {'':>6}  - {r}")
    return worst


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    c = sub.add_parser("check")
    c.add_argument("seqs", nargs="*")
    c.add_argument("--file")
    c.add_argument("--csv")
    c.add_argument("--col", default="cdrh3")

    a = ap.parse_args()
    if a.cmd == "build":
        build()
        return

    qs = list(a.seqs)
    if a.file:
        with open(a.file, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith(">"):
                    qs.append(line)
    if a.csv:
        with open(a.csv, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get(a.col):
                    qs.append(row[a.col])
    if not qs:
        sys.exit("nothing to check")
    sys.exit(check(qs))


if __name__ == "__main__":
    main()
