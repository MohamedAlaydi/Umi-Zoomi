#!/usr/bin/env python3
"""Regenerate notes/SCORES.md from numbers that are already on disk.

Every cell in the generated table is read out of a file under runs/<run>/, and
the last column of every row is the repo-relative path of that file, so a judge
can open it and see the same number.  Nothing is typed by hand here.

    py scripts/scores.py            # regenerate notes/SCORES.md
    py scripts/scores.py --check    # re-read every path the table cites

Isolation: while rows for run X are being built, only files that resolve inside
runs/X/ (or inside the directory runs/X/out points at) are ever opened.  That is
enforced by assertion, not by convention, because this repo has already had one
report read a different run's metrics.

This script reads JSON, CSV and .log files only.  It never opens a structure
file (.cif/.pdb) and never runs a model, a container or a GPU job.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUNS_DIR = REPO / "runs"
DEFAULT_TABLE = REPO / "notes" / "SCORES.md"

# Keys lifted out of each <query>_seed_<N>_sample_<M>_scores.json.  The score
# name in the table is the JSON key verbatim, so it is unambiguous.
STRUCTURE_KEYS = (
    "interface_predicted_tm_score",
    "global_predicted_distance_error",
    "average_predicted_local_distance_difference_test",
    "model_ranking_score",
)

# Per-design candidate metadata.  <csv column> -> <score name in the table>.
MANIFEST_COLUMNS = {"p_high": "p_high"}
CANDIDATE_COLUMNS = {
    "min_dist": "novelty_min_distance",
    "identity": "identity_percent_to_wild_type",
}
# Columns of the rendered novelty table inside some runs' run.log.
RUN_LOG_COLUMNS = {
    "min_dist": "novelty_min_distance",
    "identity": "identity_percent_to_wild_type",
}

HEADER = (
    "| design id | run | model + checkpoint | seed | score name | value "
    "| where it came from |"
)
SEPARATOR = "| --- | --- | --- | --- | --- | --- | --- |"

PREAMBLE = """# Score table

This is the computational score ledger for the hackathon submission.

Start with the [proposed ranked 20](RANKED_CANDIDATES.csv)
and [selection rationale](../review/pitch_her2/Rangering_begrunnet.md).
The [earlier review order](../review/evidence/panel.csv) and
[earlier ensemble order](../people/anas/final-20.csv) are dated analyses,
not additional submissions.
Public candidate IDs describe the method: `HER2-OPT` for enumerated
optimisation designs and `HER2-GEN` for a generator comparator. Their numeric
suffix is stable across ranking changes. [ID mapping](CANDIDATE_IDS.csv)
connects them to the original model queries; original evidence stays intact.
Read [how scores and judging criteria differ](SCORING.md).
The [de novo campaign report](../review/denovo/CAMPAIGN_RESULTS.md) and
[campaign evidence](../runs/011-codex-denovo-vhh/local-refold-evidence.json)
record the separate hosted-model checks. The
[binding-ddG table](../people/anas/stabddg-joined.csv) is a binding prediction,
not a thermal-stability measurement.

**This file is generated.** Do not hand-edit it: run

    py scripts/scores.py

and it is rebuilt from the files the models actually wrote. Small score and
provenance files are copied byte for byte into each run's `score-evidence/`
directory, so the cited files also exist in a fresh GitHub checkout without
the VM's data directory or output symlinks. `score-evidence/SHA256SUMS` in each
run records the snapshot hashes. Heavy structures and model weights are
outside this score ledger; see the reproducibility notes for those artifacts.
`py scripts/scores.py --check` re-reads every one of those paths and fails if
the table and the files have drifted apart. Reasoning about these numbers
belongs in `notes/DECISIONS.md`, not here.

Scores taken from each query's `*_scores.json` keep the name that file uses.
`p_high` is a classifier prediction trained on measured FACS classes. It is
not measured binding, an SPR KD or a calibrated probability of improvement.
Structural confidence, predicted binding-ddG and chemical-liability flags do
not establish higher affinity, competition with trastuzumab or higher Tm.
No new experimental values for those three endpoints are reported here.
Local novelty screens are not final organiser acceptance.
`novelty_min_distance` and
`identity_percent_to_wild_type` are not recomputed here: they are read back
verbatim from the novelty table the run itself wrote into its own `run.log` or
`candidates.csv`. The `model + checkpoint` column names the file that attests
the module, the checkpoint and the seed, in brackets.
"""

SCORES_JSON_RE = re.compile(
    r"^(?P<design>.+)_seed_(?P<seed>\d+)_sample_(?P<sample>\d+)_scores\.json$"
)
SEED_DIR_RE = re.compile(r"^seed_(?P<seed>\d+)$")
# her2_anchored_13 WGPSGFYAMD     1    80%  REJECTED   grip kept
RUN_LOG_ROW_RE = re.compile(
    r"^(?P<design>[A-Za-z0-9_.-]+)\s+(?P<cdrh3>[A-Z]{3,})\s+"
    r"(?P<min_dist>\d+)\s+(?P<identity>\d+)%\s+\S+"
)
MODEL_PROV_RE = re.compile(r"\[(?P<path>[^\]]+)\]\s*$")


# --------------------------------------------------------------------------
# isolation
# --------------------------------------------------------------------------
class Isolation:
    """The set of real directories a single run is allowed to read from."""

    def __init__(self, run_dir: Path) -> None:
        self.run_name = run_dir.name
        self.run_dir = run_dir
        roots = [Path(os.path.realpath(run_dir))]
        out = run_dir / "out"
        if out.exists():
            real_out = Path(os.path.realpath(out))
            if real_out not in roots:
                roots.append(real_out)
        self.roots = roots

    def contains(self, path: Path) -> bool:
        real = Path(os.path.realpath(path))
        for root in self.roots:
            if real == root or root in real.parents:
                return True
        return False

    def check(self, path: Path) -> Path:
        if not self.contains(path):
            raise AssertionError(
                f"isolation violation: {path} resolves outside "
                f"runs/{self.run_name}/ (allowed: {[str(r) for r in self.roots]})"
            )
        return path

    def read_text(self, path: Path) -> str:
        return self.check(path).read_text(encoding="utf-8", errors="replace")

    def read_json(self, path: Path):
        return json.loads(self.read_text(path))


def repo_rel(path: Path) -> str:
    """Repo-relative, lexical (so it keeps going through runs/X/out)."""
    return os.path.relpath(os.path.normpath(str(path)), str(REPO)).replace(os.sep, "/")


# --------------------------------------------------------------------------
# value normalisation -- one function, used by both generate and --check
# --------------------------------------------------------------------------
def norm_number(raw) -> str | None:
    """Canonical string for a number, or None if `raw` is not a finite number."""
    if isinstance(raw, bool) or raw is None:
        return None
    if isinstance(raw, int):
        return str(raw)
    if isinstance(raw, float):
        return repr(raw) if math.isfinite(raw) else None
    text = str(raw).strip()
    if not text:
        return None
    try:
        return str(int(text))
    except ValueError:
        pass
    try:
        value = float(text)
    except ValueError:
        return None
    return repr(value) if math.isfinite(value) else None


def esc(cell: str) -> str:
    return str(cell).replace("|", r"\|").strip()


# --------------------------------------------------------------------------
# provenance: model + checkpoint, and the seed, per output module directory
# --------------------------------------------------------------------------
class Provenance:
    """What runs/X/out/<module>/{result,config}.json says about the model."""

    def __init__(self, model_cell: str, prov_path: Path, seeds: set[int],
                 seed_by_scores_path: dict[str, int]) -> None:
        self.model_cell = model_cell
        self.prov_path = prov_path
        self.seeds = seeds
        self.seed_by_scores_path = seed_by_scores_path

    def seed_for(self, rel_scores_path: str, seed_from_path: int):
        """Seed attested by the provenance file, or (None, reason)."""
        attested = self.seed_by_scores_path.get(rel_scores_path)
        if attested is not None:
            return attested, None
        if seed_from_path in self.seeds:
            return seed_from_path, None
        return None, "seed not attested by result.json/config.json"


def _model_cell(module, weights, prov_path: Path) -> str:
    bits = []
    if module:
        name = str(module.get("name", "")).strip()
        version = str(module.get("version", "")).strip()
        if name:
            bits.append(f"{name} {version}".strip())
    if weights:
        bits.append(f"weights={weights}")
    if not bits:
        return ""
    return f"{', '.join(bits)} [{repo_rel(prov_path)}]"


def load_provenance(iso: Isolation, module_dir: Path, cited_file: Path | None = None):
    """-> (Provenance, None) or (None, reason)."""
    result_path = module_dir / "result.json"
    if result_path.is_file() and (cited_file is None or cited_file.name == "result.json"):
        try:
            doc = iso.read_json(result_path)
        except (OSError, ValueError) as exc:
            return None, f"unreadable result.json ({type(exc).__name__})"
        prov = doc.get("provenance") or {}
        resolved = prov.get("resolved_config") or {}
        weights = resolved.get("weights")
        module = prov.get("module") or {}
        cell = _model_cell(module, weights, result_path)
        if not cell:
            return None, "result.json records neither module nor weights"
        seeds = {int(s) for s in (resolved.get("seeds") or []) if _is_int(s)}
        by_path = {}
        for pred in (doc.get("result") or {}).get("predictions") or []:
            sp, sd = pred.get("scores_path"), pred.get("seed")
            if isinstance(sp, str) and _is_int(sd):
                by_path[sp] = int(sd)
                seeds.add(int(sd))
        return Provenance(cell, result_path, seeds, by_path), None

    config_path = module_dir / "config.json"
    if config_path.is_file():
        try:
            cfg = iso.read_json(config_path)
        except (OSError, ValueError) as exc:
            return None, f"unreadable config.json ({type(exc).__name__})"
        # config.json records the checkpoint and the seed list but not the
        # module name/version; we do not borrow those from another file.
        cell = _model_cell(None, cfg.get("weights"), config_path)
        if not cell:
            return None, "config.json records no weights"
        seeds = {int(s) for s in (cfg.get("seeds") or []) if _is_int(s)}
        return Provenance(cell, config_path, seeds, {}), None

    return None, "no result.json or config.json for this output module"


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


# --------------------------------------------------------------------------
# value extractors -- shared by generate and --check
# --------------------------------------------------------------------------
def value_from_scores_json(iso: Isolation, path: Path, design: str, score: str):
    try:
        doc = iso.read_json(path)
    except (OSError, ValueError) as exc:
        return None, f"unreadable scores json ({type(exc).__name__})"
    if not isinstance(doc, dict):
        return None, "scores json is not an object"
    if score not in doc:
        return None, f"key {score} absent from scores json"
    value = norm_number(doc[score])
    if value is None:
        return None, f"key {score} is not a finite number"
    return value, None


def _csv_rows(iso: Isolation, path: Path):
    text = iso.read_text(path)
    return list(csv.DictReader(text.splitlines()))


def _value_from_keyed_csv(iso: Isolation, path: Path, design: str, score: str,
                          columns: dict[str, str], key_column: str = "query_id"):
    try:
        rows = _csv_rows(iso, path)
    except (OSError, ValueError) as exc:
        return None, f"unreadable csv ({type(exc).__name__})"
    column = next((c for c, name in columns.items() if name == score), None)
    if column is None:
        return None, f"score {score} is not sourced from {path.name}"
    hits = [r for r in rows if (r.get(key_column) or "").strip() == design]
    if not hits:
        return None, f"no {key_column}={design} row in {path.name}"
    if len(hits) > 1:
        distinct = {(r.get(column) or "").strip() for r in hits}
        if len(distinct) > 1:
            return None, f"{design} appears {len(hits)}x in {path.name} with different {column}"
    raw = (hits[0].get(column) or "").strip()
    value = norm_number(raw)
    if value is None:
        return None, f"{column} empty or non-numeric for {design}"
    return value, None


def value_from_manifest_csv(iso, path, design, score):
    return _value_from_keyed_csv(iso, path, design, score, MANIFEST_COLUMNS)


def value_from_candidates_csv(iso, path, design, score):
    return _value_from_keyed_csv(iso, path, design, score, CANDIDATE_COLUMNS)


def parse_run_log_novelty(iso: Isolation, path: Path):
    """design -> {'min_dist': str, 'identity': str}, read verbatim from the log."""
    try:
        text = iso.read_text(path)
    except OSError as exc:
        return {}, f"unreadable run.log ({type(exc).__name__})"
    table: dict[str, dict[str, str]] = {}
    conflicted: set[str] = set()
    for line in text.splitlines():
        match = RUN_LOG_ROW_RE.match(line)
        if not match:
            continue
        design = match.group("design")
        entry = {"min_dist": match.group("min_dist"),
                 "identity": match.group("identity")}
        if design in table and table[design] != entry:
            conflicted.add(design)
        table[design] = entry
    for design in conflicted:
        table.pop(design, None)
    return table, None


def value_from_run_log(iso: Isolation, path: Path, design: str, score: str):
    table, err = parse_run_log_novelty(iso, path)
    if err:
        return None, err
    column = next((c for c, name in RUN_LOG_COLUMNS.items() if name == score), None)
    if column is None:
        return None, f"score {score} is not sourced from run.log"
    entry = table.get(design)
    if entry is None:
        return None, f"no novelty row for {design} in run.log"
    value = norm_number(entry[column])
    if value is None:
        return None, f"{column} non-numeric for {design} in run.log"
    return value, None


def extractor_for(path: Path):
    """Pick the extractor from the cited file's name, for --check."""
    name = path.name
    if name.endswith("_scores.json"):
        return value_from_scores_json
    if name == "manifest.csv":
        return value_from_manifest_csv
    if name == "candidates.csv":
        return value_from_candidates_csv
    if name == "run.log":
        return value_from_run_log
    return None


# --------------------------------------------------------------------------
# generate
# --------------------------------------------------------------------------
class Row:
    __slots__ = ("run", "design", "model", "seed", "score", "value", "source",
                 "sample")

    def __init__(self, run, design, model, seed, score, value, source, sample=1):
        self.run, self.design, self.model = run, design, model
        self.seed, self.score, self.value = seed, score, value
        self.source, self.sample = source, sample

    def sort_key(self):
        try:
            seed_key = (0, int(self.seed), "")
        except (TypeError, ValueError):
            seed_key = (1, 0, str(self.seed))
        return (self.run, self.design, self.score, seed_key, self.sample,
                self.source)

    def render(self) -> str:
        source = f"[{self.source}](../{self.source})"
        cells = [self.design, self.run, self.model, self.seed, self.score,
                 self.value, source]
        return "| " + " | ".join(esc(c) for c in cells) + " |"


class Skips:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    def add(self, reason: str, n: int = 1) -> None:
        self.counts[reason] = self.counts.get(reason, 0) + n

    def total(self) -> int:
        return sum(self.counts.values())


def iter_scores_json(iso: Isolation, module_dir: Path):
    """Yield (design, seed_from_path, sample, path) under one output module."""
    for design_dir in sorted(module_dir.iterdir()):
        if not design_dir.is_dir():
            continue
        for seed_dir in sorted(design_dir.iterdir()):
            if not seed_dir.is_dir():
                continue
            seed_match = SEED_DIR_RE.match(seed_dir.name)
            if not seed_match:
                continue
            for path in sorted(seed_dir.iterdir()):
                file_match = SCORES_JSON_RE.match(path.name)
                if not file_match or not path.is_file():
                    continue
                if file_match.group("design") != design_dir.name:
                    continue
                if file_match.group("seed") != seed_match.group("seed"):
                    continue
                iso.check(path)
                yield (design_dir.name, int(seed_match.group("seed")),
                       int(file_match.group("sample")), path)


def output_module_dirs(iso: Isolation) -> list[Path]:
    out = iso.run_dir / "out"
    if not out.is_dir():
        out = iso.run_dir / "score-evidence" / "modules"
    if not out.is_dir():
        return []
    iso.check(out)
    modules = []
    for module_dir in sorted(out.iterdir()):
        if not module_dir.is_dir():
            continue
        if any(True for _ in iter_scores_json(iso, module_dir)):
            modules.append(module_dir)
    return modules


def rows_for_run(run_dir: Path, skips: Skips) -> list[Row]:
    iso = Isolation(run_dir)
    run = run_dir.name
    rows: list[Row] = []

    # --- structure scores, plus model+checkpoint and seed provenance --------
    for module_dir in output_module_dirs(iso):
        prov, reason = load_provenance(iso, module_dir)
        if prov is None:
            n = sum(1 for _ in iter_scores_json(iso, module_dir))
            skips.add(f"{reason}", n * len(STRUCTURE_KEYS))
            continue
        for design, seed_from_path, sample, path in iter_scores_json(iso, module_dir):
            rel_in_module = os.path.relpath(str(path), str(module_dir)).replace(os.sep, "/")
            seed, seed_reason = prov.seed_for(rel_in_module, seed_from_path)
            if seed is None:
                skips.add(seed_reason, len(STRUCTURE_KEYS))
                continue
            source = repo_rel(path)
            for score in STRUCTURE_KEYS:
                value, reason = value_from_scores_json(iso, path, design, score)
                if value is None:
                    skips.add(reason, 1)
                    continue
                rows.append(Row(run, design, prov.model_cell, str(seed), score,
                                value, source, sample))

    # --- per-design candidate metadata (p_high) -----------------------------
    manifest = run_dir / "manifest.csv"
    if manifest.is_file():
        designs = _csv_designs(iso, manifest, skips)
        for design in designs:
            for score in MANIFEST_COLUMNS.values():
                value, reason = value_from_manifest_csv(iso, manifest, design, score)
                if value is None:
                    skips.add(reason.replace(design, "<design>"), 1)
                    continue
                rows.append(Row(run, design, f"[{repo_rel(manifest)}]", "n/a",
                                score, value, repo_rel(manifest)))

    # --- novelty verdicts the run itself wrote down -------------------------
    candidates = run_dir / "candidates.csv"
    if candidates.is_file():
        for design in _csv_designs(iso, candidates, skips):
            for score in CANDIDATE_COLUMNS.values():
                value, reason = value_from_candidates_csv(iso, candidates, design, score)
                if value is None:
                    skips.add(reason.replace(design, "<design>"), 1)
                    continue
                rows.append(Row(run, design, f"[{repo_rel(candidates)}]", "n/a",
                                score, value, repo_rel(candidates)))

    run_log = run_dir / "run.log"
    if run_log.is_file():
        table, err = parse_run_log_novelty(iso, run_log)
        if err:
            skips.add(err, 1)
            table = {}
        for design in sorted(table):
            for score in RUN_LOG_COLUMNS.values():
                value, reason = value_from_run_log(iso, run_log, design, score)
                if value is None:
                    skips.add(reason.replace(design, "<design>"), 1)
                    continue
                rows.append(Row(run, design, f"[{repo_rel(run_log)}]", "n/a",
                                score, value, repo_rel(run_log)))

    return rows


def _csv_designs(iso: Isolation, path: Path, skips: Skips) -> list[str]:
    try:
        rows = _csv_rows(iso, path)
    except (OSError, ValueError) as exc:
        skips.add(f"unreadable {path.name} ({type(exc).__name__})", 1)
        return []
    seen, order = set(), []
    for row in rows:
        design = (row.get("query_id") or "").strip()
        if design and design not in seen:
            seen.add(design)
            order.append(design)
    return sorted(order)


def assert_runs_do_not_share_output(run_dirs: list[Path]) -> None:
    """Two runs pointing out/ at the same tree is the cross-contamination bug."""
    seen: dict[str, str] = {}
    for run_dir in run_dirs:
        out = run_dir / "out"
        if not out.exists():
            continue
        real = os.path.realpath(out)
        if real in seen:
            raise AssertionError(
                f"runs/{seen[real]}/out and runs/{run_dir.name}/out both resolve "
                f"to {real}; refusing to generate a table that would mix them"
            )
        seen[real] = run_dir.name


def freeze_rows(rows: list[Row]) -> None:
    """Keep cited evidence in Git without tracking absolute output symlinks."""
    mapping: dict[str, str] = {}
    by_run: dict[str, set[str]] = {}
    for row in rows:
        match = MODEL_PROV_RE.search(row.model)
        if match is None:
            raise ValueError(f"Missing provenance for {row.run}/{row.design}")
        for source in (row.source, match.group("path")):
            if source in mapping:
                continue
            run_dir = RUNS_DIR / row.run
            path = Isolation(run_dir).check(REPO / source)
            rel = path.relative_to(run_dir)
            if rel.parts[0] == "score-evidence":
                destination = path
            else:
                folder = "modules" if rel.parts[0] == "out" else "inputs"
                tail = Path(*rel.parts[1:]) if folder == "modules" else rel
                destination = run_dir / "score-evidence" / folder / tail
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)
            mapping[source] = repo_rel(destination)
            by_run.setdefault(row.run, set()).add(repo_rel(destination))
    for row in rows:
        match = MODEL_PROV_RE.search(row.model)
        source = match.group("path")
        row.model = row.model[:match.start()] + f"[{mapping[source]}]"
        row.source = mapping[row.source]
    for run, sources in by_run.items():
        root = RUNS_DIR / run / "score-evidence"
        lines = []
        for rel in sorted(sources):
            path = REPO / rel
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            lines.append(f"{digest}  {path.relative_to(root).as_posix()}")
        (root / "SHA256SUMS").write_text("\n".join(lines) + "\n")


def generate(out_path: Path) -> int:
    run_dirs = sorted(d for d in RUNS_DIR.iterdir() if d.is_dir())
    assert_runs_do_not_share_output(run_dirs)

    skips = Skips()
    rows: list[Row] = []
    per_run: list[tuple[str, int, int]] = []
    for run_dir in run_dirs:
        run_rows = rows_for_run(run_dir, skips)
        designs = {r.design for r in run_rows}
        per_run.append((run_dir.name, len(run_rows), len(designs)))
        rows.extend(run_rows)

    freeze_rows(rows)
    rows.sort(key=Row.sort_key)

    body = [PREAMBLE.rstrip("\n"), "", "", HEADER, SEPARATOR]
    body.extend(row.render() for row in rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ledger = out_path.with_name(out_path.stem + "_FULL.md")
    ledger.write_text("\n".join(body) + "\n", encoding="utf-8")
    with out_path.with_suffix(".csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["design", "run", "model", "seed", "score", "value", "source", "sample"])
        writer.writerows([r.design, r.run, r.model, r.seed, r.score, r.value, r.source, r.sample] for r in rows)
    out_path.write_text(overview(rows, ledger.name, out_path.with_suffix(".csv").name), encoding="utf-8")
    for name, (fields, data) in public_panel_exports().items():
        with (out_path.parent / name).open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)

    designs = {(r.run, r.design) for r in rows}
    print(f"wrote {repo_rel(out_path)}")
    print(f"runs covered   : {sum(1 for _, n, _ in per_run if n)} of {len(per_run)}")
    print(f"designs covered: {len(designs)} (run, design) pairs")
    print(f"rows written   : {len(rows)}")
    print(f"rows skipped   : {skips.total()}")
    for reason, count in sorted(skips.counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"    {count:5d}  {reason}")
    print("per-run rows:")
    for name, nrows, ndesigns in per_run:
        print(f"    {nrows:5d} rows  {ndesigns:3d} designs  {name}")
    return 0


def candidate_label(query: str) -> str:
    match = re.fullmatch(r"anas_(\d+)", query)
    if match:
        return f"HER2-OPT-{int(match.group(1)):03d}"
    match = re.fullmatch(r"r004_cdrh3_(\d+)", query)
    if match:
        return f"HER2-GEN-{int(match.group(1)):03d}"
    return query


def run_label(run: str) -> str:
    match = re.fullmatch(r"(\d+)-(?:anas|mohamed|claude|codex)-(.+)", run)
    return f"Run {match.group(1)}: {match.group(2)}" if match else run


def public_panel_exports():
    source = "review/pitch_her2/Proposed_ranked_20.csv"
    ranking = REPO / source
    if not ranking.is_file():
        return {}
    with ranking.open() as handle:
        reader = csv.DictReader(handle)
        fields = ["candidate_id" if f == "query" else f for f in reader.fieldnames]
        original = list(reader)
    public, mapping, seen = [], [], set()
    for row in original:
        label = candidate_label(row["query"])
        if label in seen:
            raise ValueError(f"Duplicate public candidate ID: {label}")
        seen.add(label)
        public.append({"candidate_id" if k == "query" else k: label if k == "query" else v for k, v in row.items()})
        mapping.append(dict(candidate_id=label, source_query=row["query"],
                            source_file=source, pair_sha256=row["pair_sha256"]))
    return {"RANKED_CANDIDATES.csv": (fields, public),
            "CANDIDATE_IDS.csv": (list(mapping[0]) if mapping else
                                  ["candidate_id", "source_query", "source_file", "pair_sha256"], mapping)}


def overview(rows: list[Row], ledger_name: str, csv_name: str) -> str:
    """Keep the GitHub entry point readable; retain every score in the ledger."""
    lines = [PREAMBLE.rstrip(), "", f"<!-- score-ledger: {ledger_name} -->",
             f"All **{len(rows):,}** score rows: [CSV]({csv_name}) · "
             f"[full ledger with source links]({ledger_name}).", "", "## Coverage", "",
             "| Run | Designs | Score rows | Numeric seeds |", "| --- | ---: | ---: | --- |"]
    for run in sorted({r.run for r in rows}):
        subset = [r for r in rows if r.run == run]
        seeds = sorted({int(r.seed) for r in subset if str(r.seed).isdigit()})
        lines.append(f"| {run_label(run)} | {len({r.design for r in subset})} | {len(subset)} | {', '.join(map(str,seeds))} |")
    ranking = REPO / "review/pitch_her2/Proposed_ranked_20.csv"
    if ranking.is_file():
        lines += ["", "## Proposed panel: original matched seed-42 scores", "",
                  "This preserves the proposed experimental order. These are the original run-006",
                  "complex scores, not a claim of seed robustness or measured affinity. Global ipTM",
                  "also includes the VH–VL interface. See the linked rationale for the six-seed",
                  "HER2-contact evidence used for selection. A local validator pass is not final acceptance.", "",
                  "BLOSUM62 and repeated-contact counts come from the supplied ranked panel,",
                  "not from these single-seed JSON files. There is no official weighted total score.", "",
                  "| Rank | Candidate | BLOSUM62 | Four contacts / 6 | Global ipTM | Complex pLDDT | Raw score |",
                  "| ---: | --- | ---: | ---: | ---: | ---: | --- |"]
        baseline = {r.design: {} for r in rows if r.run.startswith("006-")}
        for r in rows:
            if r.run.startswith("006-") and str(r.seed) == "42" and r.sample == 1:
                baseline[r.design][r.score] = r
        panel = list(csv.DictReader(ranking.open()))
        for item in panel:
            data = baseline.get(item["query"], {})
            iptm = data.get("interface_predicted_tm_score")
            plddt = data.get("average_predicted_local_distance_difference_test")
            link = f"[JSON](../{iptm.source})" if iptm else "NA"
            lines.append(f"| {item['rank']} | {candidate_label(item['query'])} | {item['blosum62']} | {item['all_four_contacts_of_six']}/6 | {iptm.value if iptm else 'NA'} | {plddt.value if plddt else 'NA'} | {link} |")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# --check
# --------------------------------------------------------------------------
def split_row(line: str) -> list[str]:
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    cells, current, i = [], [], 0
    while i < len(inner):
        char = inner[i]
        if char == "\\" and i + 1 < len(inner) and inner[i + 1] == "|":
            current.append("|")
            i += 2
            continue
        if char == "|":
            cells.append("".join(current).strip())
            current = []
            i += 1
            continue
        current.append(char)
        i += 1
    cells.append("".join(current).strip())
    return cells


def _cited_path(iso: Isolation, run: str, cited: str):
    """-> (Path, None) or (None, problem). Rejects anything outside runs/<run>/."""
    if cited.startswith("/") or ".." in cited.split("/"):
        return None, f"cited path is not a plain repo-relative path: {cited}"
    prefix = f"runs/{run}/"
    if not cited.startswith(prefix):
        return None, f"cited path {cited} is not under {prefix}"
    path = REPO / cited
    if not iso.contains(path):
        return None, f"cited path {cited} resolves outside runs/{run}/"
    if not path.is_file():
        return None, f"cited file is missing: {cited}"
    return path, None


def check(table_path: Path) -> int:
    if not table_path.is_file():
        print(f"check: {repo_rel(table_path)} does not exist", file=sys.stderr)
        return 2
    lines = table_path.read_text(encoding="utf-8").splitlines()

    marker = re.search(r"^<!-- score-ledger: ([A-Za-z0-9_.-]+) -->$", "\n".join(lines), re.M)
    if marker:
        ledger = table_path.with_name(marker.group(1))
        result = check(ledger)
        if result:
            return result
        records = []
        for line in ledger.read_text().splitlines():
            if not line.startswith("| ") or line in (HEADER, SEPARATOR):
                continue
            design, run, model, seed, score, value, cited = split_row(line)
            match = re.fullmatch(r"\[([^\]]+)\]\(\.\./([^)]*)\)", cited)
            source = match.group(1) if match else cited
            records.append(Row(run, design, model, seed, score, value, source,
                               int(SCORES_JSON_RE.match(Path(source).name).group("sample"))
                               if SCORES_JSON_RE.match(Path(source).name) else 1))
        expected = overview(records, ledger.name, table_path.with_suffix(".csv").name)
        if table_path.read_text() != expected:
            print("check FAILED: score overview differs from source ledger or proposed ranking", file=sys.stderr)
            return 1
        csv_path = table_path.with_suffix(".csv")
        expected_csv = [["design", "run", "model", "seed", "score", "value", "source", "sample"]]
        expected_csv += [[r.design, r.run, r.model, str(r.seed), r.score, r.value, r.source, str(r.sample)] for r in records]
        if not csv_path.is_file() or list(csv.reader(csv_path.open(newline=""))) != expected_csv:
            print("check FAILED: score CSV differs from the source ledger", file=sys.stderr)
            return 1
        for name, (fields, data) in public_panel_exports().items():
            path = table_path.parent / name
            if not path.is_file():
                print(f"check FAILED: missing public panel export {name}", file=sys.stderr)
                return 1
            with path.open(newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames != fields or list(reader) != data:
                    print(f"check FAILED: changed public panel export {name}", file=sys.stderr)
                    return 1
        print(f"check OK: {repo_rel(table_path)} overview matches the ledger and proposed panel")
        return 0

    try:
        header_index = next(i for i, line in enumerate(lines)
                            if line.strip().startswith("| design id "))
    except StopIteration:
        print("check: no score table header found", file=sys.stderr)
        return 2
    if lines[header_index].strip() != HEADER:
        print("check: table header differs from the expected 7-column header",
              file=sys.stderr)
        print(f"    found   : {lines[header_index].strip()}", file=sys.stderr)
        print(f"    expected: {HEADER}", file=sys.stderr)
        return 2

    problems: list[str] = []
    checked = 0
    iso_cache: dict[str, Isolation] = {}
    prov_cache: dict[str, tuple] = {}
    verified_hashes: set[str] = set()

    for offset, line in enumerate(lines[header_index + 2:], start=header_index + 3):
        if not line.strip().startswith("|"):
            continue
        cells = split_row(line)
        if len(cells) != 7:
            problems.append(f"line {offset}: expected 7 columns, found {len(cells)}")
            continue
        design, run, model, seed, score, value, cited = cells
        linked = re.fullmatch(r"\[([^\]]+)\]\(\.\./([^)]*)\)", cited)
        if linked:
            if linked.group(1) != linked.group(2):
                problems.append(f"line {offset}: source link label and target differ")
                continue
            cited = linked.group(1)
        where = f"line {offset} [{run} / {design} / {score}]"

        run_dir = RUNS_DIR / run
        if "/" in run or not run_dir.is_dir():
            problems.append(f"{where}: no such run directory runs/{run}/")
            continue
        iso = iso_cache.setdefault(run, Isolation(run_dir))

        if run not in verified_hashes:
            verified_hashes.add(run)
            snapshot = run_dir / "score-evidence"
            hashes = snapshot / "SHA256SUMS"
            if hashes.is_file():
                for entry in hashes.read_text().splitlines():
                    digest, relative = entry.split("  ", 1)
                    candidate = snapshot / relative
                    if (Path(relative).is_absolute() or ".." in Path(relative).parts
                            or not candidate.resolve().is_relative_to(snapshot.resolve())
                            or not candidate.is_file()
                            or hashlib.sha256(candidate.read_bytes()).hexdigest() != digest):
                        problems.append(f"snapshot hash mismatch: runs/{run}/score-evidence/{relative}")

        path, problem = _cited_path(iso, run, cited)
        if problem:
            problems.append(f"{where}: {problem}")
            continue

        extractor = extractor_for(path)
        if extractor is None:
            problems.append(f"{where}: no known way to re-read a value from {cited}")
            continue
        found, reason = extractor(iso, path, design, score)
        if found is None:
            problems.append(f"{where}: {reason} ({cited})")
            continue
        if found != value:
            problems.append(
                f"{where}: table says {value!r}, {cited} says {found!r}")
            continue
        checked += 1

        # The model + checkpoint cell cites the file that attests the module,
        # the checkpoint and the seed.  Re-derive it and re-check the seed.
        prov_match = MODEL_PROV_RE.search(model)
        if not prov_match:
            problems.append(f"{where}: model cell cites no provenance file: {model!r}")
            continue
        prov_cited = prov_match.group("path").strip()
        prov_path, problem = _cited_path(iso, run, prov_cited)
        if problem:
            problems.append(f"{where}: model cell {problem}")
            continue
        if prov_path.name in ("result.json", "config.json"):
            key = prov_cited
            if key not in prov_cache:
                prov_cache[key] = load_provenance(iso, prov_path.parent, prov_path)
            prov, reason = prov_cache[key]
            if prov is None:
                problems.append(f"{where}: model cell cites {prov_cited}: {reason}")
                continue
            if prov.model_cell != model:
                problems.append(
                    f"{where}: model cell says {model!r}, {prov_cited} says "
                    f"{prov.model_cell!r}")
                continue
            rel_in_module = os.path.relpath(str(path), str(prov_path.parent))
            rel_in_module = rel_in_module.replace(os.sep, "/")
            try:
                seed_int = int(seed)
            except ValueError:
                problems.append(f"{where}: seed {seed!r} is not an integer")
                continue
            attested, reason = prov.seed_for(rel_in_module, seed_int)
            if attested is None:
                problems.append(f"{where}: seed {seed}: {reason} ({prov_cited})")
                continue
            if attested != seed_int:
                problems.append(
                    f"{where}: table says seed {seed}, {prov_cited} says {attested}")
                continue
        elif prov_cited != cited:
            problems.append(
                f"{where}: model cell cites {prov_cited} but the value came "
                f"from {cited}")
            continue

    if problems:
        print(f"check FAILED: {len(problems)} problem(s) in "
              f"{repo_rel(table_path)}", file=sys.stderr)
        for problem in problems[:20]:
            print(f"    {problem}", file=sys.stderr)
        if len(problems) > 20:
            print(f"    ... {len(problems) - 20} further problem(s)", file=sys.stderr)
        return 1
    print(f"check OK: {checked} rows in {repo_rel(table_path)} re-read from "
          f"the files they cite")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="re-read every path the table cites; exit non-zero "
                             "on a missing file or a changed value")
    parser.add_argument("--out", type=Path, default=DEFAULT_TABLE,
                        help="table to write, or to check (default notes/SCORES.md)")
    args = parser.parse_args(argv)
    if args.check:
        return check(args.out)
    return generate(args.out)


if __name__ == "__main__":
    sys.exit(main())
