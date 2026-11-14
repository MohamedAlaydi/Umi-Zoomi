# Published evidence and original model outputs

The repository includes the completed campaign report, all analysis code,
small request/configuration and job-receipt JSON files, result tables,
validator receipts, target sequence/numbering maps, and the compact offline
report in `report/`. Its SHA256SUMS covers the report’s portable evidence
and selected coordinate structures.

The original full run also contains large provider ZIP archives, PAE tensors,
full per-token data and duplicate structures. These remain in the Team 14 VM
run directory and are deliberately excluded from Git. `original-artifact-index.json`
lists their paths and byte sizes. The provider download receipts record
SHA-256 values for downloaded archives and individual artifacts.

`verify_campaign.py` audits the ORIGINAL run tree and needs those original
outputs plus the organiser data. It is not a fresh-checkout test. A fresh
checkout can inspect and verify the report SHA256SUMS, check the score
ledger with `python3 scripts/scores.py --check`, and run the separate frozen
optimisation replay with `review/replay.py`. None submits jobs.
