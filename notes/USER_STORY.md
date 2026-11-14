# User story — who this is for

Extends the user-fit material already in `PITCH_CONCEPT.md` (scorecard row),
`review/pitch_her2/MANUS_OG_JURY.md` (Brukerbehov 20 %, slides 4–5) and
`review/four_slots/TEAMBRIEF.md`. Same person, same angle, stated once in full.

## The person

The assay lead. Not a clinician, not a patient, not a pharma executive — the
person who decides which constructs get expressed this week, under a capacity
they do not control.

They have more plausible designs than slots. That is their permanent condition.
The designs in front of them are not obviously different from one another, and
nothing in a model's output tells them which four are worth the bench time.

## The moment

Four slots. Forty candidates that survived every filter. A shortlist so close
together that the scores cannot separate it — our own interface-confidence
numbers span 0.890–0.954 across the forty, with the parent molecule sitting
mid-pack at 0.946, and seed-to-seed noise of 0.0147. Ranking by score here is
ranking by noise.

So the real risk is not picking the wrong four. It is picking four that are all
the same bet, getting one ambiguous readout, and having spent the capacity
without learning anything.

> As the assay lead, I need four constructs that each answer a different
> question, with a traceable reason per slot — so that whatever the assay
> returns, the result is informative rather than merely disappointing.

## What we hand them

A ranked list where every slot carries its reason, and every number has a file
path behind it.

- **A designed experiment, not a leaderboard.** The top four are chosen to
  disagree with each other, so the four readouts partition the hypothesis space
  instead of repeating one bet.
- **Receipts, not assertions.** Each design is run through abguard; the novelty
  gate is satisfied at CDRH3 distance 3 against a required 3, 20 of 20; contact
  conservation and footprint overlap are measured against the crystal structure
  rather than assumed from sequence.
- **The liability ledger, including the bad news.** Every design removes the two
  liabilities we targeted, both of which sit at positions that make no contact
  with HER2 — so fixing them costs nothing at the interface. But eleven of the
  twenty introduce a different liability, and for eight of those an oxidation
  liability changed class rather than disappearing, ranks 1 and 2 among them.
  abguard reports this and the ranking accounts for it. An assay lead who is
  told only the good half cannot plan around the other half.
- **A statement of what each candidate is for.** Full sequence, chain check,
  per-model result, known weak point, and the question that construct answers.

## What we deliberately do not claim

This is the part that makes the list usable.

- **Not improved binding.** Our own measured-data classifier ranks the parent
  molecule above every design (0.930), and a plain substitution matrix beats
  that classifier on held-out SPR data (0.847 vs 0.751). The designs sit inside
  the noise floor. We say so.
- **Not improved thermostability.** No installed tool measures it. Chemical
  degradation is not melting temperature, and we do not let one stand in for
  the other.
- **Not "beats the parent molecule."** The parent's own eight SPR replicates
  span 6.2× — 0.0285 to 0.178 nM. "Beats baseline" is undefined until you say
  which replicate you mean, and we would rather define it than win on it.

Epitope preservation remains a hypothesis: contact conservation and footprint
overlap are measured, but across seeds that share a model and a template.

## Why the honesty is the feature

An assay lead cannot act on an overstated claim. They can act on a falsifiable
one. Every slot in our four is paired with a prediction specific enough to be
wrong, which means the assay can return bad news and the week still produced
knowledge.

That is the user fit: we are not selling a better molecule. We are handing the
person with four slots a defensible reason for each of them.

## Open before the pitch

Which file the pitch names as the deliverable is currently inconsistent:
`README.md` (15:11) says 20 optimisation designs; `review/panel18plus2/`
(14:44) says 18+2 with a different top four; `review/regelkontroll-premie/`
(14:59) recommends a prize-track file; `PUBLICATION.md` demotes the 18+2 work
to work-in-progress. The user story above assumes the README's 20. One line
needs to settle it.
