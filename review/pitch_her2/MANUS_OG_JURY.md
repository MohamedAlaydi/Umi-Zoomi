# Kan vi endre grepet og fortsatt treffe samme sted på HER2?

**Foreslått pitch for optimaliseringssporet.** Bruk den engelske presentasjonen på scenen. Under står et norsk øvingsmanus på omtrent to minutter. Tidsrammen er vårt forslag. Den oppgitte konkurranseteksten spesifiserer ingen individuell taletid.

## Det du kan si

**1. Utgangspunktet.** «Trastuzumab er et antistoff som fester seg til proteinet HER2. Vi vil lage en variant som binder godt, treffer det samme området og tåler varme bedre. I den målte strukturen fant vi fire byggesteiner i en løkke som berører HER2. Da fikk vi en idé. Hvis vi beholder de fire byggesteinene og endrer dem rundt, beholder vi kanskje grepet.»

**2. Overraskelsen.** «Vi gikk gjennom mulighetene, rangerte dem med data fra tidligere forsøk og valgte 40 forskjellige design. Alle 40 beholdt de fire byggesteinene. Så lot vi modellen forutsi formen seks ganger per design. Bare 24 av de 40 hadde alle fire kontaktene i hver beregning. Originalen beholdt dem i alle seks.»

**3. Det konkrete eksperimentet.** «Se på disse to. Begge har fem endringer. Den enkle sekvensregelen gir dem nøyaktig samme poengsum. Likevel beholdt den ene alle fire kontaktene i seks av seks beregninger. Den andre gjorde det i null av seks. Hvis begge binder HER2, hvilken av dem konkurrerer fortsatt med originalen om det samme området? Det kan Adaptyv faktisk teste.»

**4. Hvorfor vi brukte denne regelen.** «Vi prøvde først å velge fire av førti blant gamle antistoffer hvor labresultatene allerede fantes. I snitt fikk vi en tallfestet binding for 1,28 av fire ved tilfeldig valg, 2,11 med vår AI-modell og 2,38 med en enkel regel for aminosyrebytter. Det er en historisk sammenligning. Vi kjenner ennå ingen av de nye kandidatenes binding eller varmetoleranse.»

**5. Hvem vi sender og hvorfor.** «Vi bruker én plass på en kandidat med både god sekvens og stabil kontakt i modellen, to på det sammenlignbare paret, og én på en utfordrer som bare beholdt to av de opprinnelige byggesteinene. Det gir forsøkslederen fire begrunnede valg når det er dyrt å teste hvert antistoff.»

**6. Hva som vil endre meningen vår.** «Vi vil fryse rangeringen før måling. Hvis begge i paret binder og konkurrerer like godt med originalen, har de fire modellkontaktene gitt liten hjelp til å skille dem i dette forsøket. Hvis de skiller seg som forventet, har vi en grunn til å prøve regelen på flere uavhengige par. Vi vil vise både treff, bommer og tilfeller laboratoriet ikke kunne måle.»

## Slik treffer dette oppgaven

| Arrangørens kriterium | Hva laget viser |
|---|---|
| Vitenskapelig skjønn, 40 % | Dere tok utgangspunkt i krystallstrukturen, utfordret en antakelse dere selv hadde gjort, og brukte resultatet til å endre hvilke molekyler dere foreslår. Lysbilde 2, 3 og 5. |
| Gjennomføring, 20 % | Originale Apheris Foundry-resultater, samme modelloppsett for variant og kontroll, seks startverdier, kildekode og fullsekvenser med sjekksummer. For en ukjent Fab kan dommeren kjøre den eksisterende sekvensevalueringen i teamrepoet med `.venv/bin/python review/replay.py --evaluate NY_FIL.csv`. Inkluder versjonen av koden dommeren skal kjøre når teamet publiserer repoet. |
| Brukerbehov, 20 % | Forsøkslederen har flere lovende design enn tilgjengelige plasser. Teamet leverer en rangert liste, en begrunnelse per plass og eksplisitte spørsmål til laboratoriet. Lysbilde 4 og 5. |
| Vei til praktisk verdi, 20 % | Gjenta den samme prioriteringen i neste utviklingsrunde og registrer brukbare målinger og treff på alle tre egenskapene per bestilte test. Lysbilde 6. |

Apheris-presentasjonen s. 5–8 angir HER2, to spor, validering, fire garanterte plasser og tre labmål. Oppgavebeskrivelsen s. 1 og 7–9 ber om en robust pipeline, en rangert liste på opptil 20 og sammenligning med samtidig målt trastuzumab. S/A/B bestemmes etter laboratoriets målinger. Kreativitet går inn i hvordan dere stiller spørsmålet, utfordrer regelen og velger molekylene. Tabellen gjengir de fire formelle vektene. Arrangementsnettsiden sier at dommeren prøver et ukjent eksempel, ber om en presentasjon og en GitHub-lenke, og beskriver publisering av testede design og resultater i Proteinbase. Et separat vitenskapelig arbeid er en mulighet. [Offisiell FAQ](https://oslo-ai-antibodies-hackathon.vercel.app/)

## Forslaget som kan bli et vitenskapelig arbeid

**Spørsmål.** Blant trastuzumab-varianter som allerede har sammenlignbar sekvensendring, hjelper stabilt beregnet kontakt oss å velge hvilke som beholder konkurranse med trastuzumab? Relevansen kommer fra at rangering innenfor nært beslektede antistoffgrupper har vist seg vanskelig i blindede forsøk. Teamets bidrag er det konkrete HER2-paret, kontrollene og en forhåndsuttalt testbar forventning. [Erasmus mfl.](https://pubmed.ncbi.nlm.nih.gov/42618805/) · [Krystallstrukturen 1N8Z](https://www.rcsb.org/structure/1N8Z)

**Før labresultatet.** Lås sekvensene og lagre datert rangering med metode, kontaktdefinisjon, alle seks modellresultater, kriterier for sammenligning og kontroll-ID. Forventningen er større bevart konkurranse for anas_015 enn for anas_009, gitt at begge gir tolkbar binding og kan sammenlignes under laboratoriets betingelser. Registrer en eventuell uavgjort. De to har forskjellig kjemi utover de matchede målene. Paret er valgt etter utforskning av modelldata og gir en prospektiv hypotese om labresultatene.

**Etter labresultatet.** Dokumenter per variant om den lot seg produsere, tallfestet bindingsstyrke, konkurranse og direkte varmemåling. Bruk laboratoriets egen kontroll, måleusikkerhet og kriterier. Manglende uttrykk eller uleselig binding gjør spørsmålet om konkurranse uavklart. For en mer generell publikasjon trengs flere matchede par og en uavhengig serie. Et robust negativt resultat kan være like informativt. De seks prediksjonene deler modell, strukturmal og et avkortet HER2. De er tekniske repetisjoner. Konkurranse påviser overlappende binding operasjonelt, og fastslår ikke alene en identisk kontaktflate.

## Hva vi endret og hva som faktisk er kontrollert

- Etter gjennomlesing av den ferdige kjøringen er foreslått topp fire **anas_007, anas_015, anas_009 og r004_cdrh3_3**. De to første løftes fra reserveplass 8 og 13. anas_016 og anas_027 flyttes til reservelisten. De øvrige kandidatene følger tidligere innbyrdes rekkefølge. Den tidligere listen ligger urørt. Dette er en begrunnet prioritering av forsøksplasser. Rollene er ikke en tallfestet sannsynlighet for å slå originalen.
- En annen mulig matchet sammenligning i samme 20-liste er anas_021 og anas_004. Også disse har likt mutasjonsantall og lik sekvensskår seg imellom og kontakt i henholdsvis 0/6 og 6/6 prediksjoner. De kan undersøkes dersom laget får flere plasser.
- Kjøring 009 hadde en eldre oppsummering før alle GPU-filene var ferdige. For denne pitchen ble de ferdige råfilene brukt direkte. På det stratifiserte kalibreringspanelet med 30 tidligere målte konstruksjoner og tre startverdier per variant var korrelasjonen mellom minste tunge-kjede–HER2-parskår og logaritmen av målt KD **−0,34** blant de 25 med tallfestet KD. Det er en annen skår og et annet endepunkt enn kontakt mot konkurranse. Vi presenterer ingen slik kalibrering for konkurranse eller varmetoleranse.
- På denne verten ga den gjenopprettede lokale abguard-versjonen med medfølgende referansedatabase **20/20 valid** for akkurat disse kjedeparene. De samme 20 er bare omrangert. Bygget kom fra en lokal demoinstallasjon. Arrangørens bekreftelse på versjon og endelig aksept gjenstår. Laget har også et pågående de novo-spor. Denne pitchen gjelder optimalisering av Fab.
- Reproduser seks-seed-sjekken fra teamrepoet med `.venv/bin/python review/pitch_her2/pitch_evidence.py .`. Den historiske sammenligningen kjøres med `.venv/bin/python review/four_slots/historical.py`. Historiske resultater gjenbruker 255 konstruksjoner i 5 000 trekninger. Deler av kildestudien brukte sekvensregelen ved utvalg, så den historiske forskjellen kan være påvirket av utvalgsbias. [Historisk HER2-studie](https://doi.org/10.1101/2024.03.26.586756)
