# Arbeidsinstruks: JapanFold-kontroll for Team 14

Gjennomgått direkte på VM-en 14. november 2026 kl. 13:30 Europe/Oslo. Repo: `/home/hackathon/team14`, commit `699ec49`, med flere aktive og ikke-committede endringer. Status er et øyeblikksbilde.

## Beslutning

Det er riktig tidspunkt for en liten OpenDDE-pilot. Dere har allerede design, refolds og en verifisert trastuzumab-referanse. Det er for tidlig å sende alle kandidatene eller hevde at et nytt modellresultat dokumenterer bedre binding. Hovedhindringen er hvordan HER2 representeres i input.

## Det som faktisk finnes

- Run 006: 44 strukturelt skårede konstrukt, inkludert 40 enumererte kandidater, WT og tre tidligere design som kontroller. Audit og lokale filtre oppgir at alle 40 klarer den strenge lokale nyhetsmarginen. Dette er ikke offisiell abguard-godkjenning.
- I `people/anas/refold-006.csv` er WT `iface_min=0.901`, `anas_027=0.915`, `anas_001=0.9145` og den frie loop-kontrollen `r004_cdrh3_3=0.933`. Dette er strukturskårer fra én seed, ikke affiniteter.
- Run 009: flere seeds og historiske SPR-kontroller er under arbeid. Den lagrede rapporten var ufullstendig: de foreslåtte kandidatene over hadde én seed, geometrifelter manglet og kalibreringstabellen hadde ingen ferdige skårer. Ikke bruk foreløpige robusthetsetiketter som en endelig dom.
- Run 010: 16 nye/omfoldede loop-varianter med avstand 2 til gitt datasett. Oppgavedokumentene er uenige om grensen. Hold dem utenfor hovedpanelet til arrangørene har avklart eligibility.
- Run 003: eksisterende OpenDDE-request og submit-script, men ingen lokale job-ID-er eller resultater ved inspeksjonen. Dette utelukker ikke at noen har kjørt noe fra en annen mappe eller konto; sjekk før ny innsending.
- Filen `/home/hackathon/.japanfold.env` finnes. Nøkkelverdien ble ikke lest eller vist i denne gjennomgangen; autentisering og saldo må kontrolleres av den som kjører.

## Til kameraten som tar oppgaven

1. Ta ansvar for JapanFold-sammenligningen i egen Opus 5-økt på VM-en. Gå til `/home/hackathon/team14` og lim inn hele teksten i `japanfold-opus5-prompt.md`.
2. Bevar pågående Foundry-kjøringer. JapanFold er hosted og trenger ikke den delte H100-en.
3. Løs HER2-kjeden først: eksisterende C og D er to biter av samme antigen. Bruk en dokumentert sammenhengende antigenkonstrukt og lagre nummereringskart. Ikke lim fragmentene direkte sammen eller dropp en antistoffkjede.
4. Kjør WT først. Når modellen gir en tolkbar referansepose, kjør et lite panel med tre eksisterende design og to kvantifiserte SPR-kontroller. Maks seks konstrukt og to seeds, altså tolv prediksjoner totalt. Det er en avgrenset pilot, ikke et stort søk.
5. Lever tabell med kjedeparskårer, HER2-kontakter og sammenligning mot WT, pluss råfiler og job-ID-er. Skriv tydelig hvis kontroller ikke gjenskapes eller forskjellene er usikre.

Opus-prompten er en oppgave dere kan gi i neste økt. Ingen JapanFold-jobber ble startet, ingen molekyler ble endret, og ingen repo-filer ble endret som del av denne gjennomgangen.

## Hvorfor OpenDDE og ikke AF2-IG her

Dere bruker et par av VH/VL-kjeder. JapanFolds `opendde-abag` er dokumentert for tung og lett antistoffkjede sammen med antigen. AF2-IGs dokumenterte input beskriver én binderkjede og én targetkjede. Å kaste bort VL eller konstruere et nytt scFv for å passe grensesnittet ville endre spørsmålet. Se [modelloversikten](https://japanfold.aiand.com/docs/models-and-limits/) og [prediksjonsgrensesnittet](https://japanfold.aiand.com/docs/predictions/).

OpenDDE kan gi ekstra strukturell støtte og synliggjøre uenighet med Boltz-2. Det dokumenterer ikke forbedret HER2-affinitet, bevart konkurrerende binding eller høyere termostabilitet. De tre endepunktene krever sine respektive målinger.
