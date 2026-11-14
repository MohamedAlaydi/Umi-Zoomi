"""Publish an auditable status snapshot; no model result is labelled S/A/B."""
import csv,json,hashlib,shutil,difflib,os
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from prepare import ROOT,RUN,table,sha
OUT=Path(os.environ.get('FRESH_REPORT_OUTPUT',str(ROOT/'review/fresh_evaluation/report')))


def main():
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'evidence').mkdir(exist_ok=True);(OUT/'code').mkdir(exist_ok=True)
 metrics=json.loads((RUN/'training/metrics.json').read_text());gen=json.loads((RUN/'training/generation-summary.json').read_text());impact=json.loads((RUN/'source-audit-impact.json').read_text());ddg=json.loads((RUN/'binding-ddg-calibration.json').read_text());assays=json.loads((RUN/'fresh-assay-audit.json').read_text())
 geometry=json.loads((RUN/'fresh-full-context-geometry.json').read_text());rows=geometry['rows'];good=[r for r in rows if r['status']=='ok'];jobs=[]
 for folder in sorted(RUN.iterdir()):
  if folder.is_dir() and (folder/'job.json').exists():
   j=json.loads((folder/'job.json').read_text());jobs.append(dict(directory=folder.name,job_id=j['id'],status=j['status'],done=j.get('done'),total=j.get('total'),partial=j.get('partial'),error=j.get('error')))
 status=dict(snapshot_UTC=datetime.now(timezone.utc).isoformat(),jobs=jobs,delivered_geometry_rows=len(good),geometry_errors=[r for r in rows if r['status']!='ok'])
 (OUT/'status.json').write_text(json.dumps(status,indent=2));(OUT/'evidence/geometry.json').write_text(json.dumps(geometry,indent=2))
 files=['predeclared.json','new-job-manifest.json','new-sequence-experiment.json','independent-model-protocol.json','source-input-hashes.json','pool.json',
  'fresh-assay-audit.json','fresh-SPR-construct-audit.csv','binding-ddg-calibration.json','fresh-binding-ddg.csv','source-audit-impact.json','novelty-source-impact.csv',
  'fresh-known-antibody-recheck.csv','fresh-rcsb-sequence-searches.json','fresh-rcsb-hit-entities.json','fresh-rcsb-extra-hit-entities.json',
  'fresh-assay-and-sequence-scores.csv','fresh-affinity-sensitivity.csv','training/affinity-sensitivity.json','training/SPR-GP-OOF.csv',
  'candidate-evidence.csv','prioritisation-policy.json','local-boltz2-evidence.json','fresh-full-context-geometry.csv','regression-tests.log','training/protocol-before-fit.json','training/metrics.json','training/SPR-OOF.csv','training/generation-summary.json']
 for name in files:
  p=RUN/name
  if p.exists():shutil.copy2(p,OUT/'evidence'/name.replace('/','__'))
 shutil.copy2(RUN/'training/new-proposals.csv',OUT/'NYE_SEKVENSFORSLAG.csv')
 shutil.copy2(RUN/'new-sequences-submission.csv',OUT/'16_VALIDERTE_NYE_FAB.csv')
 for kind in ['validation','new-sequence-validation','panel-validation','top4-validation']:
  for name in ['explicit-reference-receipt.json','validated-reference-checked.csv']:
   p=RUN/kind/name
   if p.exists():shutil.copy2(p,OUT/'evidence'/(kind+'__'+name))
 for p in (ROOT/'review/fresh_evaluation').glob('*.py'):shutil.copy2(p,OUT/'code'/p.name)
 shutil.copy2(ROOT/'review/requirements.txt',OUT/'code/requirements.txt')
 changes=[]
 for name in ['scripts/novelty.py','scripts/multiseed_analysis.py','people/anas/collect_refold.py']:
  before=RUN/'source-before'/name.replace('/','__');after=ROOT/name
  changes.extend(difflib.unified_diff(before.read_text().splitlines(True),after.read_text().splitlines(True),fromfile='before/'+name,tofile='after/'+name))
 (OUT/'SOURCE_CHANGES.diff').write_text(''.join(changes))
 for p in RUN.glob('18plus2_DRAFT*.csv'):shutil.copy2(p,OUT/p.name)
 # Scientific figures: held-out assay checks, conditional score tradeoff and fresh docking.
 plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
 fig,axes=plt.subplots(1,3,figsize=(15,4.5),layout='constrained')
 spr=table(RUN/'training/SPR-OOF.csv');observed=np.log10([float(r['kd_nM'])/metrics['SPR']['WT_historical_kd_nM'] for r in spr]);pred=np.array([float(r['OOF_log10_KD_ratio']) for r in spr])
 axes[0].scatter(observed,pred,s=20,alpha=.6,color='#245d85');lo=min(observed.min(),pred.min());hi=max(observed.max(),pred.max());axes[0].plot([lo,hi],[lo,hi],'--',color='grey')
 axes[0].set(xlabel='Measured log10(KD / historical WT)',ylabel='Cluster-held-out prediction',title=f"Quantified SPR, n={len(spr)}\nSpearman {metrics['SPR']['cluster_OOF_rho']:.2f}")
 scored=table(RUN/'fresh-assay-and-sequence-scores.csv')
 for roles,color,label in [(['candidate'],'#999999','Original raw Fab pool'),(['new_model_generated_candidate'],'#df8a24','New H3 proposals')]:
  subset=[r for r in scored if r['role'] in roles];axes[1].scatter([float(r['SPR_predicted_log10_KD_ratio']) for r in subset],[float(r['FACS_agreement_min']) for r in subset],label=label,color=color,s=28,alpha=.8)
 axes[1].axvline(0,color='grey',ls='--');axes[1].set(xlabel='Conditional SPR model log10(KD / WT)',ylabel='Calibrated FACS high-class agreement',title='Separate experimental objectives\nFACS high is not tighter-than-WT affinity');axes[1].legend(fontsize=8)
 for kind,color,label in [('paired','#245d85','Fab'),('vhh','#b45963','VHH')]:
  subset=[r for r in good if r['kind']==kind and r['model']=='mol1'];axes[2].scatter([r['global_iptm'] for r in subset],[r['epitope_recall_4.5'] for r in subset],color=color,label=label,s=28,alpha=.8)
 axes[2].set(xlabel='Global ipTM (Fab/VHH not directly comparable)',ylabel='Recall of 19 native protein contacts',title=f'Fresh, full607 HER2, Mol1\n{sum(r["model"]=="mol1" for r in good)} delivered structures');axes[2].legend(fontsize=8)
 fig.suptitle('Independent checks guide experiment priority — no measured candidate tier',fontsize=14);fig.savefig(OUT/'NY_KVALITETSKONTROLL.png',dpi=180);fig.savefig(OUT/'NY_KVALITETSKONTROLL.pdf');plt.close(fig)
 pending=[j for j in jobs if j['status'] not in ['succeeded','failed','canceled']]
 text=f'''# Ny evaluering, trening og sekvensgenerering

Oppdatert {status['snapshot_UTC']}. Dette er en gjennomgått statusrapport; jobber som fortsatt kjører står i [status.json](status.json). Ingen kandidat har fått bekreftet S-, A- eller B-tier.

## Hva som faktisk er nytt

- Ny trening fra de originale målingene, uten gamle modellvekter, lagrede sannsynligheter eller tidligere rangering som fasit. {sum(json.loads((RUN/'training/protocol-before-fit.json').read_text())['counts'].values()):,} FACS-sekvenser etter at alle SPR-overlapp er holdt ute. Trening, kalibrering og test har adskilte mønstre ved fire native kontaktposisjoner. Dette er en strengere skaffoldintern test, ikke et bevis på overføring til ukjente antistoffamilier.
- To FACS-modeller: test-AUC {metrics['FACS']['categorical_gbm']['test_auc']:.3f} og {metrics['FACS']['onehot_logistic']['test_auc']:.3f}. De modellerer skjermingsklasse, ikke sannsynlighet for S-tier. Sammenhengen med kvantitativ SPR er svak, og endepunktene blandes derfor ikke.
- En separat modell for faktisk rapportert SPR-KD, {metrics['SPR']['quantified_constructs']} unike konstruksjoner, {metrics['SPR']['clusters']} sekvensklynger. Klynseholdt-ute Spearman {metrics['SPR']['cluster_OOF_rho']:.3f}, MSE {metrics['SPR']['cluster_OOF_MSE']:.3f} mot konstant-baseline {metrics['SPR']['mean_baseline_MSE']:.3f}. Dette er betinget på målbart KD; manglende fit er ikke fylt inn som et negativt bindeforsøk.
- {gen['raw_proposals']:,} nye forslag trukket deterministisk fra WT og seks målte foreldre; {gen['unique_after_WT_identity_gate']:,} ulike etter WT-identitetsfilter, {gen['exact_novelty_passes']:,} bestod av de 2 000 modellprioriterte forslagene. {gen['diverse_output']} råforslag beholdt. Et tak på 64 ble overskredet fordi løkken fullførte en Pareto-front; løkken er rettet, og de opprinnelige 68 er bevart for sporbarhet.
- 12 nye H3-foreldre pluss fire matchede rammeverksvarianter er valgt til ny strukturevaluering. **Alle 16 består lokal abguard med eksplisitt referanse.** Filen [16_VALIDERTE_NYE_FAB.csv](16_VALIDERTE_NYE_FAB.csv) er en valideringsbatch, ikke en ferdig rangert innsendingsfil.
- Hele HER2s 607 aminosyrer, ny seed 271828, ingen inputtemplate/hotspots: 87 opprinnelige kandidater/kontroller og 17 nye sekvens-/rammeverkstester. OpenDDE gir en separat modellkontroll av 25 forhåndsvalgte mål. Begge modellene er fortsatt beregninger; én seed gir ikke robusthetsbevis.
- Ny bindingsenergi på den eksperimentelle 1N8Z-strukturen: 76 varianter, inkludert 12 nye målte kontrollkonstruksjoner. Kontrollkorrelasjon {ddg['control_spearman_rho']:.2f}, 95 % konstruksjonsbootstrap [{ddg['control_construct_bootstrap_95CI'][0]:.2f}, {ddg['control_construct_bootstrap_95CI'][1]:.2f}]. **For usikkert til å styre rangeringen.** MC-standardfeilen er ikke prediksjonsusikkerhet. Denne modellen predikerer binding, ikke varmestabilitet.

## Feil og svake antakelser i tidligere skript

1. `multiseed_analysis.py` brukte øvre grense for å hevde non-inferiority. Det krever nedre grense. {impact['historical_NONINFERIOR_unique_sequences_lacking_required_lower_bound']} historiske unike sekvenser hadde fått en slik merkelapp uten tilstrekkelig nedre grense. Rettet. Selv korrekt statistikk for modellskår er ikke et bevis på like god biologisk binding.
2. `novelty.py` brukte Hamming for like lange sekvenser, selv om funksjonen lovet edit distance. Rettet til eksakt Levenshtein. **Dette endret ingen av de {impact['raw_Fab_sequences']} eksisterende Fab-sekvensenes nærmeste avstand**; en regresjonstest viser feilen på et skiftet sekvenseksempel. CLI-grensene er også strammet til den strengere PDF-varianten. {impact['old_loose_pass_but_fails_fresh_full_IMGT_conservative']} råsekvenser som passerte de gamle løse tallgrensene, faller utenfor den nye konservative full-IMGT-kontrollen.
3. `collect_refold.py` valgte første seed med `glob`. Flere treff krever nå eksplisitt seed, og tvetydige run-navn avvises. Sammenligning av modellkonfidens med WT beskrives som modellkonfidens, uten biologisk avvisningspåstand.
4. Første-pass-filtrene krevde bestemte kontaktrester, høy pHigh og fjerning av både D/M. Dette er hypoteser, ikke hackathonkrav eller målte Tm-forbedringer. Ny generering har myke priorer, uten disse hardkravene.
5. Beste seed, kopiert kompleks-template og en kort HER2-region kan gi for pene skårer. Den nye evalueringen bruker hele antigenet og blind refolding. Seed og kontekst er endret samtidig; forskjeller isolerer derfor ikke effekten av hver av dem.
6. FACS, kvantitativ KD, assay-reportability, konkurranse og Tm er ulike utfall. Predikerte 1,8 millioner komplekser er ikke 1,8 millioner målte bindere. Ingen nye Adaptyv-labresultater finnes for våre design.

Kodediff: [SOURCE_CHANGES.diff](SOURCE_CHANGES.diff). Regresjonstester for blant annet grenseverdier, feil seedvalg, riktig kjederolle, speiling, PAE og native kontakter ligger i `evidence/regression-tests.log`; 11 nye tester består. De eksisterende skår- og evidenstestene bestod også (5 + 7).

## Hva figurene betyr

![Nye kontroller](NY_KVALITETSKONTROLL.png)

Venstre: hvor godt den nye affinitetsmodellen predikerer holdt-ute målte konstruksjoner. Midten: ny generering søker også lavere modellert KD; høy FACS-klasse alene er utilstrekkelig. Høyre: modellkonfidens og overlapp med den native kontaktflaten er separate størrelser. Fab-global-ipTM inkluderer også VH–VL-interaksjonen og kan ikke sammenlignes direkte med VHH-ipTM.

pLDDT beskriver lokal strukturkonfidens; H3 rapporteres separat fra det ofte sikre rammeverket. Kontakt-PAE beregnes med verifisert tokenrekkefølge og begge retninger, én gang per kontaktpar. 19 kontaktrester ved 4,5 Å rekonstrueres fra native 1N8Z. Kontakt-recall og Jaccard er geometriske hypoteser om epitope, ikke et målt konkurranseforsøk. RMSD rapporteres etter hele-antigen-, bindingsdomene- og epitopejustering for å synliggjøre domeneledding. Manglende PAE blir tomt, aldri null.

## Innenfor hackathonkravene

| Krav | Praktisk håndtering |
|---|---|
| Én rangert liste, høyst 20 | 18 optimaliseringer + 2 de novo er tillatt. Ikke send hele råpoolen. |
| Topp N går til lab; fire garantert | Plasser begge spor blant topp fire dersom dere vil sikre forsøk i begge. Det reduserer antall optimaliseringer blant de fire. |
| VHH, scFv eller parret variabel Fab; totalt ≤250 aa | Nye Fab er VH120 + VL107 =227 aa. Validator kontrollerer type/lengde/nummerering. |
| Nummereringskonfidens ≥0,1; ingen uparrede cysteiner | Kjøres gjennom installert abguard med eksplisitt referanse og beholdt kvittering. Et enkelt oddetallssjekk alene er utilstrekkelig. |
| Optimalisering: H3-identitet <70 %, >2 mutasjoner fra de oppgitte sekvensene | Bruk full IMGT-H3, eksakt edit distance og alle 525 063 oppgitte løkker. Den strengere PDF-varianten håndterer avviket fra de løsere lysbildene. |
| De novo: <70 % mot nærmeste kjente antistoff; H3 minst to mutasjoner fra WT | Lokale kontroller + ny RCSB-søk/riktig variabeldomene. **Endelig databasekrav er ikke dokumentert bestått:** installert abguard sammenligner fullsekvens mot trastuzumab og har en H3-referanse; dette erstatter ikke hele Adaptyvs database. |
| S-tier etter tre målte egenskaper | SPR, konkurranse mot trastuzumab og direkte varmestabilitet, sammenlignet med samtidig målt WT. Ingen modellskår gir S-tier på forhånd. |

{len(good)} strukturer er foreløpig evaluert og {len(pending)} deljobber kjører i dette øyeblikksbildet. CSV-er og kvitteringer viser hva som er levert, mangler eller feilet. Maskinvarefeil blir ikke tolket som negative biologiske resultater.

## En sterk og redelig brystkreftcase

«Vi bygger en etterprøvbar preklinisk plattform som velger nye bindingsmoduler mot HER2 ved HER2-positiv brystkreft. Vi forbedrer utvelgelsen med faktiske målinger, bevarer det relevante epitope som hypotese, og tester en separat rammeverksstrategi for varmestabilitet. Vi forkaster rangeringer når modellene ikke består kontrollene.»

Trastuzumab er etablert ved HER2-positiv brystkreft; [EMA](https://www.ema.europa.eu/en/medicines/human/EPAR/herceptin) gir den kliniske konteksten. Våre fragmenter har ingen demonstrert behandlingseffekt eller Fc-mediert funksjon. Neste trinn er uttrykk, SPR/konkurranse/Tm med WT-kontroll, deretter cellebinding og riktig terapeutisk format før funksjon og videre preklinisk utvikling kan hevdes.

Den nye rammeverksgrenen bruker **VH S85N/R87T** fra [Ng mfl., mAbs 2025](https://doi.org/10.1080/19420862.2025.2532117). Artikkelen rapporterte høyere Tm og bevart HER2-cellebinding for full trastuzumab. Vi har verifisert restene mot artikkelens 7MN8-kjede E, ikke forvekslet dem med IMGT-posisjonene. Endringen lager et NLT-glykosyleringsmotiv; overføring til nye H3-er, Fv og cellefritt uttrykk er uprøvd. Dette er en konkret, testbar stabilitetshypotese, ikke en Tm-prediksjon.

## Reproduserbarhet

Run `014-codex-fresh-evaluation` bevarer rå sekvenser, kildehasher, fryste forespørsler, idempotenskvitteringer, model/seed/antigenkontekst, native referanse og feil. Kodekopien i `code/` viser algoritmene; originalkjøringen skjer fra prosjektets `review/fresh_evaluation/` med de opprinnelige assayfilene og valideringsmiljøet. API-nøkler og innlogging er ikke med i leveransen. Reproduksjon krever samme katalogstruktur, offentlige assaydata/hackathontilgang og API-tilgang. Dette er ikke en selvstendig installasjonspakke eller en garanti for identiske fjernmodellresultater ved senere modelloppdateringer.
'''
 extra='''
## Ny rangering og viktige kontrollresultater

[18+2, optimalisering først](18plus2_DRAFT_optimisation_first.csv) gir Fab blant de fire garanterte og plasserer de to foreløpige de novo ved15/16. [Begge spor blant topp fire](18plus2_DRAFT_both_tracks_top4.csv) flytter VHH til3/4. Dette er **forsøksprioritering, ikke S-tier-prediksjon**. En `..._evidence.csv` følger hver liste. Den endelige lokale kontrollen av standardlisten ga20 av20 godkjente med eksplisitt abguard-referanse. Endelig de novo-databasestatus er fortsatt uavklart.

Listen fordeler forsøk mellom lavere modellert KD, balanse mot FACS-klassen, FACS-sterke alternativer og to konkrete rammeverkshypoteser. H3-diversitet opprettholdes mellom vanlige kandidater; et matchet rammeverkspar deler bevisst H3. Det er ingen offentlig regel som krever at alle nye lagkandidater har ulike H3-er; det er fullsekvensene som er ulike her. Hele panelet valideres samlet. De valgte VHH-ene har svak støtte for riktig bindingsflate. Den ene ligger dessuten svært nær70%-grensen mot et kjent antistoff. **De to plassene er derfor eksplorative, og global novelty kan ikke regnes som ferdig bekreftet.**

En sekundær Gaussian-process-modell er kontrollert med samme fem sekvensklynsefold som hovedmodellen. Kjerneparametere ble lært inne i hver treningsfold. Den gir omtrent samme rangering og litt lavere MSE, uten bevis på sikker overføring til nye konstruksjoner. Dette er en sensitivitetstest valgt underveis, ikke en urørt slutt-test av modellvalg. De empiriske95%-kvantilene for absolutt holdt-ute log10-KD-feil er rundt1,7–1,8: store feil er mulige. Bootstrap-spredningen i parametere kan derfor ikke vises som et snevert biologisk konfidensintervall. Modellene overpredikerer også historisk WT-KD; de er bedre egnet til prioritering enn absolutte affinitetsløfter.

**OpenDDE-kontrollen feiler på WT:** full-context WT gjenfinner bare2 av19 native kontakter. Negative OpenDDE-resultater kan derfor ikke være et hardt avvisningsfilter. Positive sammenfall brukes som ekstra geometrisk støtte, med tydelig begrensning. Mol1-WT gjenfinner19 av19.

En lokal Apheris Boltz-2-kontroll er også gjennomført på H100, med full607-sekvens, HER2-template uten antistoffkoordinater, eksplisitt ingen MSA og seed271828. Alle fem konstruksjoner ble beregnet. Også her sviktet WT-dokkingen (0 av19 kontakter), så negative resultater brukes ikke som avvisning. Rammeverksvarianten av `newML_b973259db36d` traff19 av19; dette støtter en geometrisk hypotese og beviser verken binding eller varmestabilitet. pLDDT og globalipTM er fortsatt bare modellskårer.

For lokal kjøring måtte vi bevare HER2s fulle `_entity_poly_seq` i den eksperimentelle templaten, bruke en skrivbar Numba-cache og en skrivbar hjemmekatalog inne i containeren. Tidligere forsøk stoppet før gyldige prediksjoner og er bevart separat. Ingen modellvekter ble endret. GPU-låsen hindret konflikt med andre på VM-en. Den lokale jobben er en annen kontekst enn Mol1/OpenDDE, og skårene blandes ikke numerisk.
'''
 (OUT/'LES_MEG.md').write_text(text+extra)
 hashes={str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json'};(OUT/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=2))
 print(json.dumps({'output':str(OUT),'evaluated':len(good),'pending_jobs':len(pending),'files':len(hashes)}))

if __name__=='__main__':main()
