# Current submission and result CSVs

Use **TOP4_INNSENDING.csv** for the four current recommended constructs,
in the given row order. These are four optimisation Fab-variable pairs.
Do not combine this file with older panels or count alternative rankings
as additional designs.

| File | Rows | Purpose |
|---|---:|---|
| [TOP4_INNSENDING.csv](TOP4_INNSENDING.csv) | 4 | Ranked submission with complete sequences and track metadata. |
| [TOP4_ABGUARD.csv](TOP4_ABGUARD.csv) | 4 | Same sequences/order; exactly the validator's five required columns. |
| [TOP4_RESULTATER.csv](TOP4_RESULTATER.csv) | 4 | Per-candidate computational evidence, rank and selection reason. |
| [ALLE_KANDIDATER_RESULTATER.csv](ALLE_KANDIDATER_RESULTATER.csv) | 90 | Full current candidate-result table. Not a submission file. |
| [TOP20_UTKAST.csv](TOP20_UTKAST.csv) | 20 | Optional 18+2 draft. Not the current four-design recommendation. De novo database eligibility is unresolved. |
| [TOP4_VALIDERT.csv](TOP4_VALIDERT.csv) | 4 | Fresh local-validator output; keep the ranked input authoritative. |

The submission header is:

```csv
sequence_id,kind,heavy_sequence,light_sequence,design_description,track
```

All four have `kind=paired`, `track=optimization`, VH120 + VL107 =227
amino acids. Files are UTF-8 with comma delimiters and CSV quoting.
`TOP4_ABGUARD.csv` omits only `track`; local abguard requires the other
five fields and assigns its own novelty class.

We verified exact sequence equality between submission and evidence,
unique IDs and constructs, row order, allowed amino acids, combined length,
the original validation receipt's input hash, and a new explicit-reference
validator run with no `--drop`: 4 input rows, 4 accepted.
[VERIFICATION.json](VERIFICATION.json) records file hashes and the commands.
The installed local build does not establish final organiser acceptance or
cross-team uniqueness.

An empty result cell means unavailable, not zero. No new SPR, competitive
binding or direct thermal measurement is claimed. The current shortlist
differs from the earlier 20-design baseline and earlier 18+2 proposals;
use the source run014 evidence for these four.
