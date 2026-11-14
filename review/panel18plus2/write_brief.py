from pathlib import Path
import json
import csv
folder=Path(__file__).parent
r=json.loads((folder/'VERIFICATION.json').read_text())
lookup={row['query']:row for row in r['four_repeats_hits_of19']}
assert sum(x>y for col in ['no_template','HER2_only_template'] for x,y in zip(lookup['anas_015'][col],lookup['anas_009'][col]))==3
assert sum(y>x for col in ['no_template','HER2_only_template'] for x,y in zip(lookup['anas_015'][col],lookup['anas_009'][col]))==3
s=(folder/'teambrief_base.md').read_text()
section='''## Hva 60 nye Apheris-strukturer faktisk viste

Alle de 20 designene, originalen og én ekstra VHH-reserve ble kjørt med samme HER2-sekvens i to oppsett. Fire konstruksjoner fikk også to ekstra seeds per oppsett. Vi fikk dermed 60 fullførte strukturer fra 22 unike komplekser, med 14,39 minutter samlet kjøretid rapportert av modulene på lagets H100. Det kom ingen ekstra API-regning eller labbestilling.

| Konstruksjon | Uten strukturmal, seed 42 / 7 / 101 | Med bare HER2 som strukturmal, samme seeds |
|---|---:|---:|
'''
for name in ['trastuzumab_wt','anas_007','anas_015','anas_009']:
    row=lookup[name]
    a=' / '.join(map(str,row['no_template']))
    b=' / '.join(map(str,row['HER2_only_template']))
    section+=f'| {name} | {a} | {b} |\n'
section+='''
Hvert tall er hvor mange av 19 kjente kontaktrester som ble truffet. Originalen traff 7–13/19. Den tidligere hovedkandidaten traff 0–6/19. I duellen mellom anas_015 og anas_009 vant hver kandidat tre av seks sammenlignbare oppsett på denne kontaktmålingen. Seeds er gjentatte simuleringer av de samme proteinene. Summen er ingen sannsynlighet for binding. Boltz-resultatet på fire løkkeposisjoner og det nye resultatet på hele HER2-flaten er to forskjellige spørsmål.

For anas_015 og anas_009 er den prospektive hypotesen at førstnevnte konkurrerer sterkere med trastuzumab når begge binder og bindingsnivået er sammenlignbart. Dersom arrangøren bare rapporterer en binær konkurransetest, er støtte for hypotesen at førstnevnte består og sistnevnte ikke gjør det. Like utfall skiller ikke kandidatene. Hvis bare én uttrykkes eller bindingen ikke kan måles, er spørsmålet uavklart. Designtype, andre sekvensforskjeller og usikkerhet i assayet begrenser slutninger fra ett par.

[Alle 60 strukturresultater](OPENFOLD_RESULTS.csv) · [Kjøringskvitteringer](VERIFICATION.json)

'''
s=s.replace('## Hvorfor disse fire?',section+'## Hvorfor disse fire?')
(folder/'TEAMBESLUTNING.md').write_text(s)
