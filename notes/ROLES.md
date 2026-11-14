# Who does what

Three jobs. The pipeline is already built and working, so nobody has to
build anything. We run it a lot, pick the best, and explain why.

Claim a job in the channel by number.

---

## Job 1 — Run designs

You own the GPU. Nobody else starts a GPU job.

```
design yourname 40
```

That is the whole thing. It generates 40 designs, refolds the best 10,
scores them, and checks novelty. It runs in the background, so you can
close your laptop.

```
results yourname
```

Shows the table when it is done, or tells you it is still going.

Do it again with different settings and see what changes:

```
design yourname 40 her2
design yourname 40 antibody
```

- `her2-novel` (the default) gives the most new loops and the best fit
- `her2` sticks closer to known binders, so more get rejected as not novel
- `antibody` is the only one that can change CDRs other than H3

One run at a time. Check with `gpu` first. Start the big ones early.

---

## Job 2 — Pick the best

No GPU. You read the tables from job 1 and build the shortlist.

The rule, in order:

1. **Throw out anything the novelty check calls REJECTED.** It would never
   reach the lab.
2. **Then throw out anything with distance under 3, or over 60 % identical
   to trastuzumab.** The official limits are 2 and 70 %, so this keeps a
   margin. A design on the line is a coin flip.
3. **Sort what is left by `min_ipae`, lowest first.** Then prefer higher
   `iptm` and higher `binder_plddt`.
4. **Keep variety.** Ten near-identical CDRH3s is one bet, not ten. If two
   designs differ by one residue, keep the better one.

Put the survivors in `notes/SCORES.md` as you go, with which run they came
from. That table is something we have to hand in.

If you have spare time, the one extra thing worth doing is
**thermostability**, because it is a whole scored property most teams will
ignore. Ask in the channel before starting it, it is a bigger job.

---

## Job 3 — Tell the story

No GPU, starts now, not at 17:00.

This is the biggest job on the team even though it has no code in it.
**Winning the pitch takes us from 4 designs tested to 16.** The pitch is
scored Judgment 40 %, Execution 20 %, User fit 20 %, Path to value 20 %.
Judgment is just "why did you pick these molecules", which is a writing
job, not a science job.

You own:

- `notes/DECISIONS.md` — one line every time we decide something, and why.
  Write it when it happens. Nobody can reconstruct it at 17:00.
- The slides.
- Amass, for checking claims against real papers.

Four questions the pitch has to answer: why these molecules, how someone
else could reproduce the pipeline, who the design is for, and a realistic
route to it being used.

---

## Our biology person

Not a separate team. You sit with whoever is working and answer the
questions none of us can:

1. **Which HER2 residues must the design still touch?** Name them. That
   becomes a yes/no check on every design.
2. **Do these CDRH3 sequences look sane?** Job 2 will show you ten
   ten-letter sequences. Which would you not put in a tube, and why?
3. **Which changes buy stability?** Thermostability is one of the three
   things we are scored on and the one everyone forgets.

Answers go straight into `notes/DECISIONS.md`. Those sentences are worth
more marks than anything the rest of us type.

---

## The five commands

```
team14-help          what everything does
gpu                  is the GPU free
design yourname 40   run the pipeline
results yourname     see the table
novelty check SEQ    would this design be rejected
```

## The clock

| By | What |
| --- | --- |
| 11:30 | Jobs claimed, first big run going |
| 13:00 | Enough designs to start picking |
| 15:00 | Biology review of the shortlist |
| 16:00 | **Stop designing.** Pick the final 20. |
| 17:00 | Pitch ready |
| 18:00 | Submit |

Nothing new after 16:00. The pitch is worth more than one more run.

## Sync every 30 minutes

Three minutes, standing up, one sentence each. That is the only process
we have and it is the one that stops us drifting apart.

## Already done, do not redo

The environment, the data, the novelty checker, and run 001 which proves
the pipeline works end to end. Run `team14-help` and look at
`results 001`.
