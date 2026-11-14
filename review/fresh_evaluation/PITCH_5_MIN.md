# Short judge-facing pitch

About 3–3½ minutes, leaving room for a visual and pauses within a five-minute slot. Read the script below; keep the judging checklist for preparation.

## Script

Our question was simple: which antibody designs actually deserve a laboratory test?

We focused on HER2-positive breast cancer. HER2 is a protein on the surface of cancer cells, and trastuzumab is an established antibody that targets it. Our goal is to explore new designs that keep recognising the right target while becoming more stable.

Our users are antibody discovery teams. They can generate many possible molecules, but laboratory testing is limited. They need a clear reason to choose one design over another.

We built a workflow that learns from the organisers’ experimental data, proposes new sequences, and checks whether their predicted structures still reach the relevant binding site. The code, settings and validation records are available in our GitHub repository.

The most important part was checking whether we could trust the predictions.

One model struggled even with the original antibody. We therefore stopped using its negative predictions to reject our designs. Another scoring method performed too uncertainly on measured examples, so we removed it from the ranking.

Those checks changed which molecules we chose.

Our four priorities test clear biological ideas. The first explores our strongest new binding hypothesis. The second uses the same binding region with a published framework change intended to improve stability. Comparing that pair lets us test what the framework change contributes.

The third balances different signals from the experimental data. The fourth tests another sequence family with the stability hypothesis, so our choices cover more than one idea.

All four pass the local submission checks. Their performance still needs to be measured: the published stability result may not transfer to our new designs.

Next, Adaptyv can test whether they bind HER2, compete for the intended binding site, and remain stable when heated, alongside the original antibody. That will tell us whether our designs improve the properties the challenge rewards.

For a breast cancer programme, successful designs would then need cell testing, specificity checks and development in an appropriate therapeutic format.

The immediate value is a better-supported choice of experiments. We have built a working route from experimental data to new molecules, with clear reasons for our choices and clear tests of what comes next.

## Judging checklist — do not read aloud

| Criterion | Where the script addresses it |
|---|---|
| Judgment — 40% | Controls changed the ranking; each of the four candidates tests an explained hypothesis. |
| Execution — 20% | Working workflow, new sequences, local validation, code/settings/records in GitHub. |
| User fit — 20% | Antibody discovery teams deciding how to spend limited laboratory capacity; HER2-positive breast cancer is the intended application. |
| Path to value — 20% | Challenge assays first, then cell testing, specificity and therapeutic-format development. Immediate value is experiment selection. |

Use one visual: **experimental data → new designs → checks → four laboratory priorities**. Keep model names, performance statistics and sequence IDs for questions. Describe this as preclinical discovery work; improved treatment has not been demonstrated.
