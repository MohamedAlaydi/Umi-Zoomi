# Umi-Zoomi

Team 1 · AI × Antibodies Hackathon, Oslo · 14 November 2026

Improving **trastuzumab** against **HER2**, with Apheris Foundry, Nebius,
JapanFold and Amass.

## Latest design audit and immediate submission files

The consolidated [submission and result CSV package](submission/README.md)
contains the current ranked four, their evidence, all 90 candidate results,
an exact five-column validator input and a fresh 4/4 validation receipt.
The optional 20-row draft is labelled separately.

The fresh evaluation retrains on the original assays, generates new H3 sequences,
checks full607-residue HER2 complexes, and tests a separate framework stability
hypothesis. **The four current recommendations, in priority order, are
[`TOP4_INNSENDING.csv`](runs/014-codex-fresh-evaluation/TOP4_INNSENDING.csv).**
They use the requested six-column schema and complete sequences. All four are
optimisation designs and pass local abguard with an explicit reference.

- [Top-four evidence](runs/014-codex-fresh-evaluation/TOP4_RESULTATER.csv)
- [Single team-named CSV for the Slack handoff](submissions/umi-zoomi.csv)
- [18+2 proposal](runs/014-codex-fresh-evaluation/18plus2_DRAFT_optimisation_first.csv)
- [Fresh report and figures](review/fresh_evaluation/report/LES_MEG.md)
- [Updated pitch deck in the original visual style](review/pitch_final/deck.html) · [PDF](review/pitch_final/Umi-Zoomi-team14-fallback.pdf)
- [Slide-by-slide breast cancer pitch script](review/pitch_final/SPEAKER-SCRIPT.md)

This is experiment priority, not measured improvement or confirmed S-tier.
The two exploratory de novo entries still require the organisers' complete
known-antibody database check. The report records the available results and
unfinished or failed remote calculations at its snapshot time.

**The earlier baseline panel is [`notes/RANKED_CANDIDATES.csv`](notes/RANKED_CANDIDATES.csv):**
20 ranked optimisation designs, every one of them passed through the official
`abguard` with its receipts committed. The order is argued design by design in
[the ranking rationale](review/pitch_her2/Rangering_begrunnet.md).

---

## The finding, in one paragraph

The original SPR table includes eight WT observations, with a median KD of
0.1345 nM;0.152 nM was the first reported observation. In the initial design phase,
so we asked a different question: which parts of the molecule are actually
free to change? `scripts/contacts.py` measures every HER2 heavy atom within
4.5 Å of trastuzumab in the hackathon's own 1N8Z crystal structure. **19 HER2
residues are in contact. Of the ten CDRH3 positions the HER2 model may
redesign (99 to 108, `W G G D G F Y A M D`), only four touch HER2: W99, G103,
F104, Y105.** Six touch nothing at all. Two of those six carry documented
degradation liabilities. That guided the initial enumerated designs; the fresh
evaluation also explores other H3 substitutions and verified framework changes.

The contact set is identical at 4.5 Å and 5.0 Å. D102 is the first free
position to appear as you widen, at 5.5 Å, and it sits near the rim. The
sweep is `scripts/cutoff_sweep.py` and it is committed, because the whole
argument rests on that one number.

## What decides this competition

Two tracks, judged separately. Adaptyv makes the designs and measures three
things against a measured trastuzumab baseline: **binding** by SPR, **epitope
preservation** by competitive binding against trastuzumab, and
**thermostability**. All three beaten is S-tier, two is A-tier, one is B-tier,
and teams rank by S-tier count. **Two designs that improve all three beat ten
that each improve one.** So we rank on more than one axis.

Only about 100 designs are tested across 16 teams, from ranked lists of up to
20. **The ranking is the deliverable**, which is why most of this repo is
about selection rather than generation.

## The experiment that produced the submission

| run | what changed | result |
| --- | --- | --- |
| 001 | organisers' pipeline, unchanged | works end to end; see the confidence note below |
| 004 | 40 designs, CDRH3 loop free | **0 of 10 refolds kept all four contacts.** G103 and F104 lost every single time |
| 005 | the four contacts pinned in the input | **10 of 10 kept all four.** But 9 of 10 then failed novelty |
| 006 | the legal CDRH3 space enumerated and scored | the candidate pool the submission is drawn from |
| 007 | pinned, plus `--sequence-tsr-k 1` for loop diversity | restores novelty headroom while keeping the anchor |
| 008 | one row per candidate, every gate by one code path | the first table that records *why* anything failed |
| 009 | the same sequences refolded at six Boltz-2 seeds | **measures the noise floor.** See below |
| 010 | every ideal, novel, cysteine-free loop refolded | 16 distinct loops; controls reproduce run 006 exactly |
| 011 | a de novo VHH campaign | on hold, and the reasoning is written down |
| 012 | selection, StaB-ddG validation and `abguard` | the validated ranked 20 |
| 013 | wild-type trastuzumab scored in the same table as the designs | the liability claim, stated by the tool |

Run 004 is the result that drove everything. With the loop free the model
ignored the interface, so we stopped asking it to care and wrote the
measurement into the input as a constraint
(`design_inputs/her2_cdrh3_anchored.yaml`). That worked, and immediately cost
us novelty, which is what run 007 exists to fix.

## What we do not claim

This section is deliberately placed before the results.

- **Our structural scores cannot separate these designs.** Run 009 refolded
  the same sequences at six Boltz-2 seeds and measured a seed-to-seed SD of
  **0.0147** on `iface_min`. A difference smaller than about 0.054 is not
  detectable at one seed, and the submitted designs sit inside that noise
  against wild type. `iface_min` is a plausibility floor in our ranking, never
  an affinity.
- **Confidence does not track the epitope.** In the baseline, the design with
  the *best* confidence scores (iptm 0.965, min_ipae 0.310) had lost **half**
  its contact residues. iptm is what the pipeline hands you. We rank on
  contact conservation first and confidence second.
- **A dumb baseline beats our own model.** `review/assay_transfer.py` tests
  our FACS classifier against held-out measured SPR. Across 584 assessable
  historical variants, an untuned BLOSUM62 score against the parent reaches
  **0.847** AUROC where our classifier reaches **0.751**, with a paired
  bootstrap interval of +0.061 to +0.132. Part of that historical series was
  itself selected using BLOSUM, which we say out loud because it limits the
  claim. We report both scores and rank on where they agree.
- **Our classifier ranks trastuzumab above every design we made** (0.930).
  It is trained on the organisers' own FACS screen, 23,834 rows, test AUC
  0.927 and AP 0.830 on their held-out split, and it has never seen a
  structure. It is the only score here grounded in laboratory measurement,
  and this is what it says.
- **The parent is in the table as a control, and it is hard to beat.**
  Trastuzumab itself scores 6/6 on the loop contacts and 96.5 % mean footprint
  overlap. Several of our designs are below it on overlap. That is visible in
  the ranking rather than hidden.
- **We are not claiming thermostability.** We remove a documented aspartate
  isomerization site (D102: Harris 2001, PMID 11270864; Spanov 2022, PMID
  35047480) and a methionine oxidation site (M107: Hensel 2011, PMID
  21390239; measured as a quality attribute in the CT-P6 biosimilar, PMID
  30386977). Those are chemical degradation over time. Adaptyv measures a
  melting temperature. Whether the two are related is a question for the lab,
  not a claim for a slide.
- **We remove two liabilities, and eleven of the twenty add one.** Run 013 scores
  wild-type trastuzumab in the same table as the ranked 20, with the same tool and
  the same reference, so the claim is `abguard`'s statement rather than ours. It
  flags **eight** liabilities on the parent, a molecule that has been a medicine
  since 1998. Two of them are the ones we target: `Isom` at IMGT 110/111, carrying
  the motif `DG`, which is D102 followed by G103, and `MetOx` at IMGT 115, which is
  M107. **All 20 designs remove both.** Nine add nothing the parent did not already
  have, including ranks 3 and 4. Eleven add one, and for eight of those a tryptophan
  now sits where the parent had a methionine, so at that position the oxidation
  liability changed class rather than disappearing. **Ranks 1 and 2 are among the
  eight.** The per-design table is
  [`runs/013-claude-liability-control/comparison.csv`](runs/013-claude-liability-control/comparison.csv)
  and the reading is in that run's `NOTE.md`.
- **One correction we had to make.** A web search told us M107 was not
  oxidation prone. The primary records said the opposite. Without checking we
  would have left a liability in the molecule.
- **One finding we retracted.** An earlier "epitope footprint erosion" count
  turned out to be sub-ångström relaxation of a templated prediction, on
  light-chain contacts we never touched. It is gone, not buried.

## The novelty filter, and the correction

`abguard` is the official submission checker. The task material lists it as
pre-installed; it was not on our VM, so we first reimplemented the two
published numeric rules in `scripts/novelty.py` against the 525,063 provided
CDRH3s.

**We then found the real tool, and that changed the answer.**
[`notes/ABGUARD.md`](notes/ABGUARD.md) records where it came from and how it
was made relocatable, including the detail that the version string cannot
tell you which build you are running, so you have to count the subcommands.
Its reference manifest holds **610,109** CDRH3 rows, not 525,063, and it
draws on sources the provided tables do not include, such as patent
sequences. Our local filter had been checking against an incomplete
reference the whole time.

Everything in the submission is now validated with the real tool. The
receipts in `runs/012-codex-18plus2/validation/` record the input hash, the
package hashes and the reference manifest hash. All 20 chain pairs pass, at
CDRH3 distance 3 against a required 3.

`scripts/novelty.py` stays in the repo because it is what we used before, and
because the disagreement between the two reference sets is the most useful
thing we learned about this filter.

## How the ranking works

More than one column, and none of them is a predicted affinity:

1. **Contacts kept**, measured against the crystal structure and counted per
   design across six model runs, so a single lucky pose cannot carry a design.
2. **Footprint overlap**, the Jaccard index for the whole Fab–HER2 contact set
   against the crystal, averaged over the same six runs. Extra and missing
   HER2 residues both count against it.
3. **The BLOSUM62 sequence score** against the parent, which is the one signal
   with held-out measured SPR behind it.
4. **Liability state**, by `abguard`'s own checker, which names what each
   design removes and what it introduces.

Then a hard novelty gate, and `iface_min` only as a floor.
[`notes/SCORING.md`](notes/SCORING.md) sets out how these computational
scores differ from the three properties the lab actually measures.

**The guaranteed four are a designed experiment, not a top four.** Ranks 2 and
3 (`HER2-OPT-015` and `HER2-OPT-009`) carry the same four building blocks and
the same sequence score of 32, but one keeps all four contacts in six of six
model runs and the other in none of six. Rank 4 (`HER2-GEN-003`) comes from a
different design method and keeps only two of the four original residues, yet
contacts at all four positions in six of six. Whichever way those wells read,
they answer whether pinning the measured contacts is what buys epitope
preservation. Rank 1 (`HER2-OPT-007`) is the one design that leads on both the
sequence score and a replicated contact face.

Public candidate IDs map to the original model queries in
[`notes/CANDIDATE_IDS.csv`](notes/CANDIDATE_IDS.csv). Original evidence stays
under its original query name.

## The de novo track, and why it is on hold

Run 011 is a full de novo VHH campaign: target preparation against the 1N8Z
HER2 entity, generation, refolding by OpenFold3 and Mol-1 on both a short and
a long HER2 sequence, and `abguard` validation. Its candidates clear novelty
comfortably, at CDRH3 distance 10 and 16 against a required 2.

We are not spending early slots on them, and the reason is a control.
On the short reference, OpenFold3 recovered only 2 of the 19 crystal contact
residues **for trastuzumab itself**, while Mol-1 recovered 18 of 19. Against
that, none of the three de novo designs recovers anything under OpenFold3,
and only one (`novel3`) recovers 8 of 19 under Mol-1, in both setups. That is
the one worth following up, and it is not enough to justify two of four
guaranteed tests. The full argument is in
[the ranking rationale](review/pitch_her2/Rangering_begrunnet.md).

## Every number, and where it came from

The score ledger is **generated**, not hand-written:

```bash
py scripts/scores.py            # rebuild from the files the models wrote
py scripts/scores.py --check    # re-read every path the table cites, and fail on drift
```

- [`notes/SCORES.md`](notes/SCORES.md) is the overview and the reading order.
- `notes/SCORES_FULL.md` is the full ledger, 2168 rows, each with the path it
  came from. `--check` currently passes on all of them.
- `notes/SCORES.csv` is the same table for machines.

Small score and provenance files are copied byte for byte into each run's
`score-evidence/` directory with a `SHA256SUMS`, so every cited file exists in
a fresh checkout without the VM's data directory. Reasoning lives in
[`notes/DECISIONS.md`](notes/DECISIONS.md), not in the ledger.

## Run it yourself

Replay the whole review in a temporary directory from its frozen inputs,
including the unit tests and the five evidence reports:

```bash
python3 review/replay.py
```

Apply our frozen sequence baseline to **a Fab CSV we have never seen**:

```bash
python3 review/replay.py --evaluate your_pairs.csv
```

To reproduce a design run on a hackathon VM with the Foundry images present:

```bash
. scripts/env.sh
aws s3 sync s3://apheris-oslo-hackathon/rfd4-proteina/ data/rfd4-proteina/
cd data/rfd4-proteina/docs
N=4 TOPN=2 OUT=runs/her2-baseline bash Scripts/run-her2.sh all
py scripts/report.py <path-to>/scored-boltz2/refold_metrics.csv
```

Every Foundry task writes a `config.json` beside its output and those are
committed, so a run replays exactly, seed included. Large inputs and model
outputs are deliberately not committed; the data comes from
`s3://apheris-oslo-hackathon` and is one `aws s3 sync` away.

## What is in here

```
scripts/
  contacts.py      the contact measurement, on 1N8Z
  cutoff_sweep.py  the 4.0 to 6.0 Å sensitivity sweep
  binder_model.py  the classifier, trained on the measured FACS screen
  novelty.py       our reimplementation of the two published novelty rules
  scores.py        generates the score ledger, and --check verifies it
  first_pass.py    one row per candidate, every gate evaluated by one code path
  multiseed_analysis.py  the seed-noise and calibration analysis
  report.py        refold metrics, designed CDRH3 and novelty, per run
  env.sh           model image tags and Foundry credentials, one source
  gpurun, gpu.sh   a lock around the single H100, so five people can share it
  newrun           a numbered run directory with a reasoning stub
notes/
  RANKED_CANDIDATES.csv  the submission: 20 designs, in order
  CANDIDATE_IDS.csv      public IDs mapped to the original model queries
  SCORING.md             how these scores differ from what the lab measures
  SCORES.md / SCORES_FULL.md / SCORES.csv   the generated ledger
  DECISIONS.md           every choice and why, written as it was made
  ABGUARD.md             where the official checker came from, and its reference
  TRASTUZUMAB.md         the literature behind the design hypothesis
  AMASS.md               how claims were checked against primary records
  ROLES.md               how the team split the work
review/
  assay_transfer.py      the held-out SPR test that BLOSUM62 wins
  replay.py              replay the review, or evaluate an unseen Fab CSV
  pitch_her2/Rangering_begrunnet.md   the ranking, argued design by design
  denovo/                the de novo campaign and its readiness review
runs/NNN-who-what/       one directory per run: NOTE.md, config.json, metrics
```

## Choosing the model

From the Apheris measurements on the trastuzumab CDRH3 task:

| checkpoint | finds known binders | passes novelty | interface error |
| --- | --- | --- | --- |
| `antibody-2026-10-30` | 0 % | 100 % | 8.2 Å |
| `her2-2026-11-07` conservative | 21 % | 0 % | 9.4 Å |
| `her2-2026-11-07` balanced | 21 % | 6 % | 9.1 Å |
| `her2-2026-11-07` exploratory | 0.3 % | 74 % | 9.1 Å |
| `her2-novel-2026-11-09` | 4 % | 86 % | **6.8 Å** |

The conservative weights are the trap: rediscovering a known binder 21 % of
the time sounds good and is worth nothing, because a known binder fails the
novelty filter. We use `her2-novel-2026-11-09`. The HER2 weights only
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
`scripts/env.sh` reads the registry credentials out of `~/.bashrc` rather than
storing them, because this repo is public. A pre-commit hook rejects
credential files, secret-shaped lines and anything over 20 MB.

## Stack

Apheris Foundry (RFD4-Proteina, OpenFold3, Boltz-2, Protenix, ESMFold2,
Mol-1) on an H100; Nebius Scientific AI for hosted antibody-specific models
(NanoBodyBuilder2, AntiFold, IgBert, StaB-ddG); JapanFold for RoseTTAFold3,
OpenDDE and AF2-IG; Amass for checking claims against primary sources.
