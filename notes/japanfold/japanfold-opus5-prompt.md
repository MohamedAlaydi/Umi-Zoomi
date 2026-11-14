Du arbeider på Team 14s hackathon-VM i `/home/hackathon/team14`.

Oppgaven er å kjøre en liten, reproduserbar JapanFold/OpenDDE-kontroll av EKSISTERENDE trastuzumab–HER2-kandidater. Ikke generer eller muter nye kandidater. Bevar andres arbeid og pågående kjøringer. Bruk hosted JapanFold; ingen lokal GPU-jobb er nødvendig.

Les eventuelle gjeldende AGENTS.md. Les deretter:

- `CURRENT_PIPELINE_AUDIT.md` som bakgrunn, og kontroller påstandene mot faktiske filer.
- `runs/003-mohamed-japanfold-abag-control/{NOTE.md,build_request.py,request.json,submit.sh}`.
- `people/anas/refold-006.csv` og `runs/006-anas-enumerated-top40/out/prepared/holo/queries.json`.
- De nyeste manifestene og resultatene under `runs/009-claude-multiseed-refold/`.
- `runs/010-claude-passers-007-005/NOTE.md` og `scripts/novelty.py`.

Status ved gjennomgang 14. november 2026 kl. 13:30 Europe/Oslo: run 003 har en request, men ingen lokale job-/resultatkvitteringer. Run 009 pågår og har ufullstendige seeds, manglende geometrifelter og ennå ingen skårede kalibreringspunkter i den lagrede rapporten. Run 010s 16 kandidater har alle avstand 2 til gitt datasett. Sjekk om status er endret. Etiketter som PASS_STRICT er interne modelleringsetiketter, ikke offisiell godkjenning.

Arbeid i en NY unik run-mappe med den eksisterende nummereringsrutinen, med eget scratch under `people/`. Ikke overskriv run 003, andre resultater, aktive scripts eller teamets handoff. Opprett NOTE.md med formål, eksakte inputkilder, hashes, modell og parametere før innsending.

1. Kontroller nåværende API-dokumentasjon og relevant modellskjema:
   https://japanfold.aiand.com/docs/predictions/
   https://japanfold.aiand.com/docs/models-and-limits/
   https://japanfold.aiand.com/docs/jobs/
   Bruk `opendde-abag`, ikke AF2-IG: våre antistoffer har VL og VH som separate kjeder. Ikke fjern VL eller lag et kunstig scFv for å passe et API. Last eksisterende nøkkel privat fra miljøet eller `/home/hackathon/.japanfold.env`, uten å vise verdien. Kontroller autentisering, kreditt og eksisterende jobber uten å skrive hemmeligheter til logger. Ikke kjøp nye kreditter.

2. Løs antigenrepresentasjonen FØR en prediksjon. I eksisterende Foundry-input er A=VL (107 aa), B=VH (120 aa), C=HER2 489–580 og D=HER2 591–607. C og D er fragmenter av ETT protein med et uløst mellomrom, ikke to biologisk separate proteiner. Ikke send den gamle firekjeders requesten ukritisk. Foretrekk én sammenhengende HER2-kjede fra det eksperimentelle 1N8Z-antigenets polymersekvens, inkludert dokumenterte rester uten koordinater. Bruk lokalt rå-mmCIF i `/home/hackathon/trastuzumab_epitope/raw_1N8Z/` eller en autoritativ 1N8Z/UniProt-kilde. Verifiser sekvensjusteringen mot begge eksisterende fragmentene, riktig konstrukt og nummereringsforskyvninger; lagre en residue-map mellom inputposisjon og referansens HER2-ID. Ikke finn på rester eller skjøt C og D direkte sammen. Bruk samme antigen i HELE JapanFold-panelet. Hvis en biologisk sammenhengende representasjon ikke kan verifiseres, lever ferdig preflight og en presis blokkering; ikke send feilrepresenterte input.

3. Frys et panel på MAKS seks konstrukt:
   - `trastuzumab_wt` fra run 006 som referanse.
   - `anas_027` og `anas_001` fra run 006 som kandidater fra den enumererte gruppen.
   - `r004_cdrh3_3` fra run 006 som sammenligning med fri loop-generering.
   - Én historisk sterk og én historisk svakere binder med KVANTIFISERT SPR-KD, valgt etter måling, ikke modellskår. Bruk run 009s `manifest_calibration.csv` og den originale SPR-tabellen. Kontroller begge fulle antistoffkjedene og konstruktbakgrunnen. `no_reportable_kd` er ikke en bekreftet ikke-binder.
   Dedupliser på fulle VH/VL-sekvenser. Hent antistoffsekvensene maskinelt fra verifiserte kilder. Lagre sekvenshash, kilde, CDRH3 etter arrangørens 10-resters konvensjon og lokal eligibility-status. Sjekk kandidatene med lokal margin avstand >=3, identitet <=60 %, og cysteinkontroll. Historiske kontroller og WT er kontroller, ikke innsendinger. Hvis en foreslått kandidat ikke passerer marginen, utelat den og dokumenter hvorfor. Hold run 010s grensekandidater utenfor dette panelet inntil offisiell eligibility er avklart.

4. Kjør FØRST WT med to seeds, dersom gjeldende modell støtter dette. Bruk sekvenser uten epitopeføringer i hovedtesten; dette tester om plasseringen gjenskapes uten å oppgi svaret. Lagre alle parametere og MSA-innstillinger. Inspiser at begge antistoffkjedene er med, at antigenet er sammenhengende, og om komplekset gjenskaper det kjente bindingsområdet og en rimelig orientering etter HER2-superposisjon mot 1N8Z. Rapporter begge WT-resultater. Hvis WT ikke gjenskaper en tolkbar referansepose, stopp utvidelsen og forklar begrensningen. Ikke kast kandidater fordi modellen feiler på WT. En eventuell epitopeført oppfølging er et eget eksperiment og beviser ikke epitopebevaring.

5. Når WT-kontrollen fungerer, kjør resten av panelet med de samme to seeds og identiske innstillinger. Hele oppgaven omfatter MAKS tolv target/seed-prediksjoner inkludert WT, færre ved utelatte konstrukt. Ved manglende seed-støtte: rapporter det og bruk én prediksjon per konstrukt; identiske deterministiske gjentakelser er ikke uavhengige replikater. Registrer estimert kostnad før innsending og faktisk kostnad hvis API-et returnerer den. Lagre request-hash, idempotency-key og job-ID straks. Gjenoppta eksisterende jobb fremfor ny innsending; sjekk historikk ved tidsavbrudd, og ikke anta at en gammel idempotency-key forhindrer duplikater etter API-ets tidsvindu. Ikke last ned resultater fra feil jobb.

6. Last ned struktur, råskårer og PAE (`write_pae=true` hvis støttet). Verifiser outputsekvenser og kjede-ID-er før analyse. Lag en CSV med kandidat, seed, job-ID, antigenhash, VH/VL-hash, status og manglende felter. Rapporter VH–HER2 og VL–HER2 separat med kjedepar-ipTM hvis tilgjengelig, samt PAE over bindingsflaten, kontaktene til HER2 og overlapp med referanseepitopen. Hold VH–VL-interaksjonen utenfor antistoff–HER2-skåren. Beregn kontakter ved 4,5 Å mellom tunge atomer og gjør enkel følsomhetskontroll ved 4,0/5,0 Å. Bruk residue-map; ikke anta at gamle C/D-ID-er fortsatt gjelder. Ikke bruk de gamle firekjeders collectors uendret på et trekjeders input. Manglende skår er NA, ikke null.

7. Sammenlign kandidat mot WT INNEN OpenDDE ved samme seed. Sammenlign deretter relativ rangering og kontaktmønstre med Boltz-2. En endret antigenrepresentasjon og andre MSA-/templatevalg betyr at dette er en ekstra robusthetstest, ikke en kontrollert måling av hvilken modell som er best. Ikke trekk fra rå ipTM på tvers av modellene, og ikke estimer sikker forbedring fra bare to seeds. Undersøk om de to målte kontrollene overhodet skilles; dette lille panelet er en sanity check, ikke en validert affinitetsmodell.

Lever manifest.csv, request-filer, job-ledger, råresultater, sammenlignings-CSV og NOTE.md med beslutning per kandidat: støttet, uavklart eller svekket strukturell støtte. Gi eksakte kommandoer og filstier. Legg bare ikke-hemmelige, små sporbarhetsfiler i Git etter kontroll av faktiske ignore-regler; ikke commit andres endringer eller push. Strukturkonfidens dokumenterer ikke KD, konkurrerende binding eller Tm. Ikke kall noen kandidat bedre enn trastuzumab på affinitet eller termostabilitet uten de relevante målingene.
