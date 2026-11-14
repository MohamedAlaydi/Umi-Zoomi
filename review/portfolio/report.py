"""Prepare an18+2 decision brief, transparent run coverage and provisional rank files."""
import argparse,csv,hashlib,json,shutil
from datetime import datetime,timezone,timedelta
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from prepare import ROOT,RUN,PREVIOUS,write_csv,pair_hash


def read(p):return json.loads(p.read_text())
def table(p):return list(csv.DictReader(p.open()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path);out=parser.parse_args().output
    out.mkdir(parents=True,exist_ok=True)
    evidence=read(RUN/'common-evidence.json');summary=read(RUN/'coverage-summary.json');rows=read(RUN/'candidates.json')
    assert summary['completed_common_rows']==42 and summary['validation']['n_valid']==20
    assert all(v['status']=='ok' for v in evidence)
    candidates={r['query']:r for r in rows};coverage={r['query']:r for r in table(RUN/'score-coverage.csv')}
    for row in evidence:assert sha(ROOT/row['structure'])==row['structure_sha256']
    artifacts=0
    for directory in RUN.glob('common-*'):
        if not directory.is_dir():continue
        receipt=read(directory/'download_receipt.json');assert sha(directory/'artifacts.zip')==receipt['archive_sha256']
        for item in receipt['artifacts']:
            assert sha(directory/'artifacts'/item['path'])==item['sha256'];artifacts+=1
    opts=[r['query'] for r in rows if r['format']=='Fab'];dn=[r['query'] for r in rows if r['format']=='VHH']
    # A qualitative update within the frozen20, with reasons rather than an opaque weighted score.
    opt_order=['anas_007','anas_003']+[q for q in opts if q not in ['anas_007','anas_003']]
    chosen={'anas_007':'Highest original combined sequence/contact lead; Mol1 and OpenDDE retain whole reference epitope.',
        'anas_003':'Promoted after common scoring: BLOSUM37, both models support the interface; existing binding-ddG negative. This remains a prospective hypothesis.'}
    rank_files=[]
    for label,order in [('18plus2_begge_spor_topp4',opt_order[:2]+dn+opt_order[2:]),
                        ('18plus2_optimalisering_topp4',opt_order[:4]+dn+opt_order[4:])]:
        ranked=[]
        for i,q in enumerate(order,1):
            r=candidates[q];ranked.append(dict(rank=i,query=q,requested_track=r['requested_track'],format=r['format'],
                heavy_variable=r['heavy_variable'],light_variable=r['light_variable'],pair_sha256=r['pair_sha256'],
                evidence_reason=chosen.get(q,r['selection_reason']),status='provisional; not submitted to Adaptyv; final track subject to organisers'))
        write_csv(out/(label+'.csv'),ranked);rank_files.append(label+'.csv')
    pool={r['pair_sha256'] for r in rows}
    for name in rank_files:
        proposed=table(out/name)
        assert len(proposed)==20 and {r['pair_sha256'] for r in proposed}==pool
        assert all(pair_hash(r['heavy_variable'],r['light_variable'])==r['pair_sha256'] for r in proposed)
    strategy={label:[{'rank':i+1,'query':q} for i,q in enumerate(order)] for label,order in [
        ('both_tracks_top4',opt_order[:2]+dn+opt_order[2:]),('optimisation_top4',opt_order[:4]+dn+opt_order[4:]) ]}
    provided=read(PREVIOUS/'provided-HER2-reference-check.json');h3={r['candidate']:r for r in provided['candidates']}
    ddg_summary=summary['binding_ddg_controls'];billed=sum(read(p)['amount'] for p in RUN.glob('common-*/usage.json'))
    stamp=datetime.now(timezone(timedelta(hours=1))).strftime('%d.%m.%Y kl.%H:%M Oslo')
    md=f'''#18 optimaliseringer +2 de novo: anbefalt behandling

Oppdatert {stamp}. Dette er et konkret forslag innenfor de samme20 fullsekvensene. Ingen labinnsending er gjort av denne chatten.

**18+2 er tillatt. Rekkefølgen avgjør hvilke design som faktisk blir laget.** Oppgavebeskrivelsen s.7–8 tillater valgfri blanding av spor og ber om én rangert liste med opptil20 design. Dere har4 garanterte laboratorieplasser, ikke20. Øvrige plasser avhenger av pitch og dommernominasjoner. Hvert design får sitt spor bestemt av valideringen; formatet VHH gjør det ikke automatisk de novo. [Oppgaven](source_rules/challenge.pdf).

## Min anbefaling for målet om å teste begge spor

Plasser to optimaliseringer og de to de novo-forslagene på plass1–4. Da blir begge spor representert i de fire garanterte plassene, forutsatt endelig aksept. Dette er et bevisst valg av18 sterke optimaliseringshypoteser og2 mer usikre, utforskende VHH-er. Dersom målet først og fremst er størst mulig antall vellykkede labdesign, har optimaliseringene betydelig sterkere modellstøtte i dag.

| Plass | Kandidat | Spor | Begrunnelse og usikkerhet |
|---:|---|---|---|
|1|anas_007|optimalisering|Opprinnelig lead; seks lokale Boltz2-seeds og begge nye modeller støtter omtrent samme flate. Ingen ny målt KD eller Tm.|
|2|anas_003|optimalisering|Løftet fra den tidligere plass8: BLOSUM37, lav kontakt-PAE i begge blinde modellene, og binding-ddG−0.514±0.156kcal/mol i en eksisterende kjøring. MC-feilen er ikke modellens prediksjonsfeil.|
|3|novel2 / originalt design12|de novo, foreslått|Best monomer-foldsamsvar av tre: NBB2 CA-RMSD1.14Å. De blinde modellene gjenfinner ingen av de19 referanse-epitoprestene. Mulig CDRH3-glykosyleringsmotiv.|
|4|novel3 / originalt design2|de novo, foreslått|Sterkest relativ epitopehypotese blant VHH-ene: Mol1 gjenfinner8/19 både kort og lang HER2. Samtidig er H3 svært usikker: NBB2 H3-RMSD15.0Å etter rammeverkstilpasning.|

Novel2 og novel3 tester to forskjellige usikre hypoteser, henholdsvis fold og mulig bindingssted. De er ikke dokumenterte bindere. Novel1 er reserve fordi det ikke har kombinasjonen av bedre monomer-fold eller mer konsistent epitopehypotese enn disse to.

Hvis dere vil beskytte alle fire første plasser til optimalisering, bruk alternativfilen som legger VHH-ene på plass5–6. Med bare4 tildelte labtester blir ingen VHH da testet. **Ikke legg VHH-ene på19–20 hvis dere vil regne med eksperimentell deltakelse i begge spor:** selv en pitchvinner får i utgangspunktet16 tester.

| Antall tildelte labtester N | Begge spor i topp4 | Optimalisering i topp4 |
|---:|---|---|
|4|2 optimalisering +2 de novo|4 optimalisering +0 de novo|
|6|4 optimalisering +2 de novo|4 optimalisering +2 de novo|
|8|6 optimalisering +2 de novo|6 optimalisering +2 de novo|
|12|10 optimalisering +2 de novo|10 optimalisering +2 de novo|
|16|14 optimalisering +2 de novo|14 optimalisering +2 de novo|
|20|18 optimalisering +2 de novo|18 optimalisering +2 de novo|

Den tidligere sammenligningen anas_015 mot anas_009 ligger samlet på plass5–6 i forslaget med begge spor i topp4. Dermed kan den fortsatt bli et konkret laboratorieeksperiment ved minst6 tildelte tester. Hele utvalget på18 Fab-er er uendret; bare rekkefølgen er oppdatert etter de felles modellkontrollene. De to Fab-ene fra den gamle20-listen som er ute, er anas_032 og anas_027, de tidligere plass19 og20.

## Hva som er kjørt på akkurat disse20

**Nå har hele panelet samme grunnleggende Mol1- og OpenDDE-sammenligning.** Jeg supplerte den tidligere VHH-kampanjen med36 nye prediksjoner for de18 Fab-ene, og gjenbrukte6 identiske tidligere VHH-/WT-resultater. Totalt42 felles vurderinger:20 kandidater +1 WT-kontroll, med2 modeller. Samme ekte HER2-sekvens på119 aminosyrer, seed42, ett sample per modell og ingen oppgitt strukturell mal eller hotspot. Én prediksjon per modell gir ingen presis usikkerhetsfordeling. Modellene kan dele treningskunnskap og er ikke to uavhengige labforsøk.

| Sjekk |18 Fab-optimaliseringer|2 VHH-forslag|Tolkning|
|---|---|---|---|
|Installert abguard, eksplisitt referanse|18/18 består|2/2 består|Sekvens-/formatfilter; endelig typeavhengig nearest-known-status må bekreftes av arrangørens løsning.|
|Lokal Boltz2 med felles mal|6 seeds per kandidat|ikke brukt på VHH-ene|Robusthet innen samme modell og mal, ikke seks uavhengige metoder.|
|FACS-modell|Eksisterende skår der tilgjengelig|ikke anvendelig|Trastuzumab-familieskår; ikke kalibrert bindersannsynlighet for nye VHH-er.|
|Mol1 blind cofold|18/18 ferdige|2/2 ferdige|Felles kort HER2-kontekst og WT-kontroll; mål på strukturstøtte.|
|OpenDDE AbAg blind cofold|18/18 ferdige|2/2 ferdige|Ekstra antistoff–antigen-modell; uenighet bevares.|
|OpenFold3|Ingen nye fra denne paneletappen|Begge i kort og lang kontekst|Tidligere VHH-diagnostikk, med svak WT-epitopegjenfinning.|
|AF2-IG|Ikke kjørt her på Fab-ene|Begge kjørt|Gitt designpose: holder interfacet seg? Det er en betinget sjekk.|
|NanoBodyBuilder2|Ikke kjørt på Fab-format|Begge, fire unrefined og ett refined resultat|Monomer-fold og loopusikkerhet; ingen antigenmodell.|
|StaB binding-ddG|9/18 har tidligere resultater|Ikke en egnet WT-mutant-sammenligning|Predikert endring i binding, ikke termisk stabilitet.|
|SoluProt / NetSolP / Aggrescan3D|Ingen bekreftede resultater i vårt utvalg|Ingen bekreftede resultater|Anbefalt uttrykks-/aggregeringsscreening i oppgaven; skal ikke merkes som bestått.|
|Nye Adaptyv-labmålinger|0|0|Kommer etter innsending/utvalg.|

717 tidligere råfiler ble hashkontrollert før gjenbruk. De36 nye modellresultatene er lastet ned og hashkontrollert.20/20 sekvenser består den installerte eksplisitte referansevalideringen. To nye regresjonstester verifiserer kjederoller og kontakt-PAE, også når antigen står først eller residue-ID-er ikke er sekvensielle. Ved ingen kontakt beholdes interface-PAE som ukjent, ikke0.

## Hva de nye felles kjøringene viser

Mol1 gjenfinner19/19 referanse-epitoprester for alle18 Fab-er, med Jaccard omtrent0.655–0.826 og kontakt-PAE omtrent1.5–3.6Å. WT har18/19 og Jaccard0.783. Dette støtter at Fab-ene kan beholde området, men betyr ikke at alle binder bedre enn WT: kontaktgjenfinning måler verken KD eller en konkurransekurve.

OpenDDE har større sprik. For eksempel har anas_003 kontakt-PAE2.69Å, mens anas_015 har13.89Å. WT gjenfinner også bare7/19 med OpenDDE; derfor er dette et flagg om modelluenighet, ikke et automatisk avslag. Rangeringen prioriterer kandidater med flere støttende observasjoner, men ingen samlet poengsum fra ukalibrerte råskårer er laget.

For VHH-ene er kort-kontekst Mol1-ipTM0.124 og0.190; OpenDDE0.245 og0.217. GlobalipTM fra Fab og VHH kan ikke sammenlignes direkte fordi Fab også har et sterkt tung-/lettkjedeinterface. Kontaktgeometri og antigen-spesifikk PAE er derfor med i tabellen. AF2-IG ga også svake interfaceverdier for begge. Et valgt de novo-design er her et utforskende forsøk, ikke et lovende treff bevist av mange modellnavn.

StaB-ddG-kontrollene har Spearman rho{ddg_summary['spearman_rho']:.3f} på8 utvalgte historiske kontrollvarianter. Det er støtte til å lese denne skåren som en ekstra bindinghypotese, men for få og for utvalgte data til presis individuell prediksjon.9 av18 Fab-er har score; manglende score er ikke satt til null. Foreslåtte kandidater har fortsatt ingen ny, eksperimentelt målt KD.

Begge VHH-ene er undersøkt direkte mot alle525063 CDRH3-er i de to oppgitte HER2-tabellene. Minste IMGT-editavstand er11 for novel2 og18 for novel3. De har også under70% fullsekvensidentitet til våre hentede kjente antistoffreferanser og0 RCSB-treff ved70%-grensen. Denne begrensede referansedekningen kan ikke erstatte arrangørens komplette typeavhengige antistoffdatabase.

## JapanFold, Nebius og Adaptyv er forskjellige ting

JapanFold er en modellplattform. På den har vi brukt BoltzGen til å lage design og OpenFold3, Mol1, OpenDDE og AF2-IG til ulike struktursjekker. Nebius ga NanoBodyBuilder2 og AntiFold, mens lokale Apheris-modeller sto for RFD4-design og Boltz2-sjekker. Adaptyv er laboratoriet, som etter utvalg skal uttrykke designene og måle HER2-binding med SPR, konkurranse med trastuzumab og termisk stabilitet mot en samtidig målt WT-kontroll. WT-kontrollen i beregningene kommer i tillegg til de20 innsendingskandidatene; den bruker ikke en av våre20 designplasser. [Oppgaven s.8](source_rules/challenge.pdf), [offisiell FAQ](https://oslo-ai-antibodies-hackathon.vercel.app/).

Hvis «adapty» betyr Adaptyvs tidligere konkurransepipeline: oppgaven viser til erfaringer med Aggrescan3D, SoluProt, NetSolP og ProteinMPNN med løselige vekter. Disse erfaringene er relevante for å velge hvilke proteiner som kan uttrykkes, men det er andre data, mål og proteiner enn nye HER2-resultater. Vi har ikke slike uttrykksprediksjoner for hele panelet. [Primærstudien om Adaptyvs EGFR-konkurranse](https://www.biorxiv.org/content/10.1101/2025.04.17.648362v2.full).

Hvis «adapty» betyr adaptive kjøringer: ja, designarbeidet endret retning etter funn. De første hosted designene manglet kanoniske Cys, så vi gikk til antistoffspesifikke RFD4-oppsett; deretter helsekvensnyhet, uavhengig refolding og AntiFold. AntiFold-runden ble stoppet da alle16 sekvensene gikk tilbake mot kjente antistoffer. Dette er adaptiv forsøksplanlegging basert på beregninger, ikke en labbasert læringssløyfe eller en ferdig bayesiansk optimaliserer.

## Slik leses de tidligere fire figurpanelene

|Panel|Hva det viser|Hva det ikke beviser|
|---|---|---|
|A:96 designsekvenser|80 komplekser +16 AntiFold-varianter i ulike armer. 15 Cys-varianter og20 gamle kontroller er separat.|96 bindere eller96 uavhengige eksperimenter.|
|B:epitopegjenfinning|Om modellen plasserer binderen ved de19 referanserestene. WT viser hva hver modell klarer.|Målt konkurranse med trastuzumab eller bedre KD.|
|C:NAC mot historisk KD|En CA-basert rammeverk-konfidensskår mot25 reelle historiske KD-er; gjentatte seeds samles per konstruksjon.|At høy pLDDT betyr binding, at metoden er bedre enn ipTM, eller at resultatet overfører til nye VHH-er.|
|D:AntiFold-score mot nyhet|Alle16 får bedre betinget likelihood, men over70% identitet til et kjent antistoff.|At en modelloptimalisert sekvens er en god de novo-innsending. De16 ble holdt tilbake.|

## De viktigste tallene

- pLDDT: modellens tillit til lokal struktur. Det er ikke en sannsynlighet for HER2-binding.
- ipTM: tillit til kjeders relative plassering. Global score kan skjule hvilket interface som er godt.
- PAE: usikkerhet i relativ posisjon, iÅ; lavere er bedre. Her rapporteres symmetrisk PAE for faktiske kontaktresiduepar ved4.5Å.
- RMSD: hvor langt en struktur avviker etter en definert tilpasning, iÅ. En VHH kan ha god rammeverks-RMSD og ustabil H3.
- Recall: hvor mange av de19 referanserestene som berøres. Jaccard: overlapp delt på alle kontaktrester i modell eller referanse; ekstra kontakter trekker ned.
- Binding-ddG: predikert endring i bindingsfri energi for mutasjoner mot WT. Monte Carlo-feil beskriver beregningssampling, ikke total prediksjonsusikkerhet.
- Tm: termisk måling. Ingen av disse struktur- eller likelihood-skårene er Tm.

## Praktisk før innlevering

1. Velg én global rekkefølge av20; bruk varianten med begge spor i topp4 hvis begge skal være garantert representert i laboratoriet.
2. Frys eksakte VH/VL-/VHH-sekvenser og SHA-hasher. Endrer dere en sekvens, må novelty og relevante modeller kjøres på nytt.
3. Kjør arrangørens endelige validering og sjekk faktisk track. Våre to VHH-er er foreslått som de novo; det er ikke teamets etikett som avgjør.
4. Oppgi rang, format, kjeder, begrunnelse og hva hvert forsøk skal lære. Skill predikert risiko fra målt resultat i pitch og repo.
5. Følg de tre biologiske endepunktene separat: HER2-SPR, konkurranse mot WT og termisk stabilitet. Labresultater kommer senere.

Pitchvurderingen er40% begrunnelse,20% reproduserbar gjennomføring,20% brukerbehov og20% vei til praktisk verdi. Både den høye usikkerheten til de novo-valgene og modelluenigheten er derfor del av beslutningsgrunnlaget. [Offisiell FAQ](https://oslo-ai-antibodies-hackathon.vercel.app/).

## Leveranser

-`18plus2_begge_spor_topp4.csv`: foreslått rekkefølge for deltakelse i begge spor fra de fire første labplassene.
-`18plus2_optimalisering_topp4.csv`: alternativ med fire optimaliseringer først og VHH på5–6.
-`score-coverage.csv`:20 rader med hvilke kjøringer og resultater som finnes, og hvilke som mangler.
-`felles-modellkontroll.png`: felles Mol1-/OpenDDE-sammenligning for hele panelet og WT.
-`tidligere-denovo-kampanje.png`: den tidligere firepanelsfiguren forklart over.
-`evidence/` og`source/`: kvitteringer og kildekode. Full modelloutput beholdes i teamprosjektets run012 og gjenbrukte run011.

Nye JapanFold-kjøringer for de18 Fab-ene kostet${billed:.6f}. Dette inkluderer ikke de tidligere kjøringene, Nebius eller lokalGPU. Ingen ny betalt labbestilling er gjort.
'''
    # Restore ordinary spacing in prose while leaving protein/model identifiers intact.
    import re
    for word in ['de','alle','for','på','med','og','har','er','ikke','bare','mot','under','over','plass','design','første','samme','blir','rundt','fra','til','i','ved','omtrent','rho']:
        md=re.sub(r'\b'+word+r'(?=\d)',word+' ',md)
    md=md.replace('#18','# 18').replace('\n-`','\n- `').replace('iÅ','i Å').replace('mot1','mot 1').replace('negative. This','negative. This')
    (out/'LES_DETTE_18_PLUS_2.md').write_text(md)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    ordered=['trastuzumab_wt']+opt_order+dn;short={r['query']:r.get('short_name',r['query']) for r in rows}
    z=[];pae=[]
    for q in ordered:
        vals=[next(v for v in evidence if v['candidate']==q and v['model']==m) for m in ['mol1','opendde-abag']]
        z.append([v['epitope_jaccard_4.5'] for v in vals]);pae.append([v['mean_contact_pair_symmetric_PAE_A'] for v in vals])
    z=np.array(z);pae=np.array(pae,dtype=float);labels=['WT Fab control']+[short.get(q,q)+(' [VHH]' if q in dn else '') for q in ordered[1:]]
    fig,(a,b)=plt.subplots(1,2,figsize=(10,11.3),gridspec_kw={'width_ratios':[1,1]});fig.subplots_adjust(left=.27,right=.94,bottom=.11,top=.83,wspace=.45)
    im=a.imshow(z,aspect='auto',vmin=0,vmax=1,cmap='YlGnBu');ip=b.imshow(pae,aspect='auto',vmin=0,vmax=25,cmap='YlOrRd')
    for axis,data in [(a,z),(b,pae)]:
        axis.set_xticks([0,1],['Mol-1','OpenDDE AbAg']);axis.xaxis.tick_top();axis.tick_params(axis='both',length=0)
        axis.set_yticks(range(len(labels)),labels if axis==a else ['']*len(labels));axis.axhline(.5,color='white',lw=3);axis.axhline(18.5,color='white',lw=3)
        for (i,j),v in np.ndenumerate(data):axis.text(j,i,f'{v:.2f}' if axis==a else f'{v:.1f}',ha='center',va='center',fontsize=9,color='white' if (axis==a and v>.55) or (axis==b and v>14) else '#152438')
        axis.spines[['left','right','bottom','top']].set_visible(False)
    a.set_title('Epitope Jaccard ↑',pad=34);b.set_title('Contact-pair PAE [Å] ↓',pad=34)
    fig.suptitle('18 optimisation designs + 2 exploratory VHHs',fontsize=17,fontweight='bold',y=.97)
    fig.text(.27,.925,'HER2 119 aa · seed 42 · one sample/model · no input template or hotspot',fontsize=9)
    fig.text(.06,.038,'Model geometry and confidence, not measured affinity or competition.\nWithin-format interpretation: Fab and VHH contact footprints can differ. One prediction/model is not a confidence interval.\nWT: Mol-1 recovers 18/19 reference residues; OpenDDE 7/19. No new Adaptyv results.',fontsize=9)
    fig.savefig(out/'felles-modellkontroll.png',dpi=180,facecolor='white');fig.savefig(out/'felles-modellkontroll.pdf',facecolor='white');plt.close(fig)
    shutil.copy2(out.parent/'denovo-campaign/campaign-evidence.png',out/'tidligere-denovo-kampanje.png')
    shutil.copy2(RUN/'score-coverage.csv',out/'score-coverage.csv')
    sources=out/'source';sources.mkdir(exist_ok=True)
    for p in Path(__file__).parent.glob('*.py'):shutil.copy2(p,sources/p.name)
    rules=out/'source_rules';rules.mkdir(exist_ok=True)
    shutil.copy2(ROOT/'review/organizer/ai-antibodies-hackathon-apheris.pdf',rules/'challenge.pdf')
    ev=out/'evidence';ev.mkdir(exist_ok=True)
    for n in ['coverage-summary.json','common-evidence.json','predeclared.json','manifest.json','candidates.json','contact-tests.log']:
        shutil.copy2(RUN/n,ev/n)
    for n in ['explicit-reference-receipt.json','novelty-reference-checked.csv','validated-reference-checked.csv']:
        shutil.copy2(RUN/'validation'/n,ev/('validation-'+n))
    for folder in RUN.glob('common-*'):
        if not folder.is_dir():continue
        for n in ['submission.json','download_receipt.json','usage.json','request.json']:
            shutil.copy2(folder/n,ev/(folder.name+'__'+n))
    audit=dict(passed=True,completed_utc=datetime.now(timezone.utc).isoformat(),candidate_count=20,format_counts={'Fab':18,'VHH':2},
        complete_model_rows=42,new_model_rows=36,reused_model_rows=6,accepted_by_installed_reference_validator=20,
        prior_raw_file_hashes_verified=717,new_artifact_hashes_verified=artifacts,
        same20_sequences_in_both_rankings=True,regression_tests_passed=2,new_Adaptyv_lab_results=0,
        decisions=strategy,run_source='runs/012-codex-18plus2 with explicit run011 reuse',billed_JapanFold_usd=billed)
    (out/'audit.json').write_text(json.dumps(audit,indent=2))
    (RUN/'decision.json').write_text(json.dumps(audit,indent=2))
    (out/'README.md').write_text('Start with LES_DETTE_18_PLUS_2.md. Both rank files are proposals over the same frozen18Fab/2VHH panel, with full sequences and hashes. The score-coverage.csv marks missing work explicitly. No new lab results or lab submission is claimed. The source report builder depends on the existing team14 project and run011 data.\n')
    manifest=''.join(sha(p)+'  '+str(p.relative_to(out))+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='SHA256SUMS')
    (out/'SHA256SUMS').write_text(manifest)
    print(json.dumps(audit,indent=2))

if __name__=='__main__':main()
