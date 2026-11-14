# HER2 de novo: gjennomført kampanje og beslutning

Oppdatert 2026-11-14T14:29:15.258542+00:00. Implementert i teamprosjektets `review/denovo/` og `runs/011-codex-denovo-vhh/`.

**Vi har gjennomført en større designkampanje, men har ikke dokumentert en ny HER2-binder.** Tre VHH-er består den installerte abguard-byggets de novo-regler og vår ekstra sekvensscreening. Uavhengige strukturmodeller gir fortsatt svak støtte til de ønskede bindingsposene. Behold den eksisterende Fab-optimaliseringsserien som hovedcase og presenter VHH-ene som eksperimentelle reserver.

## Hva som faktisk er gjort

- 80 genererte komplekser: 16 BoltzGen og 64 lokale RFD4-antistoffdesign, fordelt på to hosted og fire lokale armer. I tillegg 16 AntiFold-varianter med uendret nytt rammeverk: **96 nye designsekvenser**.
- 15 eksplisitte Cys-varianter var diagnostikk, og 20 eksisterende Fab-par var kontroller. Disse telles ikke som 35 ekstra de novo-funn.
- **131 innsendte sekvenser til lokal abguard; 127 består**, inkludert alle 20 gamle Fab-par. Ingen duplikate ID-er eller konstruksjoner. Referanseindeksen inneholder 610109 CDRH3-er.
- 48 kompleksprediksjoner er ferdige: 16 prediksjoner av fire original/Cys-par gjennom to modeller, 27 blinde cofolds og 5 designbetingede AF2-IG-sjekker. NanoBodyBuilder2 ga 5 modeller per VHH, totalt 15 modeller for 3 sekvenser.
- En eksisterende fullført teamkjøring med 30 SPR-konstruksjoner og 3 Boltz2-seeds per konstruksjon ble analysert på nytt. Dette er 90 modeller, men **25 kvantifiserte eksperimentelle KD-er**, ikke 90 uavhengige målinger.
- 20 datakontroller og 8 nye regresjonstester består. Den tidligere optimaliseringsanalysen ble også reprodusert med 7 tester og 193 verifiserte originale inputfiler.

## Kandidatene

| Kandidat | Lengde | Min. CDRH3-avstand | Høyeste identitet i referanseutvalget | NBB2 CA-RMSD | CDRH3-RMSD etter rammeverkstilpasning |
|---|---:|---:|---:|---:|---:|
| novel2 (12) | 124 | 10 | 68.5% | 1.14 Å | 2.41 Å |
| novel1 (13) | 130 | 13 | 68.7% | 2.79 Å | 6.81 Å |
| novel3 (2) | 134 | 16 | 67.4% | 5.79 Å | 15.02 Å |

RMSD beskriver samsvar med designet, ikke målt funksjon. Alle tre har to kanoniske cysteiner og ingen atompar under 2 Å mellom designet antistoff og antigen. Den beste monomer-folden er novel2 (original design 12). Den har et mulig N-glykosyleringsmotiv NVS i CDRH3. De to andre har blant annet isomeriserings-/deamideringsmotiver. Motiver er risikoflagg, ikke målte feil eller automatisk avvisning.

## Det viktigste kvalitetsfunnet

Mol-1 gjenfinner 18/19 av WT-epitopens kontaktrester med global ipTM 0.953. De nye VHH-ene har Mol-1 ipTM 0.124–0.190 på crop119 og svak/varierende epitopeoverlapp. AF2-IG gir ipTM 0.108–0.121 og interfacePAE rundt 26 Å for de tre selv når designposen oppgis. Dette er utilstrekkelig støtte til å kalle dem vellykkede bindere. OpenFold3 gjenfinner bare 2/19 WT-rester, som også viser hvorfor vi må kontrollere hver modell før negative prediksjoner tolkes. Fab- og VHH-globalipTM er ikke direkte kalibrert mot hverandre.

Alle 16 AntiFold-varianter har bedre strukturkondisjonert CDR-likelihood (NLL 0.707–0.769 mot 2.523 for originalen), men blir 70.9–73.1% identiske med minst ett kjent antistoff i samme utvidede referanseutvalg. Alle 16 består installert abguard som de_novo. Vi holder dem likevel tilbake på grunn av oppgavens strengere identitetskrav. Optimalisering av modellscore er derfor ikke nok.

## Hva abguard faktisk bekrefter

Den installerte 0.1.0-byggen identifiseres med kilde- og referansehasher, fordi det har eksistert ulike bygg med samme versjonsnummer. Dens track-klassifisering bruker identitet til trastuzumab. Oppgave-PDF-en beskriver derimot identitet til nærmeste kjente antistoff. Vi bevarer begge vurderingene.

`novelty-report` i dette bygget hopper over referansedatabasen via standardargumentet `skipped=True`; ukjent novelty-verdi må ikke telles som bestått. `team-validate` bruker referansen korrekt. En egen adapter bruker de offentlige Python-funksjonene med eksplisitt referanse uten å endre arrangørens validator. Adapteren og `team-validate` returnerer nøyaktig samme 127 aksepterte ID-er. Den feilaktige CLI-rapporten er bevart som revisjonsspor.

De tre opprinnelige VHH-ene har 0 RCSB-treff med 70%-grense og under 70% global aligneringsidentitet til de faktiske antistoffreferansene vi hentet. RCSB og dette utvalget dekker ikke alle kjente antistoffer. Dette er ikke et universelt novelty-bevis eller endelig godkjenning fra arrangørene.

De to lokale HER2-tabellene er også undersøkt direkte: 524346 FACS-rader og768 SPR-rader gir nøyaktig525063 unike CDRH3-er. Alle FACS/trastuzumab-VH-er ble kontrollert mot de faste flankene; IMGT-løkken er SR + den oppgitte core-sekvensen + Y. De andre SPR-VH-ene ble nummerert direkte. Minste eksakte Levenshtein-avstand mot alle525063 normaliserte IMGT-løkker er11 for novel2,15 for novel1 og18 for novel3. Dette oppfyller provided-data-kravet uten å anta at abguard-bundlen inneholder samme tabeller.

## Forskningsbasert evaluering

Den nye CA-baserte NAC-tilpasningen bruker IMGT-rammeverksresiduer og predikert CA-pLDDT, inspirert av [Liang mfl., preprint, oktober 2026](https://arxiv.org/abs/2610.23136). På de 25 målte KD-ene er Spearman rho −0.464, bootstrap 95% KI [−0.710,−0.103]. Forskjellen mot ipTM er −0.101 med paret KI [−0.575,+0.423]. Vi har derfor ikke vist at metoden er bedre enn ipTM. Utvalget er lite, stratifisert og består av beslektede trastuzumab-varianter; overføring til nye VHH-er er ikke dokumentert. Vi har ikke implementert paperets RIC-metrikk eller brukt denne analysen til å velge en terskel etterpå.

[AntiFold](https://github.com/oxpig/AntiFold/tree/9918344067f34a6b026f2634fdba212fc3e6e986) ble valgt for antistoffspesifikk CDR-inversfolding, [OpenDDE](https://arxiv.org/abs/2607.03787) for et ekstra antistoff–antigen-checkpoint, og [JapanFold AF2-IG](https://japanfold.aiand.com/docs/predictions/) for en separat designbetinget posesjekk. AMASS ble brukt til fem avgrensede litteratursøk; den ferske NAC-preprinten ble lest fra primærkilden da den ikke ble funnet presist i indeksen.

## Hva vi kan si til juryen

«Vi bygget en sporbar HER2-designsløyfe som undersøker både funksjon, sekvensnyhet og modellfeil. Vi gjennomførte 96 sekvensdesign, la til uavhengige modeller og kjente kontroller, og testet evalueringsmetoden mot reelle historiske affinitetsmålinger. Vi fant tre novelty-screenede VHH-er, men oppdaget også at bedre modell-likelihood kan føre design tilbake mot kjente antistoffer. Derfor skiller plattformen eksplisitt mellom validatorbestått, modellstøttet og eksperimentelt bekreftet. Den eksisterende datastøttede Fab-optimaliseringen er vår hovedcase.»

Den eksisterende analysen på 584 historiske FACS-usette konstruksjoner ga BLOSUM-AUROC 0.847 mot FACS-modell 0.751 for rapporterbar SPR-tilpasning. Nærmeste-FACS-positive-baseline var omtrent 0.850. BLOSUM er dermed ikke vist bedre enn alle enkle baselines. Historisk utvalgsbias og skillet mellom SPR-fit og sterk binding begrenser overføringen. Se teamets eksisterende pitch og rangering for de konkrete Fab-kandidatene.

## Hva som gjenstår

1. Endelig arrangørvurdering av nearest-known-identitet og korrekt track.
2. Ekspresjon/renhet, monomerstatus og kvantitativ SPR med samtidige WT-kontroller og konsentrasjonsserie.
3. Trastuzumab-konkurranse eller direkte epitopekartlegging.
4. Direkte termisk måling mot WT. pLDDT, disulfidavstand og binding-ddG er ikke Tm.
5. En ny målrettet designrunde som beholder nyheten samtidig som CDR-konformasjon og docking blir mer robuste. Vi har gjennomført denne kampanjens beregninger; laboratorieresultatene er ennå ikke produsert.

## Ressurser og kostnad

JapanFold har fakturert **$0.415739** for de ni konkrete jobb-ID-ene i denne kampanjen, inklusive et mislykket AF2-inputforsøk som kostet $0. Det ble rettet ved å legge til et påkrevd CIF-felt, uten å endre koordinater; korrigert kjøring fullførte 5/5. AMASS-søk brukte 25 kreditter, tilsvarende $0.25 etter tjenestens kredittpris. Nebius returnerte ingen per-jobb dollarpris; lokal H100 er ikke separat priset. Tallene er ikke en samlet infrastrukturkostnad.

## Filer og reproduksjon

- `report.html`: offline rapport, figur og roterbar CA-strukturvisning.
- `campaign-evidence.png` / `.pdf`: figur til presentasjonen.
- `exploratory-candidates.csv`: tre reserver med sekvens, hasher og bevisstatus; dette erstatter ikke den rangerte innsendingsfilen.
- `evidence.json`, `receipts/` og `source/`: resultater, kildekode, kvitteringer og kvalitetsspor.
- `structures/`: utvalgte design-, refold- og monomerstrukturer. Fullt originalarkiv ligger i teamprosjektets run011.

Rapporten kan bygges igjen med `PYTHONPATH=review/denovo/.venv/lib/python3.12/site-packages .venv/bin/python review/denovo/build_report.py --output <mappe>`. Revisjonen kjøres med samme Pythonmiljø og `review/denovo/verify_campaign.py`. Dette krever teamprosjektets eksisterende data og miljø. Pakken er ikke et selvstendig modell-/vektarkiv. Ingen API-jobber sendes på nytt av rapportbyggeren eller revisjonen.
