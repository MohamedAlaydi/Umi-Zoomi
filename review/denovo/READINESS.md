# De novo HER2: hva som kreves, hva som er sjekket, og anbefalt løp

Status 14. november 2026, kontrollert omtrent kl. 13:45–14:00 Oslo-tid. Dette er en miljø- og evidensgjennomgang med klargjøring av målsekvens og lokal kvalitetskontroll. Ingen nye antistoffkandidater eller modellprediksjoner er laget i denne gjennomgangen.

## Beslutningen

Behold optimaliseringsløpet som hovedleveranse. Et separat VHH-pilotløp er den mest praktiske de novo-utvidelsen å undersøke, fordi det har én antistoffkjede og kan kjøres via JapanFold uten å vente på teamets opptatte H100. Dette er en teknisk prioritering, ikke dokumentasjon på at VHH vil gi bedre binding, termostabilitet eller konkurranseresultat enn Fab.

Den første beslutningen i piloten er **om designene faktisk kan kvalifisere som de novo**. Arrangørens kriterium er strengere enn mange artiklers bruk av ordet. Et nytt sett CDR-er på et kjent rammeverk kan fremdeles ha over 70 % identitet til et kjent antistoff. Både den lokale RFD4-antistoffoppskriften og BoltzGens publiserte VHH-eksempel bevarer rammeverk. Ingen av dem garanterer konkurransens de novo-status. [BoltzGen-eksempel](https://github.com/HannesStark/boltzgen/blob/main/example/nanobody/penguinpox.yaml) · [Eksempel på bevart rammeverk](https://github.com/HannesStark/boltzgen/blob/main/example/nanobody_scaffolds/7eow.yaml)

Å endre mange rammeverksrester kun for å komme under et identitetstall er ikke en god designstrategi: det må samtidig være et foldbart, funksjonelt antistoff. Track skal bestemmes av arrangørens typebevisste kontroll, ikke av modellnavnet eller av teamets egen etikett.

## Hackathonkrav

De vedlagte oppgave-PDF-ene beskriver to spor som evalueres separat. For de novo kreves under 70 % identitet til nærmeste kjente antistoff i referansebasen, ikke bare lav likhet med trastuzumab. Oppgaveteksten krever dessuten minst to CDRH3-endringer fra trastuzumab. Formatet skal være VHH, scFv eller paret Fab-variabelregion, total antistofflengde høyst 250 rester og ingen uparede cysteiner; nummereringskonfidens minst 0,1. Den offisielle validatoren er autoriteten.

Optimaliseringsreglene beskrives ulikt i dokumentene: oppgavens figur og siste filterliste sier avstand strengt over to og CDRH3-identitet under 70 %, mens lysbildene bruker minst to og høyst 70 %. Behold teamets interne margin til dette er avklart. Ikke bruk den lokale CDRH3-cachen som erstatning for full de novo-databasesøk.

Laboratoriet måler HER2-binding med SPR, konkurranse mot trastuzumab og termostabilitet. En predikert struktur dokumenterer ingen av disse tre alene. Eksisterende historisk WT-KD er en referanse; den samtidige kontrollmålingen hos Adaptyv bestemmer konkurransesammenligningen.

Pitchvektene er 40 % begrunnelse, 20 % gjennomføring, 20 % brukerbehov og 20 % vei til verdi. Oppgaveteksten ber om en rangert liste på inntil 20 design, med fire garanterte tester og flere etter pitch. Den offentlige planen oppgir pitchforberedelse 17:00 og innsendingsfrist 18:00 Oslo-tid, med forbehold om endringer. [Arrangørens nettside](https://oslo-ai-antibodies-hackathon.vercel.app/)

## Hva miljøet faktisk har

| Ressurs | Verifisert nå | Bruk i anbefalt løp |
|---|---|---|
| Lokal maskin | H100 80 GB, omtrent 338 GB ledig disk; GPU brukes av eksisterende Boltz-jobb | Bevar eksisterende jobb og GPU-lås. Bruk forhåndslastet RFD4 `antibody-2026-10-30` dersom et strukturbasert alternativ trengs. |
| Apheris | Antistoff-, HER2- og HER2-novel-images samt flere refoldere ligger lokalt; tidligere løp har komplette resultater | Antistoffmodellen kan redesigne flere CDR-er; HER2-modellene endrer CDRH3. Dette er ikke full de novo-statuskontroll. |
| JapanFold | Health, modellkontrakter, autentisert kredittsjekk og jobbliste svarte HTTP 200. Saldo 1 100 USD. Jobblisten var tom ved sjekken | BoltzGen `nanobody-anything` som pilotkilde; AF2-IG for kompatible VHH–mål-strukturer; separat uavhengig cofold av finalister. |
| Nebius | Autentisert NanoBodyBuilder2-schema svarte; korrekt kontrakt lagret | Antistoffspesifikk vurdering av VHH-fold. Et tilgjengelig schema beviser ikke at en ny jobb vil lykkes eller hvor lang køen er. |
| AMASS | Autentisert saldo og tre litteratursøk svarte HTTP 200; 60 treff returnert | Kildekontroll som endrer forsøksvalg, med søke- og kostnadslogg. Ikke en prediksjonstjeneste. |
| immunum | Installert som `2.1.0` i eget `review/denovo/.venv` | Lokal nummerering og sekvenskontroll; delt modellmiljø er ikke endret. |
| abguard / offisiell referansebase | Ikke funnet på sjekket PATH, blant relevante lokale filer eller i S3-inventaret på 81 objekter | Må hentes fra arrangørene eller erstattes av deres offisielle portal. Et bibliotek kalt immunum gir ikke denne databasen. |

Modellmetadata er øyeblikksbilder. JapanFold oppgir historisk BoltzGen-jobbkost median 0,015 USD og 90-persentil 0,047 USD, men dette er blandede tidligere jobbstørrelser; VHH-protokollen mangler egen prisstatistikk. Det er **ikke et tilbud eller en øvre kostnadsgrense**. AF2-IG har historisk 90-persentil 0,00087 USD per mål, OpenDDE-ABAG 0,011 USD per mål. Modellvalg må følge formatet: OpenDDE-ABAG er dokumentert for Fab, mens en VHH kan trenge en annen cofolder. [Live modellkontrakt og kostnadsforklaring](https://japanfold.aiand.com/docs/models-and-limits/)

## Klargjort i prosjektet

`prepare_target.py` matcher alle 109 modellerte HER2-rester i arrangørens lokale struktur mot RCSB-sekvensen for `1N8Z_3`. Den lager en sammenhengende **119-residuers pilotsekvens** for de samme endepunktene, med de naturlige restene 581–590 inkludert som sekvens. Den oppfinner ingen koordinater for det uoppløste partiet.

RCSB-mappingen viser at entity-posisjon 1–607 svarer til UniProt P04626 posisjon 23–629. Pilotområdet 489–607 svarer derfor til UniProt 511–629. Detaljert CSV mapper hver pilotposisjon, koordinatdekning og de 19 HER2-restene som kontaktes ved 4,5 Å. Ikke bland disse nummereringssystemene når et API ber om 1-baserte målposisjoner. [1N8Z](https://www.rcsb.org/structure/1N8Z) · [RCSBs sekvensmapping](https://sequence-coordinates.rcsb.org/)

Filene `her2_pilot_target.fasta`, `her2_pilot_residue_map.csv`, `target_preparation.json` og `rcsb_1n8z_her2_mapping.json` er lokale, sporbare inngangsressurser. Pilotsekvensen er et avgrenset mål for innledende design; den er ikke en ferdig validert modell av hele HER2. Større antigenkontekst, uoppløst sløyfe og relevante glykosylasjoner må vurderes på finalister.

`preflight.py` kontrollerer Fab/VHH-sekvenser, deklarert kjedeoppsett, kanoniske aminosyrer, lengde, nummerering, duplikater og sekvenshash. Alle 20 par i den eksisterende review-listen består disse lokale sjekkene. Minimum nummereringskonfidens er omtrent 0,861. Ved enkel posisjonsvis sammenligning av de like lange parene er identiteten til trastuzumab minst 96,9 %. Dette er en diagnostikk, ikke det offisielle databasesøket. Det er ingen grunnlag for å presentere disse som de novo.

En viktig grense: immunum/IMGT gir **13 rester** i CDRH3 der arrangørens muterte vindu har **10**. Begge sekvensdelene lagres tydelig som ulike definisjoner. Det offisielle skjemaet og verktøyversjonen må avgjøre ekstraksjonen før nyhetsfiltrering.

## Kvalitetssjekker og åpne porter

| Kontroll | Resultat nå | Hva som må til videre |
|---|---|---|
| Reproduserbar evidens | Bestått: sju eksisterende tester, identiske analyser/figur og kontroll av 193 kildefiler | Frys det eksakte innsendingspanelet med versjon og hash. |
| Ny forhåndskontroll | Tre nye regresjonstester bestått; alle 20 gamle par består lokale sekvenssjekker | Kjør samme kontroll på nye kandidater. Verktøyet gir aldri offisiell track. |
| Antistofftype | Gamle Fab-par nummereres; ingen ny VHH evaluert | VHH må være et fungerende enkelt-domeneantistoff, ikke bare en tung Fab-kjede. Kontroller fold og offisiell type. |
| Nyhet og spor | Ikke offisielt verifisert | Validatorversjon, referansebase, nærmeste treff, identitet, tildelt spor og sekvenshash må lagres. |
| Cysteiner og disulfider | Gamle kjeder har to Cys hver; paring ikke bevist av antallet | Kontroller forventede disulfider, fri Cys og eventuelle ekstra broer i struktur og offisielt verktøy. |
| Målsekvens og nummerering | Pilotsekvens og 109 koordinatrester matcher; 19 referansekontakter mappet | Bevar riktig naturlig sekvens og eksplisitt restkart i alle modeller. |
| Full mål-/glykan-kontekst | Åpent | Undersøk kollisjoner mot større HER2-kontekst og relevante glykosyleringer. Uavklart glykanmodell er ikke «bestått». |
| Grensesnittskår | Verifisert for eksisterende Fab-oppsett | Lag kjederollebasert analyse for VHH. Dagens firekjedeanalyse antar VL/VH/C/D og kan ikke brukes uendret. |
| Geometri | Eksisterende strukturer og avstandsfølsomhet er kontrollert | Nye design trenger kollisjoner, kjedekontinuitet, antistofffold, begravd grenseflate, refold-RMSD og HER2-fotavtrykk ved flere avstander. |
| Uavhengig modell | JapanFold tilgjengelig; ingen fullført OpenDDE-evaluering i den kontrollerte historikken | Refold finalister med en annen modell; et annet vertsnavn for samme modell er ikke uavhengig metode. |
| Template/initial guess | Eksisterende løp bruker kjent struktur | Skill designbetinget/initial-guess-sjekk fra cofold uten påtvunget bindingspose. AF2-IG er ikke en blind dockingtest. |
| Kontrollgrunnlag | WT og gjentatte Fab-kontroller reproduseres | Bruk kompatible positive kontroller og decoys for VHH; sammenlign ikke absolutte Fab- og VHH-konfidensskårer som om de hadde samme fordeling. |
| Seeds og rangstabilitet | Run 009 er fortsatt ufullstendig i analysert snapshot | Krev komplett kandidat–kontroll-paring for hvert sammenlignet seed og rapporter manglende resultater. Ingen robust forbedring er dokumentert i snapshotet. |
| Målt bindingskalibrering | Retrospektiv HER2-audit reprodusert; strukturkalibreringspanelet hadde null ferdige datapunkter i snapshotet | Ikke gi nye VHH-er «p(binding)» fra en FACS-modell trent på trastuzumab-CDRH3. Unngå trening/test-overlapp og seleksjonsbias. |
| Epitope | Predikert fotavtrykk kan måles | Konkurranse mot trastuzumab er den avgjørende eksperimentelle kontrollen. Kontaktlikhet alene er ikke bevis. |
| Termostabilitet og kjemi | Ingen ny kandidat har målt Tm | Hold Tm, kjemisk degradering, aggregasjon og uttrykk atskilt. Eventuell ΔΔG er en støtteindikasjon for en definert sammenligning. |
| Uttrykk og spesifisitet | Ikke målt for nye kandidater | Screen sekvens-/overflaterisiko og relevante off-targets. Hold «ingen uttrykk», «ingen rapporterbar fit» og «ikke målt» som ulike utfall. |
| Innsending | Ranglister finnes, men offisielle kvitteringer mangler | Velg én endelig rangering, korrekt VHH/Fab/scFv-format, metadata og godkjente reservesekvenser. |

## Ressursbruk med en konkret hensikt

**JapanFold:** undersøk en liten, epitopebetinget VHH-pilot først, eksempelvis 4–8 kandidater for å teste format og kjedenummerering. Piloten er en programvare-/formatprøve, ikke en kampanje med dokumentert treffrate. Utvid bare dersom faktisk output er et gyldig antistoff og en troverdig vei til de novo-kvalifisering finnes. En «nanobody»-etikett fra API-et er utilstrekkelig. Bruk lokal sekvenskontroll før flere refolds, AF2-IG på kompatible designkomplekser og en annen cofolder på de få finalistene. [Designkontrakt](https://japanfold.aiand.com/docs/designs/) · [Prediksjonskontrakt](https://japanfold.aiand.com/docs/predictions/)

**Apheris:** behold det fungerende optimaliseringsløpet og muligheten for et antistoffspesifikt alternativ med flere CDR-er. Ikke endre de delte wrapperne for å få VHH gjennom et Fab-skjema. Nye inn-/utdata trenger eget run-ID og manifest, og GPU-jobber må bruke teamets lås.

**Nebius:** bruk NanoBodyBuilder2 til kandidatens antistofffold dersom pilotsekvensene er gode nok til å gå videre. Modellens eget strukturavvik er et nyttig signal, men verken Tm eller antigenspesifisitet. Live-schemaet til `stab-ddg` viser operasjonen **`predict-binding-ddg`**: bindingsenergiendring ved mutasjoner i et angitt kompleks, ikke smeltetemperatur. Det må ikke presenteres som et termostabilitetsmål. Ingen slik prediksjonsjobb er kjørt.

**AMASS:** søkene fant BoltzGen, RFdiffusion-antistoffarbeidet og den blindede Ginkgo-developability-konkurransen. Dette støtter bruk av generativt design med etterfølgende screening, og en forsiktig behandling av stabilitetsprediksjoner. RFdiffusion-artikkelen inkluderer eksperimentell screening og affinitetsmodning; resultatene er ikke en forventning om subnanomolar HER2-binding fra en liten pilot. Ginkgo rapporterer topp Spearman 0,392 for Tm på et holdt-utenfor testsett av kliniske antistoffer; det er heller ingen direkte VHH-kalibrering. [RFdiffusion primærartikkel](https://doi.org/10.1038/s41586-025-09721-5) · [Ginkgo primærartikkel](https://doi.org/10.1080/19420862.2026.2634216)

AMASS-bruken her var tre søk à fem kreditter, totalt **15 kreditter / 0,15 USD**. Treffene er litteraturhenvisninger og abstrakter, ikke en full systematisk litteraturgjennomgang. JapanFold-kallene var metadata-/kontokontroller, ikke nye prediksjoner. Kredittsaldiene er delte øyeblikksbilder, ikke øremerkede budsjetter.

## Forsøket som kan gjøre casen sterk

Presenter én gjennomgående forskningsbeslutning: **Hvilken evidens fortjener de få laboratorieplassene?** Bruk eksisterende optimaliseringsdesign som etablert arm, en de novo-arm bare hvis den kvalifiserer, og samme tydelige skille mellom sekvensgyldighet, strukturell plausibilitet og de tre laboratorieutfallene.

Dere har allerede et konkret funn å bygge på: I den reproduserte, retrospektive SPR-sammenligningen av 584 unike, FACS-usette ikke-WT-konstruksjoner med tolkbar fit-status fikk den faste BLOSUM-baselinen AUC 0,847 mot 0,751 for FACS-modellen. En enkel avstand til nærmeste FACS-high kom omtrent likt med BLOSUM, så ikke påstå at én metode er entydig best. Panelet var metodeselektert, «fit» er ikke bare binding, og dette beviser ingen generell prospektiv gevinst. Det viser hvorfor en høy intern modellskår alene er et svakt utvalgskriterium.

Det nye bidraget er et beslutningsløp som kan vise hvilke kandidater som forkastes, hvorfor modeller er uenige, og hvilken måling som kan avgjøre uenigheten. Frys utvalget før Adaptyv-resultatene og mål uttrykk, SPR, konkurranse og termostabilitet med samme kampanjekontroll. Ikke lov et S-tier-antistoff før disse dataene finnes.

## Prioritet resten av dagen

1. Skaff faktisk validator/portal og bekreft format, referansebase og CDRH3-definisjon. Dette er første avklaring med arrangøren.
2. Behold minst hoveddelen av arbeidsinnsatsen på eksisterende optimalisering, komplett rangliste og pitch. Gjennomgangen har ikke vist at et nytt VHH-løp er en bedre konkurransesatsing.
3. Gjennomfør kun en avgrenset VHH-pilot når mål-/formatkontrakten og nyhetsvurderingen er avklart; mål faktisk tid, leverte design og gyldighetsandel før utvidelse.
4. Sett en intern beslutning senest rundt 15:00 Oslo: hvis ingen troverdig de novo-kandidat finnes, behold dette som dokumentert utviklingsarbeid og ikke bruk en garantert testplass på etiketten alene. Hvis en kandidat kvalifiserer og har sammenhengende evidens, vurder én av de fire plassene til den; dette er et porteføljevalg, ikke et krav fra konkurransen.
5. Rundt 16:00: frys rekkefølge, sekvenshash, begrunnelse, forbehold og reservasjonsliste. Bruk tiden fram til den oppgitte 18:00-fristen på demonstrasjon, repo og pitch. Tilpass etter arrangørenes faktiske dagsplan.

## Reproduserbarhet

Se `README.md` for den nye isolerte sekvenskontrollen. Kjør `prepare_target.py` med teamets vanlige Python-miljø med Biotite/SciPy. Den gamle analysen gjenskapes med `.venv/bin/python review/replay.py`. Nye ressurser ligger bare i `review/denovo/`; eksisterende kandidater, resultatfiler, ranglister og GPU-jobber er bevart.

`evidence/` inneholder autentiseringsstatus uten nøkler, utvalgte offentlige modellkontrakter, AMASS-søkelogg og kilde-ID-er, testlogg, preflight-resultat for de 20 eksisterende parene og logg fra den vellykkede reproduksjonen. De store referansedataene forblir i det eksisterende datasettet.
