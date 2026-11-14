# Who does what

Five of us, one GPU, and a 16:00 freeze. Claim a role in the channel.

## Why it is split this way

We are not split into "the IT half" and "the biology half". Two reasons.

The pitch is scored **Judgment 40 %, Execution 20 %, User fit 20 %, Path
to value 20 %**. Execution is the pipeline. Judgment is the biological
reasoning behind the molecules we picked. Putting four people on the 20 %
and one person on the 40 % is backwards.

And there is **one H100**. Only one person can generate designs at a time.
So the other four roles are all deliberately GPU-free and run in parallel.

Our biologist is not a separate team. They rotate across all four roles
and own every call about whether a design makes biological sense.

## The roles

### 1. Generation
**Owns the GPU. Nobody else holds it.**

Design batches with RFD4-Proteina: sweeps over checkpoint, replicate count,
recycle strategy and seed. Every run goes through `newrun` and `gpurun`,
and every run's `NOTE.md` gets filled in while the job is running.

First action: a real optimisation batch, `her2-novel-2026-11-09`, far more
than the 4 replicates the baseline used.

Done when: a candidate pool big enough that filtering hard still leaves 20.

### 2. Ranking
**The thing that actually wins. No GPU.**

We are scored on three properties, so one score column cannot rank us.
Build the three-column table:

- binding: `min_ipae`, `iptm`, `binder_plddt`, plus whatever independent
  signals land from role 3 and JapanFold
- epitope preserved: verify per design, do not assume it
- thermostability: ThermoMPNN, Nebius `stab-ddg`

Rank by how many axes a design is predicted to improve, then by confidence
within that. A design predicted to improve all three outranks a design
with a brilliant `min_ipae` and nothing else, because that is literally
the scoring rule.

Also owns the **developability gate**: Aggrescan 3D, SoluProt, NetSolP,
ProteinMPNN soluble weights. Adaptyv's own write-up says expression
improved once teams scored with these. A design that will not express
reads zero on all three properties, so this is a gate, not a tiebreak.

First action: decide and write down what the ranking is, before there is
anything to rank.

### 3. Data
**Pure CPU, zero contention, start now.**

`~/team14/data/her2-trastuzumab` has 524,346 CDRH3 variants with FACS
binding classes and 768 with real SPR numbers. Train/val/test splits are
already made in `zenodo-10831512-trastuzumab-ngs`.

Train a classifier on measured binding. This is the **only signal we have
that touches reality instead of a model's opinion of itself**. Everything
else we have is a confidence score, and confidence is not affinity.

Feed the result to role 2 as an independent column.

First action: load the splits, get a baseline accuracy, see whether the
model separates the three FACS classes at all.

### 4. Pitch and evidence
**Starts now, not at 17:00. The highest-leverage seat.**

Winning the pitch takes us from 4 designs tested to 16. That is a 4x
multiplier on whether any of our work reaches a lab.

Owns: `notes/DECISIONS.md`, `notes/SCORES.md`, the repo README, the slides,
and Amass for checking claims against primary sources (what is known about
the trastuzumab epitope, what has been tried on thermostability).

The pitch has to answer four things: why these molecules, how the pipeline
reproduces, who the design is for, and a credible route to real use.

First action: start the decisions log properly and claim the Amass credits.

### 5. Biology
**Rotates. Reviews continuously, not at the end.**

Sits with generation when choosing what to sample, with ranking when
deciding what the numbers mean, with the pitch when it gets written.

Two concrete deliverables, not "the biology approach":

1. **Which HER2 contacts must survive.** Name the residues. Role 2 turns
   that into an automatic check on every refolded complex.
2. **Which mutations are plausible** without wrecking the fold, and which
   buy thermostability cheaply. Thermostability is a whole scored axis
   that most teams will forget, and it is the cheapest route to S-tier.

## How we stay together

**Sync every 30 minutes. Three minutes, standing, one sentence each.**
Two groups drifting apart for five hours is what actually sinks hackathon
projects, and this is cheap insurance against it.

Anyone can `tmux attach` to anyone else's session. Use it. Pairing on the
thing in front of you beats five solo tracks.

## The clock

| By | What |
| --- | --- |
| 11:30 | Roles claimed. First real design batch running. |
| 13:00 | Ranking written down. Developability gate working. |
| 15:00 | Pool big enough to filter hard. Biology review of the shortlist. |
| 16:00 | **Freeze.** Ranked 20 picked and novelty-checked. Repo clean. |
| 17:00 | Pitch rehearsed. Score tables done. |
| 18:00 | Submit. |

Do not design after 16:00. The pitch is worth more than one more batch.

## Already done, do not redo

- The environment: `env.sh`, `gpurun`, `newrun`, the venv, Claude Code
  with per-person logins. Run `team14-help`.
- 14 GB of hackathon data synced to `~/team14/data`.
- Run 001: the organisers' pipeline verified end to end, with numbers.
- `novelty check <CDRH3>`: our stand-in for `abguard`, which is missing
  from the VM. 525,063 sequences, matching the organisers' count exactly.
- Run 003: a JapanFold OpenDDE job that adds an independent model **and a
  wild-type trastuzumab control**, written and ready to submit.

## Still open

- Amass credits need claiming.
- `abguard` and `immunum` are missing from our VM although the task PDF
  says they are installed. Worth asking the Apheris team on site.
- `foundry-toolkit weight list` / `skill list` / `workflow list` are empty
  with the robot credential, so a browser `foundry-toolkit login` may be
  needed for the agent skills and Nextflow workflows.
