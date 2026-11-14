# Replay on the team VM

Use a fresh directory for derived CSV and JSON files. These two commands recompute the 104 native-context overlays, proposed list, source-matched scores and historical counts.

```bash
project=/home/hackathon/team14
src="$project/review/regelkontroll-premie/replay"
replay_dir=$(mktemp -d)
cp "$src"/{1n8z.cif,field-guide.html,thermal-flags.json,thermal-input.csv,common-panel-snapshot.csv} "$replay_dir/"
"$project/.venv/bin/python" "$src/context_check.py" "$project" "$replay_dir/1n8z.cif" "$replay_dir/ECTODOMAIN.csv"
python3 "$src/audit_panel.py" "$project" "$replay_dir"
cmp "$project/review/regelkontroll-premie/RANK_AND_EVIDENCE.csv" "$replay_dir/RANK_AND_EVIDENCE.csv"
```

Use the installed abguard environment and explicit reference bundle as in the earlier panel18plus2/REPRODUCE.md. Run team-validate on PRIZE_TOP20.csv and PRIZE_TOP10.csv separately. The sequence-only thermal motif benchmark used team-validate with --no-novelty --all-liabilities on thermal-input.csv, because known published comparators should be retained. Verify native coordinates against https://files.rcsb.org/download/1N8Z.cif and the captured guide against https://oslo-ai-antibodies-hackathon.vercel.app/participant_guide. Geometry considers native extracellular protein atoms with coordinates, and excludes glycans and the membrane.

The parallel team edited the live run012 submission export during this audit. Its sequence membership still overlapped on exactly 19/20. The included CSV freezes the compared version.
