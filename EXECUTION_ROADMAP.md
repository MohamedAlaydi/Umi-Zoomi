# From the current evidence to a ranked, testable submission

**Timebox.** The published schedule starts pitch preparation at 17:00 Oslo time and lists an 18:00 pitch deadline on 14 November. The official task asks for a ranked list of up to 20 before pitch evaluation, plus the presentation and GitHub repository. The immediate dependency is the organiser's full-sequence validator. The CPU analyses, code, full-pair list and presentation evidence are available now. [Event schedule and FAQ](https://oslo-ai-antibodies-hackathon.vercel.app/) · [Provisional ranked list](review/evidence/panel.csv)

## Before the deadline, in order

| Priority | Who can act and estimated effort | Deliverable and decision |
|---|---|---|
| 1. Obtain official validity for the exact pairs | Submission lead, about 15–30 minutes after receiving the organiser's current tool or portal | Use the provided paired Fab format and the actual validator's input contract. Save its version or portal timestamp, the VH/VL pair hash, track, verdict and reason for every row. Keep the original rank file. Put approved replacements in a separately dated file. A missing validator receipt leaves a slot provisional. |
| 2. Review the first four and reserves together | Assay lead and design lead, 15 minutes | Check the 4/8/12/16 prefixes and the reserves up to 20. Explain the rationale for each of the first four. For an ineligible candidate, prefer a valid replacement for the same experimental question, then observe the panel's distance rule and log the change. All 20 proposed pairs have a 120-aa VH and 107-aa VL. |
| 3. Incorporate completed work by teammates | Structural-analysis owner, 15–30 minutes once a complete result exists | The seed-42 batches in runs 009 and 010 are covered. For new seeds require a WT for every candidate–seed comparison, an identical input background, template, settings and chain mapping. Show per-seed deltas and denominators. If a sign reverses or required samples are missing, record that and preserve the original snapshot. |
| 4. Prepare the pitch handoff | Speaker and repository owner, 20–30 minutes | Use concept 1 and the saved evidence figure. Open the sequence list and reproduce the result before the pitch. Link the team's GitHub repository with the reviewed version of the materials they intend to publish. Preserve a copy of the exact ranked list that goes to the organiser. |

The project and evidence bundle are in English for the international judging panel. The host has a shared Git checkout and H100. These review tools read completed inputs and perform CPU calculations. They can run beside the team's design jobs. Each replay uses a new temporary directory. The original model outputs, measured data, run manifests and the teammates' pending changes remain available to their owners. [Run receipts](review/evidence/completed_batches.json)

## Reproduce at the normal entry point

From the Team 14 project or an extracted copy of the handoff, use the team's Python interpreter or an environment with the versions below. The bundle includes the 44 matched coordinate models, original confidence records, minimal cross-run inputs, both frozen FACS models and encoders, both HER2 tables, six published split CSVs, the VHH matrix archive and supplementary SPR table. It also captures the team's dated multi-seed tables and alternative ranking. Three small archives contain the **193 hashed original inputs**. The evidence replay needs neither the full GPU volumes nor container weights. [Core input manifest](review/evidence/replay-inputs.json) · [Late input manifest](review/evidence/late-inputs.json) · [Evidence checksums](review/evidence/SHA256SUMS)

```bash
.venv/bin/python review/replay.py
```

On another machine, create a Python 3.12 virtual environment, install the pinned packages with `python -m pip install -r review/requirements.txt`, and use its interpreter in place of `.venv/bin/python`. The tested SSH environment used Python 3.12.3, scikit-learn 1.9.1, NumPy 2.5.4, SciPy 1.18.1, pandas 3.1.1, joblib 1.6.0, Biotite 2.0.0 and Matplotlib 3.11.2. The command verifies the archive and original-file hashes, loads the saved team artifact, runs regression tests, refits the two source-assay controls using two CPU threads and checks regenerated analytical outputs. The replay requires only local CPU and disk. Exact PNG equality also depends on fonts and renderer versions. [Tested package versions](review/requirements.txt)

For a judge's previously unseen pair, supply a CSV with `query`, `heavy_variable` and `light_variable`. The same command accepts the proposed panel as a runnable example. It emits the parent substitution score, mutation count, local provided-data distance and local screen for a compatible construct. An incompatible framework, light chain or nonstandard sequence receives an explicit status with empty score fields. Nothing assigns a track or estimates an experimental KD. [New-pair evaluator](review/evaluate_pairs.py)

```bash
.venv/bin/python review/replay.py --evaluate review/evidence/panel.csv
```

The pair checksum is SHA-256 over UTF-8/ASCII bytes of `VH=<heavy>` then a newline, then `VL=<light>` then a final newline, with the uppercase, untagged variable sequences. Use this exact convention to match future validation and assay receipts. Sources for the research inputs are the organiser's supplied tables and reference coordinates, the authors' HER2 study, the Mehta split archive and the Smorodina matrices and supplementary SPR records. Use the original citations and applicable dataset terms when distributing outside the team. [HER2 study](https://doi.org/10.1101/2024.03.26.586756) · [Source splits](https://doi.org/10.5281/zenodo.10831512) · [VHH matrices](https://doi.org/10.5281/zenodo.18390239) · [VHH experimental supplement](https://doi.org/10.64898/2026.03.02.709004) · [1N8Z](https://www.rcsb.org/structure/1N8Z)

The isolated verification ran seven regression tests and reproduced six analytical JSON files, the complete 20-row CSV and the pitch figure byte for byte. In an independent check, the new-pair entry point matched all 20 stored candidate IDs, parent substitution scores and local distances from their full VH/VL sequences. The replay used fresh directories on the same SSH VM and its existing scientific Python environment. Reproducing model training or GPU inference on a different host remains a separate test.

## Implemented and frozen

| Addition | What it checks |
|---|---|
| `review/assay_transfer.py`, `split_check.py` | Paired WT identity, missingness, duplicate/overlap exclusion, fixed FACS and BLOSUM comparators, paired confidence interval with 2,000 seeded draws, within-mutation-count concordance and independently fitted published random/clonotype splits. [SPR outcomes](review/evidence/assay_transfer.json) · [Source-assay holdouts](review/evidence/split_check.json) |
| `review/structure_checks.py`, `completed_batches.py` | Four chain identities, modeled sequence equality, directional pair symmetrisation, fixed seeds and templates, coordinate footprints and raw score provenance. Counts cross-run repeats and tests identity of repeated controls. [Matched batch](review/evidence/structure_checks.json) · [Later runs](review/evidence/completed_batches.json) |
| `review/vhh_controls.py` | Same pair identities across three models, shuffled-pair negatives separated from experimentally measured absence of a fit, or missing material. [VHH results](review/evidence/vhh_controls.json) |
| `review/late_comparison.py` | Reproduces the concurrently developed ensemble's stored probabilities. Tests both FACS models, their mean and distance to the nearest measured high-FACS loop on identical constructs. Audits repetitions and WT seed coverage in the team's dated partial snapshot. [Comparator and seed findings](review/evidence/late_comparison.json) |
| `review/panel.py`, `evaluate_pairs.py`, `test_evidence.py` | Implements the four slot roles plus a diverse tail, matches exported VH/VL to hashed input, and applies the sequence baseline to new pairs. Regression cases cover duplicate/control treatment, conflicting labels, ties, chain order and the internal interface, light-chain contacts and residue IDs, ranking invariance and abstention on unsupported constructs. [Panel](review/evidence/panel.csv) |
| `review/plot_evidence.py`, `replay.py` | Rebuild the figure from saved results and reproduce all analytical outputs in an isolated directory. The research ledger can be inspected without spending credits again. [Figure](review/evidence/assay-and-contacts.png) · [AMASS receipts](review/evidence/amass_ledger.json) |

## Optional work with an explicit decision attached

* **Complete run 009 analysis before purchasing another fold.** The team prepared 60 candidate queries and a 30-member historical calibration panel with 10 binder, 10 intermediate, five weak quantified and five nonbinding-labelled examples. Selection was stratified by outcome. Verify each original label/assay and keep missing fits separate when testing whether geometry orders them. A tiny enriched panel can reveal a failure mode but cannot calibrate real-world prevalence or success probability. The 19-query seed-42 file already verifies three same-seed repeats. Check completion of later files directly. [Run 009 receipts](review/evidence/completed_batches.json)
* **Resolve the representation question before using JapanFold.** Confirm with the model's documented contract how an unguided four-chain input treats two HER2 fragments separated by missing coordinates. Only a result from comparable WT/variant inputs with an explicit decision it might change would justify the call. The observed OpenDDE historical P90 was about US$0.011 per target, or US$0.033 for the stored three-target request. It is an estimate. Nebius AntiFold schema access also worked. Its potential role is a sequence-compatibility diagnostic. Obtain a provider estimate for any job. [Input audit](CURRENT_PIPELINE_AUDIT.md) · [JapanFold interface](https://japanfold.aiand.com/docs/predictions/)
* **Test transport to another campaign as soon as one exists.** Freeze the baseline and model recipe, withhold an entire independently selected campaign, retain construct-level outcomes and repeat the paired comparison. Report missingness, class balance and dependent variant families. This directly addresses the selection bias left unresolved by bootstrapping a single retrospective library.

## After lab data arrive

Keep one record per proposed pair with its original rank, whether it passed the official validator, whether the lab selected it, produced material and measured each outcome, and the contemporaneous WT identifier. Retain all replicate values, units and assay conditions supplied. Record no material, no reportable fit, inconclusive and missing as distinct observations.

1. Compare fitted HER2 KD with the same-run WT using the lab's replicates, limits and interpretation. For reportability, show the number assessable per selected construct and per expressed construct. Preserve the original selection denominator.
2. Compare competitive binding directly with the organiser's criterion. Relate it separately to footprint overlap, the chain-specific scores and the free-loop hypothesis. Four tests give case evidence. Pooling later independent campaigns can test the decision rule.
3. Use the direct thermal measurement and same-format WT to determine thermal improvement. Record any stability result independently of the chemical-liability hypothesis. Apply the organiser's S/A/B criteria only after the relevant experimental outcomes are known.

**Research expenditure.** This review used 47 AMASS credits, US$0.47, across searches, DOI resolution and six full-record requests. Closing balance for that check was 10,448 credits. Compute for the retrospective review used the team's CPU environment. This review launched zero paid prediction jobs. Later model work by other team members is outside that accounting. [Metered calls](review/evidence/amass_ledger.json)
