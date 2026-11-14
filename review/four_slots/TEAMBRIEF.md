# Hvilke fire av førti antistoffer skal få en labplass?

**Oppgaven fra arrangøren.** Lag og ranger varianter av trastuzumab. Dette er et antistoff som fester seg til proteinet HER2. Laboratoriet undersøker hvor godt variantene binder, om de konkurrerer med originalen om samme sted, og hvor godt de tåler varme. Fire plasser er garantert.

**Produktet vi kan vise.** En demonstrasjon hvor dommeren får 40 gamle kandidater med skjulte labresultater og et budsjett på fire tester. Vis hvilke fire en enkel sekvensregel og lagets eksisterende modell velger. Avslør så hva laboratoriet faktisk klarte å måle. Vis kandidater med ukjent utfall som egen kategori.

**Første kjøring.** Vi fant 255 ulike historiske varianter med fire til seks endringer fra originalen og uten eksakt overlapp i treningsskjermen. Av dem hadde 82 en tallfestet bindingsstyrke, 128 manglet en rapporterbar tilpasning, 41 var inkonklusive og fire manglet rapportert utfall. Programmet trakk 40 ulike per runde i 5 000 runder, og alle tre utvalgsmetodene fikk se samme gruppe. Regelen og den lagrede modellen brukte bare sekvensen til å velge fire. Eksakte skårlikheter ble løst etter trekkeorden.

| Valg av fire | Tallfestet binding | Ingen rapporterbar tilpasning | Uavklart eller manglende resultat |
|---|---:|---:|---:|
| Tilfeldig | 1,28 | 2,03 | 0,69 |
| Lagets FACS-modell | 2,11 | 0,99 | 0,90 |
| Sekvensregelen BLOSUM62 | 2,38 | 0,72 | 0,89 |

Tallene er gjennomsnitt per fire plasser i en simulering med gjenbruk av 255 historiske varianter. Deler av kildestudien brukte BLOSUM ved utvalg av kandidater. Utvalgsbias og bare tre historiske eksempler med alle lagets designkrav begrenser overføringen. En rapporterbar bindingsstyrke kan være svakere enn originalen. Dette sier heller ingenting direkte om varme eller bindested. [Opprinnelig HER2-studie](https://doi.org/10.1101/2024.03.26.586756)

**Spørsmålet som gjør dette relevant for de nye designene.** Avstand til den nærmeste tidligere positive sekvensen gjorde det godt historisk, men ga nøyaktig samme svar på alle 40 nye kandidater. Vår nye gjennomgang av lagets StaB-ddG-tabell gir et annet eksempel. På åtte målte kontroller fulgte modellen i stor grad rekkefølgen fra svak til sterk binding (Spearman 0,88). Likevel rangerte den ctrl03 først. Historisk KD var 0,224 nM for ctrl03 og 0,0234 nM for ctrl01. Ctrl01 bandt rundt 9,6 ganger sterkere i disse målingene, og rangert etter målt binding var ctrl03 nummer tre. Kontrollene var håndplukket over et bredt styrkeintervall. Et åpent spørsmål er om en strukturmodell kan skille mellom to allerede lovende kandidater med samme antall endringer.

**Hva teamet bør gjøre nå.** Én person viser fire-av-førti-demonstrasjonen. Én bruker den planlagte historiske kontrollkjøringen til å sammenligne modellene på eksempler med like mange endringer, med fasiten skjult under utvelgelsen. Én viser de fire nye forslagene, hva laboratoriet kan lære av hver, og sjekker fullsekvensene med arrangørens validator. For de nye designene står alle tre egenskaper åpne til Adaptyv har målt dem.

**Melding du kan sende til teamet**

> Jeg foreslår at vi pitcher «Hvilke fire av førti fortjener en labplass?». Vi kan vise dommerne et valg på gamle antistoffer, skjule labfasiten og så avsløre hvilken regel som faktisk fant målbar binding. Deretter viser vi hvorfor en regel som fungerte historisk, ga samme svar på alle våre 40 nye design. La oss bruke neste analyse på det vanskelige valget mellom de lovende kandidatene, og avslutte med de fire vi vil teste og hvorfor.

**Gjenta fra Team 14-prosjektet**

```bash
.venv/bin/python review/four_slots/historical.py
```

[Resultater med inngangssjekksummer](historical.json) · [Kode](historical.py)
