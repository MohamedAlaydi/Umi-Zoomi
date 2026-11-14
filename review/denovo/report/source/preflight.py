"""Local sequence preflight for candidate Fab/VHH CSVs; never assigns a track.

Input: query, format (Fab or VHH), heavy_variable, light_variable (empty for VHH).
Optional pair_sha256 is checked against the review's VH=...\nVL=...\n convention.
Install requirements.txt into an isolated environment. JSON is written to stdout.
"""
import argparse
import csv
import hashlib
import importlib.metadata
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from immunum import Annotator

AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")


def pair_hash(heavy, light):
    return hashlib.sha256(f"VH={heavy}\nVL={light}\n".encode()).hexdigest()


def numbering(sequence, chains):
    annotator = Annotator(chains=chains, scheme="imgt", min_confidence=0.1)
    result = annotator.number(sequence)
    if result.error:
        return {"status": "FAIL", "error_kind": result.error_kind}
    regions = annotator.segment(sequence)
    return {"status": "PASS_LOCAL", "chain": result.chain,
            "confidence": result.confidence, "prefix": regions.prefix,
            "postfix": regions.postfix, "cdr3_imgt": regions.cdr3,
            "cdr_lengths": [len(getattr(regions, f"cdr{i}") or "") for i in (1, 2, 3)],
            "canonical_cysteines_present": all(result.numbering.get(p) == "C" for p in ("23", "104"))}


def assess(row, parent):
    heavy, light = row.get("heavy_variable", ""), row.get("light_variable", "")
    fmt = row.get("format", "")
    digest = pair_hash(heavy, light)
    errors = []
    if not row.get("query"):
        errors.append("missing_query")
    if fmt not in ("Fab", "VHH"):
        errors.append("unsupported_format_local_tool_handles_Fab_and_VHH_only")
    if not heavy or not set(heavy + light) <= AMINO_ACIDS:
        errors.append("missing_or_noncanonical_variable_sequence")
    if (fmt == "Fab" and not light) or (fmt == "VHH" and light):
        errors.append("format_chain_count_mismatch")
    if len(heavy + light) > 250:
        errors.append("variable_sequences_exceed_250_residues")
    if row.get("pair_sha256") and row["pair_sha256"] != digest:
        errors.append("sequence_hash_mismatch")
    annotations = {}
    if not errors:
        # Let the model detect a light chain rather than forcing it into an H profile.
        annotations["heavy"] = numbering(heavy, ["H", "K", "L"])
        if light:
            annotations["light"] = numbering(light, ["K", "L"])
        for role, result in annotations.items():
            if result["status"] == "FAIL":
                errors.append(f"{role}_not_numberable_at_0.1")
            elif result["prefix"] or result["postfix"]:
                errors.append(f"{role}_has_flanking_residues_requires_official_extraction")
            if role == "heavy" and result.get("chain") not in (None, "H"):
                errors.append("heavy_detected_as_light_chain")
    # Diagnostic only: this is not the official type-aware database comparison.
    identity = None
    if len(heavy) == len(parent["vh_sequence"]) and len(light) == len(parent["vl_sequence"]):
        identity = sum(a == b for a, b in zip(heavy + light, parent["vh_sequence"] + parent["vl_sequence"])) / len(heavy + light)
    return {"query": row.get("query"), "format": fmt, "pair_sha256": digest,
            "length": len(heavy + light), "local_status": "FAIL_LOCAL" if errors else "PASS_LOCAL",
            "errors": errors, "numbering": annotations,
            "cysteine_counts": {"heavy": heavy.count("C"), "light": light.count("C")},
            "aligned_identity_to_trastuzumab_pair_diagnostic": identity,
            "official_eligibility": "UNVERIFIED", "assigned_track": None,
            "pending_checks": ["official_validator_and_database", "disulfide_pairing",
                               "antigen_chain_mapping", "interface_geometry_and_context",
                               "independent_refolding", "expression", "SPR",
                               "competition", "thermal_measurement"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--parent-spr", required=True, type=Path,
                        help="Organiser's SPR CSV containing the paired WT reference")
    args = parser.parse_args()
    with args.parent_spr.open(newline="") as handle:
        parents = [r for r in csv.DictReader(handle) if r["cdrh3"] == "WGGDGFYAMD"]
    pairs = {(r["vh_sequence"], r["vl_sequence"]) for r in parents}
    if len(pairs) != 1:
        raise ValueError("Expected one unambiguous WT VH/VL pair")
    with args.csv.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    results = [assess(row, parents[0]) for row in rows]
    ids = Counter(row.get("query") for row in rows)
    hashes = Counter(row["pair_sha256"] for row in results)
    for result in results:
        if ids[result["query"]] > 1:
            result["errors"].append("duplicate_query")
        if hashes[result["pair_sha256"]] > 1:
            result["errors"].append("duplicate_sequence_pair")
        if result["errors"]:
            result["local_status"] = "FAIL_LOCAL"
    print(json.dumps({"created_utc": datetime.now(timezone.utc).isoformat(),
                      "immunum_version": importlib.metadata.version("immunum"),
                      "input_sha256": hashlib.sha256(args.csv.read_bytes()).hexdigest(),
                      "parent_spr_sha256": hashlib.sha256(args.parent_spr.read_bytes()).hexdigest(),
                      "scope": "local sequence diagnostics only; no track assignment or efficacy claim",
                      "counts": dict(Counter(r["local_status"] for r in results)),
                      "rows": results}, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
