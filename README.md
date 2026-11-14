# Umi-Zoomi

> The repo of the hackathon winners

Team 14 · AI × Antibodies Hackathon, Oslo · 14 November 2026

Improving **trastuzumab** against **HER2**, with Apheris Foundry, Nebius
and JapanFold.

---

## Current evidence and submission materials

The current proposal is a ranked panel of 20 Fab optimisation designs. Start
with the [ranked full-sequence CSV](review/pitch_her2/Proposed_ranked_20.csv),
[selection rationale](review/pitch_her2/Rangering_begrunnet.md), and
[pitch deck](review/pitch_her2/HER2_pitch.pdf). The first four proposed tests
are `anas_007`, `anas_015`, `anas_009`, and `r004_cdrh3_3`. Earlier ranking
files remain as dated alternatives; they are not additional submissions.

- [Score ledger](notes/SCORES.md): generated scores, source links, seeds and
  small raw-score snapshots that can be checked from a fresh checkout.
- [Pipeline audit](CURRENT_PIPELINE_AUDIT.md) and
  [execution roadmap](EXECUTION_ROADMAP.md): controls, assay transfer,
  reproducibility and remaining experimental work.
- [De novo campaign](review/denovo/CAMPAIGN_RESULTS.md): 96 new sequences
  and independent model checks. Three VHHs remain exploratory reserves;
  weak docking support does not establish new HER2 binding.
  The [offline report](review/denovo/report/report.html),
  [evidence figure](review/denovo/report/campaign-evidence.pdf), and
  [candidate export](review/denovo/report/exploratory-candidates.csv)
  include compact structures and receipts.
- [Validator status](notes/ABGUARD.md): the recovered local build and its
  limitations. A local pass is distinct from final organiser acceptance.
- [JapanFold handoff](notes/japanfold/README.md): the earlier Fab pilot
  plan, preserved with its date and links to the subsequent campaign.

No new candidate has measured SPR affinity, competitive binding or Tm in
this repository. Model confidence, FACS classifier outputs, chemical
liability flags and predicted binding-ddG are computational evidence.

The score ledger requires only Python's standard library:

```bash
python3 scripts/scores.py --check
python3 -m unittest discover -s scripts -p 'test_scores.py'
```

The frozen optimisation review can be replayed on CPU after installing
`review/requirements.txt`, without downloading data or submitting jobs:

```bash
python3 review/replay.py
```

Raw GPU tensors, full model archives and weights remain excluded. Compact
campaign reports, configuration, job receipts and score snapshots are
published; see the campaign documentation for the original-output audit.

---

## The task, and what actually decides it

Two tracks, judged separately:

- **Optimisation** — mutate trastuzumab, keeping its format. CDRH3 at most
  70 % identical to trastuzumab, and at least 2 mutations away from every
  one of the 525,063 provided sequences.
- **De novo** — a new HER2 binder under 70 % identity to any known
  antibody. VHH, scFv or Fab.

Adaptyv then measures three things against a measured trastuzumab
baseline: **binding** by SPR, **epitope preservation** by competitive
binding against trastuzumab, and **thermostability**.

A design that beats the baseline on all three is S-tier, two is A-tier,
one is B-tier, and teams are ranked by S-tier count. **Two designs that
improve all three beat ten that each improve one.** That is the single
fact that shapes everything here: we rank on three axes, not on affinity.

Only 100 designs are tested in total across 16 teams, from ranked lists of
up to 20. The ranking is the deliverable.

## What is in here

```
scripts/
  novelty.py     the novelty filter, reimplemented locally (see below)
  novelty        wrapper: `novelty check <CDRH3>`
  report.py      refold metrics + designed CDRH3 + novelty, per run
  env.sh         model image tags and Foundry credentials, one source
  gpurun         a lock around the single H100, so five people can share it
  newrun         a numbered run directory with a reasoning stub
  gpu.sh         who is on the GPU right now
  py             the team venv
notes/
  DECISIONS.md   every choice and why, written as it was made
  SCORES.md      every number and where it came from
runs/
  NNN-who-what/  one directory per run: NOTE.md, config.json, metrics
```

Large inputs and model outputs are deliberately not committed. The data
comes from `s3://apheris-oslo-hackathon` and is reproducible with one
`aws s3 sync`; what is committed is the configuration and the reasoning,
which is what makes a run repeatable.

## We had to rebuild the novelty filter

`abguard`, the official submission checker, **was not installed on our
VM**, although the task description says it is. A design that fails the
novelty filter is never sent to the lab, so shipping designs without
checking them is the most expensive mistake available.

So `scripts/novelty.py` implements the two published numeric rules against
every provided CDRH3:

```bash
novelty build                 # caches the provided sequences, once
novelty check WASSSEYYFD      # one or many, or --file / --csv
```

It reports, per design, the minimum distance to anything in the provided
data and the identity to trastuzumab's own CDRH3 (`WGGDGFYAMD`).

Our cache contains **525,063** unique CDRH3s, which matches the figure the
organisers published exactly. That agreement is why we trust the filter.

It is not the official tool. A pass here means "worth spending a refold
on", not "accepted".

## Results

### Run 001, baseline

The organisers' own HER2 pipeline, unchanged, to prove the chain works
before changing anything: RFD4-Proteina `her2-novel-2026-11-09` → 4
designs → top 2 selected → refolded with Boltz-2 on the 1N8Z template →
scored.

| design | min_ipae | iptm | binder_plddt | backbone_rmsd | CDRH3 | novelty distance | % id to trastuzumab |
| --- | --- | --- | --- | --- | --- | --- | --- |
| her2_cdrh3_3 | 0.310 | 0.965 | 98.51 | 0.744 | WASSSEYYFD | 3 | 30 % |
| her2_cdrh3_2 | 0.331 | 0.946 | 95.57 | 1.041 | WGPPYFYAMD | 2 | 70 % |

Three things we take from this, all recorded in `notes/DECISIONS.md`:

1. **The `pass` column comes out empty** for the HER2 exercise, as the
   Apheris documentation warns. So we rank on `min_ipae`, `iptm` and
   `binder_plddt`.
2. **`her2_cdrh3_2` sits exactly on both limits**: distance 2, identity
   70 %. The task PDF says "under 70 %", the Apheris slides say "at most
   70 %". A design on the line is a coin flip we are not taking, so our
   internal bar is distance ≥ 3 and identity ≤ 60 %.
3. **Those confidence numbers are inflated.** The model was handed the
   framework and the target, so an iptm of 0.965 says the geometry is
   self-consistent, not that the design binds. Confidence is not affinity,
   and affinity ranking is the weakest thing in this field.

## Reproducing a run

On a hackathon VM with the Foundry images present:

```bash
. scripts/env.sh
aws s3 sync s3://apheris-oslo-hackathon/rfd4-proteina/ data/rfd4-proteina/
cd data/rfd4-proteina/docs
N=4 TOPN=2 OUT=runs/her2-baseline bash Scripts/run-her2.sh all
```

Then, from the repo root:

```bash
py scripts/report.py <path-to>/scored-boltz2/refold_metrics.csv
```

Every Foundry task writes a `config.json` beside its output; those are
committed, so a run can be replayed exactly, seed included.

## Choosing the model

From the Apheris measurements on the trastuzumab CDRH3 task:

| checkpoint | finds known binders | passes novelty | interface error |
| --- | --- | --- | --- |
| `antibody-2026-10-30` | 0 % | 100 % | 8.2 Å |
| `her2-2026-11-07` conservative | 21 % | 0 % | 9.4 Å |
| `her2-2026-11-07` balanced | 21 % | 6 % | 9.1 Å |
| `her2-2026-11-07` exploratory | 0.3 % | 74 % | 9.1 Å |
| `her2-novel-2026-11-09` | 4 % | 86 % | **6.8 Å** |

The conservative weights are the trap: rediscovering a known binder 21 %
of the time sounds good and is worth nothing, because a known binder fails
the novelty filter. We use `her2-novel-2026-11-09`. The HER2 weights only
redesign CDRH3; other CDRs need `antibody-2026-10-30`.

## Working on the VM

One shared Linux user and one H100, so:

```bash
echo yourname > ~/.team_me     # your prompt, and your own Claude login
team14-help                    # the shortcuts
gpu                            # is the card free?
gpurun yourname <command>      # queue behind whoever holds it
newrun yourname slug           # a run directory with a reasoning stub
```

Long jobs go in `tmux`. Scratch lives in `people/<yourname>/`.

`scripts/env.sh` reads the registry credentials out of `~/.bashrc` rather
than storing them, because this repo is public. A pre-commit hook rejects
credential files, secret-shaped lines and anything over 20 MB.

## Stack

Apheris Foundry (RFD4-Proteina, OpenFold3, Boltz-2, Protenix, ESMFold2,
Mol-1) on an H100; Nebius Scientific AI for hosted antibody-specific
models (NanoBodyBuilder2, AntiFold, IgBert, stab-ddG); JapanFold for
RoseTTAFold3, OpenDDE and AF2-IG; Amass for checking claims against
primary sources.
