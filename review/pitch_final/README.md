# Umi Zoomi: HER2 antibody redesign

Run `node serve.mjs` and open http://localhost:8791/deck.html . On Windows, use `start-deck.cmd` with Node installed. Keep the folder together; fonts, sound and 3D libraries are local.

The presentation keeps the supplied visual style and follows the whole design-and-evaluation project. The live deck has 11 stops with 23 forward presses after the holding screen. The PDF has 14 pages, including separate views of all four variants.

- PDF page 12 compares the four designs: screening-model score, two conditional affinity estimates and interface PAE.
- PDF page 13 shows primary affinity-model predictions against 180 historical measured SPR constructs, with groups held out.
- `SPEAKER-SCRIPT.md` contains an expanded spoken script and detailed preparation notes, including units and limitations.
- `FOUR_DESIGN_COMPARISON.csv` and `RESULTS_AND_SOURCES.json` contain the numerical sources.
- `TOP4_INNSENDING.csv` is unchanged; it keeps the validated six-column submission format.

The candidate table contains predictions, not new laboratory measurements. Framework effects are unmodelled by the H3 assay predictors. The validation plot uses historical experimental measurements. No improved therapy, affinity or thermal stability has been demonstrated for the new variants.

The complete second-model comparison remains in the MODEL_CONTROL files. Source datasets and further campaign evidence are documented in the project repository.
