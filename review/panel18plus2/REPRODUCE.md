# Reproduce the 18 + 2 review

The working project is `/home/hackathon/team14`. The model receipts, inputs, run scripts, coordinates, and preserved diagnostics are in `runs/review-apheris-of3-panel/`. The reviewed deliverables and analysis scripts are in `review/panel18plus2/`. The main ranked list is `RANKED_18_PLUS_2.csv`. The reproducibility ZIP includes a model-run snapshot, analysis code, third-party source tables used in the thermal audit, historical results, and copies of the earlier candidate summaries used in the decision. The original team project supplies the helper modules, the large local training dataset, and the fitted baseline model.

## Repeat analysis offline

From the team repository, set the paths below. Use a fresh directory for every replay. The analysis reads weights and coordinates only when required. No external API keys are needed.

```bash
teamdir=/home/hackathon/team14
source_dir="$teamdir/review/panel18plus2"
panel_replay=$(mktemp -d)
cp "$source_dir"/{order.json,original_reference.csv,DSF1.csv,DSF2.csv,original_commit.txt,flab_commit.txt} "$panel_replay/"
python3 "$source_dir/build_panel.py" "$teamdir" "$panel_replay"
ref=/home/hackathon/tools/abguard-venv/lib/python3.12/site-packages/abguard/reference_data
checker=/home/hackathon/tools/abguard-venv/bin/abguard
"$checker" team-validate "$panel_replay/RANKED_18_PLUS_2.csv" --reference-db "$ref" -o "$panel_replay/validator-output.csv"
"$checker" team-validate "$panel_replay/RANKED_18_PLUS_2.csv" --reference-db "$ref" --all-liabilities -o "$panel_replay/liabilities.json"
"$teamdir/.venv/bin/python" "$source_dir/historical_binding.py" "$teamdir" > "$panel_replay/historical_binding.json"
python3 "$source_dir/thermal_reference.py" "$teamdir" "$panel_replay" > "$panel_replay/thermal_reference.json"
"$teamdir/.venv/bin/python" "$source_dir/finalize.py" "$teamdir" "$panel_replay"
cmp "$source_dir/RANKED_18_PLUS_2.csv" "$panel_replay/RANKED_18_PLUS_2.csv"
cmp "$source_dir/OPENFOLD_RESULTS.csv" "$panel_replay/OPENFOLD_RESULTS.csv"
cp "$source_dir/deck.py" "$panel_replay/"
uv run --isolated --no-project --with python-pptx==1.0.2 --with pymupdf==2.1 python "$panel_replay/deck.py"
```

Each coordinate is matched to its input chain by full sequence before scoring. A failure in chain identity, reference surface, sample counts, paired sequence identity, order, or membership aborts verification. Contacts use model 1, non-hydrogen atoms, positive occupancy and 4.5 Å. The Jaccard column excludes ten reference-unresolved positions from the comparison. Their modeled contacts are counted separately. Recovery counts use the same 19 observed crystal residues in every arm.

## Repeat GPU inference

The runs are an optional separate step. The digest and seeds are recorded in `VERIFICATION.json`. First batch, extension and pair-repeats have their own input and scripts. To repeat one arm with the original team GPU lock, run `bash run.sh NEW_OUTPUT_NAME` or `bash run_her2_template.sh NEW_OUTPUT_NAME` from its directory. The H100 was already allocated. There were no paid inference calls, lab orders or API charges from this review. VM running time is separate. A dry run does not validate template parsing in this CLI. The first attempt at the organiser's two-piece template failed because local label sequence IDs on C/D were interpreted as missing sequence. The diagnostic log is kept. The successful target-only template is generated from the original coordinates by `make_template.py`. The conversion joins the two observed HER2 stretches at their correct indices, supplies the full native sequence, and checks that every retained atom coordinate, residue identity and author position is unchanged.

## Distinguish three sources of evidence

The `apheris-openfold3` receipts with the provider module and checkpoint identify the new local runs. The earlier hosted JapanFold OpenFold3 runs are a separate delivery route. The organizer's competition scores arrive after lab allocation. No organizer acceptance receipt or Adaptyv result accompanies this package. Published comparative thermal data are from other constructs and assay conditions.

The historical KD group was assembled with the existing `review/assay_transfer.py` and `review/four_slots/historical.py`. Files in the public sources folder can be obtained from the [study authors](https://github.com/AbSciBio/unlocking-de-novo-antibody-design/tree/cd2bd4b6932b5301d435555dc22084d407e4b92b) and the [FLAb benchmark](https://github.com/Graylab/FLAb/tree/e05e3f0135783ffb7de412df6a1467e7a0031911/data/thermostability).
