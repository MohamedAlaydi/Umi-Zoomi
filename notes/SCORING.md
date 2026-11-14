# What the scores mean

There is **no official weighted numerical score for our candidate table**.
The organisers allow each team to rank valid designs using its own internal
criteria. Our table preserves the team's proposed experimental order; it is
not sorted by global ipTM and does not compute a probability of winning.

Public names describe the method, not the person who ran it. `HER2-OPT-007`
is an enumerated optimisation candidate; `HER2-GEN-003` is a generator
comparator. Numbers identify candidates and do not change when ranks change.
The [mapping](CANDIDATE_IDS.csv) connects each label to its original query
and full VH/VL sequence checksum. Raw model evidence retains its original IDs.

## Computational evidence used by the team

| Value | Built from | Interpretation |
| --- | --- | --- |
| BLOSUM62 | Amino-acid substitution scores relative to the trastuzumab parent | A sequence-based heuristic; not measured affinity. It was compared with historical SPR outcomes. |
| Four contacts / 6 | Number of six Foundry predictions in which all four specified loop positions contact HER2, using a 4.5 Å heavy-atom cutoff | Persistence of the proposed contact pattern across seeds. The six predictions share a model and template. |
| HER2 footprint overlap | Predicted HER2 contact-residue set compared with the crystallographic reference; Jaccard penalises missing and extra contacts | A structural hypothesis about epitope overlap. It does not replace the competition assay. |
| Global ipTM | `interface_predicted_tm_score` from a raw model score JSON | Confidence in relative chain placement, on a 0–1 scale. The Fab complex also contains a VH–VL interface, so this is not an antibody–HER2-only affinity score. |
| Complex pLDDT | `average_predicted_local_distance_difference_test` from the same JSON | Average local structural confidence for the whole complex. It is distinct from binder-only pLDDT and from thermal stability. |
| `p_high` | Classifier prediction learned from the supplied FACS classes | A model estimate of a source-assay class. It is not a measured SPR KD or a validated probability that the new design improves on trastuzumab. |
| Local novelty distance and identity | Recorded local sequence comparison against the provided reference set | Triage for eligibility; the organiser's type-aware validator and final acceptance remain separate. |
| Binding-ddG | A model's predicted change in binding free energy, with its reported Monte Carlo error | A binding prediction, not folding stability or Tm. Controls and prediction error matter. |

The first four experimental slots express the team's hypotheses: a
sequence/contact lead, a matched contact-preserving versus contact-losing
pair, and a free-generation comparator. Sequence diversity and eligibility
also constrain selection. Neither `p_high` nor global ipTM alone defines
the order. The [rationale](../review/pitch_her2/Rangering_begrunnet.md)
explains the design choices; the [ranked export](RANKED_CANDIDATES.csv)
records the actual preserved order.

## What the organisers actually specified

The supplied task description gives these instructions:

- **Page 6:** the HER2 `pass` column remains empty; use `min_ipae`, `iptm`
  and `binder_plddt` for structural ranking. Lower interface error and higher
  structural confidence are useful model checks. Our summary explicitly
  labels its pLDDT as **complex** pLDDT rather than calling it binder pLDDT.
- **Page 7:** designs must pass the hard filters, then teams choose their own
  internal ranking criteria. Submit a ranked list of up to 20 designs.
- **Page 7:** Aggrescan 3D, SoluProt, NetSolP and ProteinMPNN with soluble
  weights are suggestions for expression/developability screening. Listing
  these suggestions does not mean this team has run those tools.
- **Pages 1 and 8–9:** final experimental evaluation compares HER2 binding by
  SPR, epitope preservation by competition with trastuzumab, and direct
  thermostability measurements with the measured trastuzumab reference.
  The S/A/B tiers reflect the number of properties improved/preserved as
  defined by the organisers, not a sum of our computational scores.

Source: [supplied task description](../review/organizer/ai-antibodies-hackathon-apheris.pdf).
The current table reports computational evidence and historical calibration;
new candidate SPR, competition and Tm results are not available in this snapshot.

Pitch judging is a separate decision: scientific judgment 40%, execution
20%, user fit 20% and path to value 20%. The published submission requirement
is a presentation and a GitHub repository link. We found no requirement
that a file must be named `SCORES.md`; that is this team's way of presenting
its traceable evidence. [Official event FAQ](https://oslo-ai-antibodies-hackathon.vercel.app/#faq)
