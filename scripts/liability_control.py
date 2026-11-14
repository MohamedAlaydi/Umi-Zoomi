#!/usr/bin/env python3
"""Run the official abguard liability checker on wild-type trastuzumab and the ranked 20 together.

The pitch claims we remove two documented degradation liabilities, D102 isomerization and
M107 oxidation. Until now that claim had no control: abguard had only ever been run on the
designs, never on the parent, so "removed" and "added" were our words rather than the
tool's. This run puts the parent in the same table and lets abguard say it.

The wild-type heavy chain is not typed in by hand. It is derived from each design by
substituting the parent CDRH3 back into that design's own framework, and the script asserts
that all 20 designs yield the identical parent sequence and that it matches the independent
copy in review/denovo/test_regional.py.

Usage, from the repo root:
    python3 liability_control.py            # build and report, writes into the run dir
"""
import csv
import json
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RANKED = ROOT / "notes/RANKED_CANDIDATES.csv"
OUT = ROOT / "runs/013-claude-liability-control"

ABGUARD = Path("/home/hackathon/tools/abguard-venv/bin/abguard")
REFERENCE = Path("/home/hackathon/tools/abguard-venv/lib/python3.12/site-packages/abguard/reference_data")

WT_CDRH3 = "WGGDGFYAMD"
# independent copy, from review/denovo/test_regional.py
WT_HEAVY_EXPECTED = (
    "EVQLVESGGGLVQPGGSLRLSCAASGFNIKDTYIHWVRQAPGKGLEWVARIYPTNGYTRYADSVKGRFTISADTSKNT"
    "AYLQMNSLRAEDTAVYYCSRWGGDGFYAMDYWGQGTLVTVSS"
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(l):
    """A liability's identity: what it is and exactly where."""
    return (l["tag"], l.get("region"), "/".join(l.get("imgt_positions") or []))


def label(k):
    tag, region, pos = k
    return f"{tag}@{region}:{pos}" if pos else f"{tag}@{region}"


def main():
    rows = list(csv.DictReader(RANKED.open(encoding="utf-8")))
    assert len(rows) == 20, f"expected 20 ranked designs, got {len(rows)}"

    # derive the parent heavy chain from every design, and require unanimity
    derived = set()
    for r in rows:
        h, cdr = r["heavy_variable"], r["cdrh3"]
        assert cdr in h, f"{r['candidate_id']}: cdrh3 {cdr} not found in its own heavy chain"
        derived.add(h.replace(cdr, WT_CDRH3))
    assert len(derived) == 1, f"designs disagree on the parent framework: {len(derived)} variants"
    wt_heavy = derived.pop()
    assert wt_heavy == WT_HEAVY_EXPECTED, "derived parent does not match test_regional.py"

    lights = {r["light_variable"] for r in rows}
    assert len(lights) == 1, "designs do not share one light chain"
    wt_light = lights.pop()

    OUT.mkdir(parents=True, exist_ok=True)
    sub = OUT / "submission.csv"
    with sub.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sequence_id", "kind", "heavy_sequence", "light_sequence", "design_description"])
        w.writerow(["trastuzumab_wt", "paired", wt_heavy, wt_light,
                    "Wild-type trastuzumab Fv, the control. Not a submitted design."])
        for r in rows:
            w.writerow([r["candidate_id"], "paired", r["heavy_variable"], r["light_variable"],
                        f"rank {r['rank']}"])
    print(f"wrote {sub.relative_to(ROOT)} with {len(rows) + 1} rows (parent + 20)")

    # the official checker, same invocation as review/denovo/run_abguard.py
    res = OUT / "result.json"
    cmd = [str(ABGUARD), "team-validate", str(sub), "--all-liabilities",
           "--reference-db", str(REFERENCE), "-o", str(res)]
    print("$ " + " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    if p.returncode != 0:
        sys.exit(f"abguard failed with {p.returncode}")

    data = json.loads(res.read_text(encoding="utf-8"))
    by_id = {d["sequence_id"]: d for d in data}
    assert "trastuzumab_wt" in by_id, "the control is missing from the abguard output"

    parent = {key(l): l for l in by_id["trastuzumab_wt"].get("liabilities", [])}
    print(f"\nparent liabilities, by abguard: {len(parent)}")
    for k, l in sorted(parent.items()):
        print(f"   {label(k):<28} {l['severity']:<7} {l['name']}")

    comp = OUT / "comparison.csv"
    with comp.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "candidate_id", "n_parent", "n_design",
                    "removed_vs_parent", "added_vs_parent", "net", "added_severity_max"])
        lines = []
        for r in rows:
            cid = r["candidate_id"]
            d = by_id.get(cid)
            assert d is not None, f"{cid} missing from abguard output"
            mine = {key(l): l for l in d.get("liabilities", [])}
            removed = sorted(parent.keys() - mine.keys())
            added = sorted(mine.keys() - parent.keys())
            sev = {"high": 3, "medium": 2, "low": 1}
            worst = max((sev.get(mine[k]["severity"], 0) for k in added), default=0)
            worst_s = {3: "high", 2: "medium", 1: "low", 0: ""}[worst]
            w.writerow([r["rank"], cid, len(parent), len(mine),
                        "; ".join(label(k) for k in removed) or "none",
                        "; ".join(label(k) for k in added) or "none",
                        len(mine) - len(parent), worst_s])
            lines.append((int(r["rank"]), cid, removed, added, worst_s))
    print(f"\nwrote {comp.relative_to(ROOT)}")

    print("\nrank cand            removed vs parent                  added vs parent")
    print("-" * 100)
    for rank, cid, removed, added, worst_s in sorted(lines):
        rm = ", ".join(label(k) for k in removed) or "-"
        ad = ", ".join(label(k) for k in added) or "-"
        flag = "  <-- " + worst_s if worst_s in ("high", "medium") else ""
        print(f"{rank:>4} {cid:<15} {rm:<34} {ad}{flag}")

    clean = [c for _, c, _, a, _ in sorted(lines) if not a]
    print(f"\n{len(clean)} of 20 add no new liability the parent did not already have.")
    if clean:
        print("   " + ", ".join(clean))

    (OUT / "input_hashes.txt").write_text(
        f"submission.csv  {sha(sub)}\n"
        f"abguard reference_data manifest.json  "
        f"{sha(REFERENCE / 'manifest.json')}\n",
        encoding="utf-8")
    print("wrote input_hashes.txt")


if __name__ == "__main__":
    main()
