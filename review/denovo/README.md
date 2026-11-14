# De novo readiness and local sequence preflight

This tool accepts Fab or VHH variable sequences, checks numbering, lengths,
hashes and duplicates, and leaves official eligibility unverified. It does not
generate candidates, assign a competition track, validate disulfides, predict
affinity or predict melting temperature. A VHH declaration does not establish
that a heavy chain is a functional single-domain antibody.

Install separately from the shared GPU environment:

```bash
uv venv review/denovo/.venv
uv pip install --python review/denovo/.venv/bin/python -r review/denovo/requirements.txt
review/denovo/.venv/bin/python review/denovo/preflight.py review/evidence/panel.csv \
  --parent-spr data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv
```

Input columns: `query`, `format` (`Fab` or `VHH`), `heavy_variable`,
`light_variable` (empty for VHH), optional `pair_sha256`. Sequences must be
uppercase, untagged, canonical amino acids. The diagnostic parent identity is
computed only for a matching pair of lengths; it is not a nearest-database
alignment. scFv extraction and type-aware official checks require the actual
organiser tool. The IMGT CDRH3 differs from the organiser's 10-residue mutated
window; do not substitute one for the other in the novelty cache.

The current `review/structure_checks.py` assumes A=VL, B=VH, C/D=HER2
fragments and the original framework. It must not be applied unchanged to VHH.
Future geometry checks need explicit chain-role and antigen-residue maps.

Read `READINESS.md` for the dated environment audit, model choices, remaining
gates, proposed experiment and pitch evidence.

The downloadable bundle is a copy of this project subdirectory, without the
virtual environment or the original datasets. Restore it under `review/denovo/`
in the Team 14 checkout to use the target-preparation script and regression
tests. `preflight.py` itself can run elsewhere with an explicit `--parent-spr`.

## Completed campaign

The earlier READINESS.md is a preparation-time snapshot. Current results are in CAMPAIGN_RESULTS.md and team14/runs/011-codex-denovo-vhh/. The campaign completed 96 design sequences and the independent computational checks; binding and thermal experiments remain pending. Use refresh.sh <output-directory> to audit/rebuild without submitting new jobs.

The optional browser/PDF export uses export_report.py --output <directory>, with the separate report-requirements.txt and Chromium installed. The core audit and report builder require no browser or new model jobs.
