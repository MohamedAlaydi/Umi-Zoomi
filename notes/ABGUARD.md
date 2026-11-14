# abguard, the official submission checker

**14 Nov, 13:10.** It is on PATH again. `CURRENT_PIPELINE_AUDIT.md` says
"No `abguard` executable found on PATH" — that was true when it was
written and is no longer true.

```bash
abguard --help
```

## Where it came from, and why that matters

The organiser material lists abguard under "Pre-installed on every
machine". It was not: nothing on PATH, nothing in `uv tool list`, nothing
in the S3 bucket (all 81 objects checked, no match).

It was installed here on 11 Nov from `/home/hackathon/repos/apheris-abguard-demo`,
a directory that has since been deleted. What survived is the extracted
build in the uv cache, which is one `uv cache clean` from being gone, so it
is now copied out:

- `/home/hackathon/tools/abguard-venv` — a relocatable venv, 581 MB
- `~/.local/bin/abguard` → symlink into it

Verified independent of the cache: no path under the tree references
`.cache/uv`, `pyvenv.cfg` carries `relocatable = true`, and the launcher
resolves its interpreter relatively through `realpath`.

**Two different builds were in that cache, both calling themselves 0.1.0.**

| Cache entry | Built | Subcommands | CDRH3 reference |
| --- | --- | --- | --- |
| `Qac-5ZxtgcgWcIUj` | 11 Nov 13:52 | 5 | missing |
| `kz8D0M1psy9lr-7f` | 11 Nov 16:17 | 10 | 610,109 rows |

We installed the 16:17 one. The earlier build has no novelty machinery at
all. There is no `--version` flag and no `version` subcommand, and the
metadata says `0.1.0` for both, so **the version string cannot tell you
which build you are running**. Count the subcommands instead.

That is also the reason to ask Apheris for the official wheel before we
submit: what we have is a build from a deleted demo directory, and we
cannot name its version in a submission receipt.

## What it does

Ten subcommands. The five that grade:

| Command | Does |
| --- | --- |
| `team-validate` | Validate one team's submission table |
| `competition-validate` | Validate every team's submission in a folder, reject shared sequences |
| `liability-report` | How often each LAP liability occurs in a submission |
| `novelty-report` | How novel each design is, filtering nothing |
| `reference` | Print the LAP Antibody Liability Reference it implements |

Plus `dashboard` (marimo) and four `reference-*` commands for building,
ingesting, exporting and inspecting a reference database.

## The submission table

```bash
abguard team-validate designs.csv --no-novelty
abguard team-validate designs.csv --reference-db <bundle-or-duckdb>
```

Columns: `sequence_id`, `kind`, `heavy_sequence`, `light_sequence`,
`design_description`. Rows are partitioned on `kind` (`vhh`, `scfv`,
`paired`) and each partition is validated against its own schema.

Reads `.csv .tsv .parquet .arrow .feather .ipc .json .jsonl .ndjson .avro
.xlsx .tab .txt .pq`.

Options: `--drop` (drop bad rows instead of failing), `--all-liabilities`
(every liability per design, JSON), `-o/--output`, `--reference-db`,
`--no-novelty`, `-v/--verbose`.

**`team-validate` refuses to run unless you pass either `--reference-db`
or `--no-novelty`.** Skipping the novelty check is always explicit, which
means a run without a receipt is visible as such.

## The novelty gate

With `--reference-db`, a design must differ from trastuzumab and from
every known CDRH3 by at least **3 mutations in CDRH3** if it is a
trastuzumab variant (>=70% identity), or **2** if de novo.

Compare that with `scripts/novelty.py`, which matches 525,063 loops; the
bundled reference here has 610,109 rows, IMGT-numbered, `min_confidence
0.1`. The local script stays useful for triage, but it is not this.
