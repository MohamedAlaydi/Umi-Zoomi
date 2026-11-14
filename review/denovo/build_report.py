"""Build the judge-facing report from frozen campaign evidence; never submits jobs."""
import argparse,base64,csv,hashlib,html,json,shutil
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from biotite.structure.io.pdb import PDBFile
from collect_campaign import ROOT,RUN,EPITOPE
from collect_refolds import ca,align


def read(name):return json.loads((RUN/name).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(path):return list(csv.DictReader(path.open()))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    sources=out/'source';sources.mkdir(exist_ok=True)
    for p in Path(__file__).parent.glob('*.py'):shutil.copy2(p,sources/p.name)
    for name in ['her2_pilot_target.fasta','her2_pilot_residue_map.csv','target_preparation.json','rcsb_1n8z_her2_mapping.json','requirements.txt']:
        shutil.copy2(Path(__file__).parent/name,sources/name)
    local={r['query']:r for r in read('local-candidates.json')};selected=read('nanobodybuilder-inputs.json')
    liab={r['sequence_id']:r for r in read('abguard-final/liabilities.json')}
    identity={r['query']:r for r in read('local-final-known-identity.json')}
    nbb={r['candidate']:r for r in read('nanobodybuilder-evidence.json')}
    evidence=read('local-refold-evidence.json');cal=read('regional-calibration.json')
    usage=read('japanfold-usage-ledger.json');audit=read('quality-audit.json');ab=read('abguard-final/explicit-reference-receipt.json')
    provided=read('provided-HER2-reference-check.json');provided_by_id={r['candidate']:r for r in provided['candidates']}
    generated=read('pilot-candidates.json');anti=read('antifold-candidates.json');antiid={r['query']:r for r in read('antifold-final-known-identity.json')}
    completed=datetime.now(timezone.utc).isoformat()
    candidates=[]
    for item in selected:
        key=item['candidate'];row=local[key];final=next(m for m in nbb[key]['models'] if m['native_file']=='final_model.pdb')
        candidates.append(dict(name=item['name'],sequence_id=key,heavy_sequence=row['heavy_variable'],light_sequence='',kind='vhh',
            length=row['length'],installed_abguard_valid=liab[key]['is_valid'],installed_abguard_class=liab[key]['novelty_class'],
            nearest_CDRH3_distance=liab[key]['cdrh3_min_distance'],
            min_CDRH3_distance_to_provided525063=provided_by_id[key]['min_distance_provided_imgt'],small_reference_max_identity=identity[key]['best']['identity_over_alignment'],
            small_reference_nearest=identity[key]['best']['reference'],RCSB_hits_at70percent=0,
            generation_epitope_recall=row['footprint']['4.5']['recall'],NBB2_final_all_CA_rmsd=final['all_CA_rmsd_after_self_fit'],
            NBB2_final_CDRH3_CA_rmsd=final['CA_rmsd_after_framework_fit']['cdr3'],
            n_high_severity_motifs=liab[key]['n_high_severity'],motifs='; '.join(x['tag']+':'+x['motif'] for x in liab[key]['liabilities']),
            binding_evidence='UNSUPPORTED; independent docking weak; no measurement',
            submission_status='EXPLORATORY_RESERVE; preserve existing optimization panel',
            sequence_sha256=row['sequence_sha256'],source_structure=row['structure']))
    candidates.sort(key=lambda r:r['NBB2_final_all_CA_rmsd'])
    with (out/'exploratory-candidates.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(candidates[0]));w.writeheader();w.writerows(candidates)
    aggregate=dict(completed_utc=completed,campaign=read('campaign.json'),candidates=candidates,
        cofolds=evidence,calibration={k:v for k,v in cal.items() if k!='input_hashes'},
        abguard=ab,provided_HER2_check=provided,quality_audit=audit,JapanFold_usage=usage,
        claims={'measured_binding_improvement':False,'measured_Tm_improvement':False,'universal_antibody_novelty_proven':False,
                'installed_validator_pass_for_three_reserves':True,'prospective_wet_lab_samples':0})
    (out/'evidence.json').write_text(json.dumps(aggregate,indent=2))
    # Static, exportable scientific figure. Repeated seeds are aggregated per construct.
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,2,figsize=(13,9.1));fig.patch.set_facecolor('#f5f7fa')
    ax=axes[0,0];counts=[16,16,16,16,16,16];names=['BoltzGen\ndirected','BoltzGen\nblind','RFD4 fixed\nCDR1–3','RFD4 fixed\nlong H3','RFD4\nvariable k1','RFD4\nvariable k2']
    # The first two hosted arms each have eight; the seventh arm is AntiFold16.
    counts=[8,8,16,16,16,16,16];names+=['AntiFold\nCDR opt.']
    ax.bar(range(7),counts,color=['#86a8b5','#b7c7d1','#66849b','#66849b','#12a88b','#66849b','#c28d47'])
    ax.set_xticks(range(7),names,fontsize=8);ax.set_ylim(0,22);ax.set_yticks([0,4,8,12,16,20]);ax.set_ylabel('New sequence designs')
    ax.set_title('A  96 new sequences across seven arms',loc='left',fontweight='bold')
    for i,n in enumerate(counts):ax.text(i,n+.3,str(n),ha='center')
    ax.text(.02,.97,'80 generated complexes + 16 sequence variants\n15 Cys diagnostics and 20 old controls are separate',transform=ax.transAxes,va='top',fontsize=9)
    ax=axes[0,1];models=['openfold3','mol1','opendde-abag'];labels=['OpenFold3','Mol-1','OpenDDE AbAg'];xx=np.arange(3)
    for i,item in enumerate(selected):
        vals=[next(r['epitope_recall_4.5'] for r in evidence if r['model']==m and r['name']==item['name']+'_crop119') for m in models]
        ax.scatter(xx+(i-1)*.11,vals,s=56,label=item['name'],alpha=.9)
    wt=[next(r['epitope_recall_4.5'] for r in evidence if r['model']==m and r['name']=='trastuzumab_wt_control') for m in models]
    ax.plot(xx,wt,'D--',color='#176e5a',label='Trastuzumab WT Fab',markersize=7)
    ax.set_xticks(xx,labels);ax.set_ylim(-.05,1.07);ax.set_ylabel('Fraction of 19 WT epitope residues contacted')
    ax.set_title('B  Blind docking needs a matched positive control',loc='left',fontweight='bold');ax.legend(fontsize=8,loc='upper left')
    ax.text(.59,.94,'Crop119 · 4.5 Å contacts\nNot a binding measurement',transform=ax.transAxes,fontsize=8,va='top')
    ax=axes[1,0];rows=[r for r in table(RUN/'regional-calibration.csv') if r['kd_nM'] and float(r['kd_nM'])>0]
    ax.scatter([float(r['ca_nac']) for r in rows],[np.log10(float(r['kd_nM'])) for r in rows],c='#247b9b',s=38,edgecolors='white')
    stat=cal['statistics']['ca_nac'];ax.set_xlabel('Framework CA pLDDT (CA-based NAC adaptation)');ax.set_ylabel('log10 measured KD [nM]')
    ax.set_title('C  Calibration uses real historical affinity',loc='left',fontweight='bold')
    ax.text(.02,.98,f"25 constructs, 3 seeds each\nSpearman ρ = {stat['rho_log10_KD']:.3f}\n95% bootstrap CI [{stat['bootstrap_ci95'][0]:.3f}, {stat['bootstrap_ci95'][1]:.3f}]",transform=ax.transAxes,va='top',fontsize=9)
    ax.text(.02,.03,'Related variants; selected retrospective panel.\nNo proven advantage over ipTM; paired CI spans zero.',transform=ax.transAxes,fontsize=8)
    ax=axes[1,1]
    ax.scatter([antiid[r['query']]['best']['identity_over_alignment']*100 for r in anti],[r['conditional_cdr_nll'] for r in anti],s=45,c='#bd8442',label='16 AntiFold variants')
    parent='rfd4-variable-sequence-k1__her2_variable_sequence_12_generated'
    ax.scatter([identity[parent]['best']['identity_over_alignment']*100],[anti[0]['parent_conditional_cdr_nll']],marker='*',s=180,c='#12a88b',label='Novel2 parent')
    ax.axvline(70,c='#b64b4b',linestyle='--');ax.set_xlim(66,75);ax.set_xlabel('Nearest known identity in same reference subset [%]');ax.set_ylabel('CDR conditional negative log-likelihood ↓')
    ax.set_title('D  Better likelihood can erase novelty',loc='left',fontweight='bold');ax.legend(fontsize=9)
    ax.text(.03,.48,'All 16 pass installed abguard\nbut exceed 70% identity to a known antibody.\nHeld back from de novo submission.',transform=ax.transAxes,fontsize=9)
    fig.suptitle('HER2 • an evidence-driven antibody design campaign',fontsize=19,x=.055,ha='left',fontweight='bold')
    fig.text(.055,.015,'No new experimental affinity, competition or thermal stability measurements. Computational evidence and retrospective calibration only.',fontsize=9,color='#415367')
    fig.tight_layout(rect=[.025,.04,.99,.95],h_pad=3,w_pad=3)
    fig.savefig(out/'campaign-evidence.png',dpi=190,facecolor=fig.get_facecolor());fig.savefig(out/'campaign-evidence.pdf',facecolor=fig.get_facecolor());plt.close(fig)
    # Compact offline CA-trace viewer: all comparisons are aligned on the same target.
    viewers={}
    for item in selected:
        row=local[item['candidate']];d=ca(ROOT/row['structure']);target=np.concatenate([d['C'],d['D']]);center=target.mean(axis=0)
        points=lambda a:np.round(a-center,3).tolist()
        trace=dict(target=points(target),target_ids=list(range(1,93))+list(range(103,120)),design=points(d['H']))
        final=next(m for m in nbb[item['candidate']]['models'] if m['native_file']=='final_model.pdb')
        atoms=PDBFile.read(ROOT/final['path']).get_structure(model=1);a=atoms.coord[atoms.atom_name=='CA'];r,o=align(a,d['H']);trace['NBB2_self_aligned']=points(a@r+o)
        for model in models+['af2ig']:
            entry=next(e for e in evidence if e['model']==model and e['name']==item['name']+'_crop119')
            atoms=ca(ROOT/entry['structure']);ag=atoms[entry['chain_roles']['T']];idx=np.array(list(range(92))+list(range(102,119)))
            r,o=align(ag[idx],target);trace[model]=points(atoms[entry['chain_roles']['H']]@r+o)
        viewers[item['name']]=trace
    (out/'viewer-data.json').write_text(json.dumps(viewers,separators=(',',':')))
    md=f'''# HER2 de novo: gjennomført kampanje og beslutning

Oppdatert {completed}. Implementert i teamprosjektets `review/denovo/` og `runs/011-codex-denovo-vhh/`.

**Vi har gjennomført en større designkampanje, men har ikke dokumentert en ny HER2-binder.** Tre VHH-er består den installerte abguard-byggets de novo-regler og vår ekstra sekvensscreening. Uavhengige strukturmodeller gir fortsatt svak støtte til de ønskede bindingsposene. Behold den eksisterende Fab-optimaliseringsserien som hovedcase og presenter VHH-ene som eksperimentelle reserver.

## Hva som faktisk er gjort

- 80 genererte komplekser: 16 BoltzGen og 64 lokale RFD4-antistoffdesign, fordelt på to hosted og fire lokale armer. I tillegg 16 AntiFold-varianter med uendret nytt rammeverk: **96 nye designsekvenser**.
- 15 eksplisitte Cys-varianter var diagnostikk, og 20 eksisterende Fab-par var kontroller. Disse telles ikke som 35 ekstra de novo-funn.
- **131 innsendte sekvenser til lokal abguard; 127 består**, inkludert alle 20 gamle Fab-par. Ingen duplikate ID-er eller konstruksjoner. Referanseindeksen inneholder 610109 CDRH3-er.
- 48 kompleksprediksjoner er ferdige: 16 prediksjoner av fire original/Cys-par gjennom to modeller, 27 blinde cofolds og 5 designbetingede AF2-IG-sjekker. NanoBodyBuilder2 ga 5 modeller per VHH, totalt 15 modeller for 3 sekvenser.
- En eksisterende fullført teamkjøring med 30 SPR-konstruksjoner og 3 Boltz2-seeds per konstruksjon ble analysert på nytt. Dette er 90 modeller, men **25 kvantifiserte eksperimentelle KD-er**, ikke 90 uavhengige målinger.
- {audit['n_checks']} datakontroller og 8 nye regresjonstester består. Den tidligere optimaliseringsanalysen ble også reprodusert med 7 tester og 193 verifiserte originale inputfiler.

## Kandidatene

| Kandidat | Lengde | Min. CDRH3-avstand | Høyeste identitet i referanseutvalget | NBB2 CA-RMSD | CDRH3-RMSD etter rammeverkstilpasning |
|---|---:|---:|---:|---:|---:|
'''
    for c in candidates:md+=f"| {c['name']} ({c['sequence_id'].split('_')[-2]}) | {c['length']} | {c['nearest_CDRH3_distance']} | {100*c['small_reference_max_identity']:.1f}% | {c['NBB2_final_all_CA_rmsd']:.2f} Å | {c['NBB2_final_CDRH3_CA_rmsd']:.2f} Å |\n"
    md+='''
RMSD beskriver samsvar med designet, ikke målt funksjon. Alle tre har to kanoniske cysteiner og ingen atompar under 2 Å mellom designet antistoff og antigen. Den beste monomer-folden er novel2 (original design 12). Den har et mulig N-glykosyleringsmotiv NVS i CDRH3. De to andre har blant annet isomeriserings-/deamideringsmotiver. Motiver er risikoflagg, ikke målte feil eller automatisk avvisning.

## Det viktigste kvalitetsfunnet

Mol-1 gjenfinner 18/19 av WT-epitopens kontaktrester med global ipTM 0.953. De nye VHH-ene har Mol-1 ipTM 0.124–0.190 på crop119 og svak/varierende epitopeoverlapp. AF2-IG gir ipTM 0.108–0.121 og interfacePAE rundt 26 Å for de tre selv når designposen oppgis. Dette er utilstrekkelig støtte til å kalle dem vellykkede bindere. OpenFold3 gjenfinner bare 2/19 WT-rester, som også viser hvorfor vi må kontrollere hver modell før negative prediksjoner tolkes. Fab- og VHH-globalipTM er ikke direkte kalibrert mot hverandre.

Alle 16 AntiFold-varianter har bedre strukturkondisjonert CDR-likelihood (NLL 0.707–0.769 mot 2.523 for originalen), men blir 70.9–73.1% identiske med minst ett kjent antistoff i samme utvidede referanseutvalg. Alle 16 består installert abguard som de_novo. Vi holder dem likevel tilbake på grunn av oppgavens strengere identitetskrav. Optimalisering av modellscore er derfor ikke nok.

## Hva abguard faktisk bekrefter

Den installerte 0.1.0-byggen identifiseres med kilde- og referansehasher, fordi det har eksistert ulike bygg med samme versjonsnummer. Dens track-klassifisering bruker identitet til trastuzumab. Oppgave-PDF-en beskriver derimot identitet til nærmeste kjente antistoff. Vi bevarer begge vurderingene.

`novelty-report` i dette bygget hopper over referansedatabasen via standardargumentet `skipped=True`; ukjent novelty-verdi må ikke telles som bestått. `team-validate` bruker referansen korrekt. En egen adapter bruker de offentlige Python-funksjonene med eksplisitt referanse uten å endre arrangørens validator. Adapteren og `team-validate` returnerer nøyaktig samme 127 aksepterte ID-er. Den feilaktige CLI-rapporten er bevart som revisjonsspor.

De tre opprinnelige VHH-ene har 0 RCSB-treff med 70%-grense og under 70% global aligneringsidentitet til de faktiske antistoffreferansene vi hentet. RCSB og dette utvalget dekker ikke alle kjente antistoffer. Dette er ikke et universelt novelty-bevis eller endelig godkjenning fra arrangørene.

De to lokale HER2-tabellene er også undersøkt direkte: 524346 FACS-rader og768 SPR-rader gir nøyaktig525063 unike CDRH3-er. Alle FACS/trastuzumab-VH-er ble kontrollert mot de faste flankene; IMGT-løkken er SR + den oppgitte core-sekvensen + Y. De andre SPR-VH-ene ble nummerert direkte. Minste eksakte Levenshtein-avstand mot alle525063 normaliserte IMGT-løkker er11 for novel2,15 for novel1 og18 for novel3. Dette oppfyller provided-data-kravet uten å anta at abguard-bundlen inneholder samme tabeller.\n\n## Forskningsbasert evaluering

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
'''
    md+=f"\n## Ressurser og kostnad\n\nJapanFold har fakturert **${usage['amount_usd']:.6f}** for de ni konkrete jobb-ID-ene i denne kampanjen, inklusive et mislykket AF2-inputforsøk som kostet $0. Det ble rettet ved å legge til et påkrevd CIF-felt, uten å endre koordinater; korrigert kjøring fullførte 5/5. AMASS-søk brukte 25 kreditter, tilsvarende $0.25 etter tjenestens kredittpris. Nebius returnerte ingen per-jobb dollarpris; lokal H100 er ikke separat priset. Tallene er ikke en samlet infrastrukturkostnad.\n"
    md+='''
## Filer og reproduksjon

- `report.html`: offline rapport, figur og roterbar CA-strukturvisning.
- `campaign-evidence.png` / `.pdf`: figur til presentasjonen.
- `exploratory-candidates.csv`: tre reserver med sekvens, hasher og bevisstatus; dette erstatter ikke den rangerte innsendingsfilen.
- `evidence.json`, `receipts/` og `source/`: resultater, kildekode, kvitteringer og kvalitetsspor.
- `structures/`: utvalgte design-, refold- og monomerstrukturer. Fullt originalarkiv ligger i teamprosjektets run011.

Rapporten kan bygges igjen med `PYTHONPATH=review/denovo/.venv/lib/python3.12/site-packages .venv/bin/python review/denovo/build_report.py --output <mappe>`. Revisjonen kjøres med samme Pythonmiljø og `review/denovo/verify_campaign.py`. Dette krever teamprosjektets eksisterende data og miljø. Pakken er ikke et selvstendig modell-/vektarkiv. Ingen API-jobber sendes på nytt av rapportbyggeren eller revisjonen.
'''
    (out/'RESULTATER.md').write_text(md);(Path(__file__).parent/'CAMPAIGN_RESULTS.md').write_text(md)
    # Pitch supplement: five concise slides and speaking notes, preserving the main Fab pitch.
    slides=[('The decision problem','Four guaranteed experiments. Which predictions deserve them?',
        'Start with the team’s data-supported Fab optimization panel. Treat de novo VHHs as a separate, explicitly riskier track.'),
        ('What we built','96 new sequences · 48 complex refolds · real affinity calibration',
        '80 generated complexes, 16 inverse-folding variants. 32 finalist/control pose checks plus 16 cysteine diagnostics.Three VHH sequences independently modelled with NanoBodyBuilder2. Calibration reuses 90 completed team models across 30 constructs.'),
        ('The falsification test','Known control first; confidence alone is insufficient',
        'Mol-1 recovers 18/19 WT epitope residues. The three novelty-screened VHHs receive weak docking support. AF2-IG also fails to retain the proposed interface convincingly. We report this before committing experimental slots.'),
        ('The non-obvious result','All 16 optimized variants pass abguard — and lose strict novelty',
        'AntiFold improves conditional sequence likelihood, but all 16 variants exceed 70% identity to a known antibody. The extra full-sequence gate catches what the installed WT-relative classifier misses.'),
        ('Value and next experiment','An auditable route from a model output to a defensible experiment',
        'Every candidate carries exact sequences, chain mappings, source/model hashes, reference scope, controls and a decision state. Next: expression, quantitative SPR, trastuzumab competition and direct thermal measurement. No newly measured binding or Tm claim.')]
    notes='# English pitch supplement: de novo quality and research\n\nUse alongside the existing main optimization pitch. All model jobs described here are completed.\n\n'
    for i,(title,headline,body) in enumerate(slides,1):notes+=f'## {i}. {title}\n\n**{headline}**\n\n{body}\n\n'
    notes+='## Questions to prepare for\n\n- Are these validated binders? No; three exploratory VHHs pass the installed sequence validator and additional limited novelty checks. Docking support is weak and experiments are pending.\n- Is127/131 a binder hit rate? No. It is sequence-validation acceptance across new designs, diagnostics and 20 previous controls.\n- Did NAC beat ipTM? The point correlation was stronger on25 related constructs; the paired bootstrap interval includes zero.\n- Why not automatically select VHHs for the four slots? The current Fab panel has stronger data support; novelty alone does not justify replacing it.\n- Is the API bill the total project cost? No; JapanFold$0.415739 and AMASS25credits are separately recorded. Nebius and localGPU costs are not separately priced.\n'
    (out/'PITCH_SUPPLEMENT.md').write_text(notes)
    tr=''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in [c['name'],c['length'],c['nearest_CDRH3_distance'],f"{100*c['small_reference_max_identity']:.1f}%",f"{c['NBB2_final_all_CA_rmsd']:.2f} Å",'Exploratory reserve'])+'</tr>' for c in candidates)
    blocks=''.join(f'<section class="slide"><div class="eyebrow">{i:02d} / PITCH SUPPLEMENT</div><h2>{html.escape(h)}</h2><h3>{html.escape(t)}</h3><p>{html.escape(b)}</p></section>' for i,(t,h,b) in enumerate(slides,1))
    png=base64.b64encode((out/'campaign-evidence.png').read_bytes()).decode()
    viewer_json=json.dumps(viewers,separators=(',',':'))
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HER2 / evidence room</title><style>
:root{--ink:#e9f0f9;--muted:#a6b7c8;--bg:#0a1421;--line:#27384a;--green:#6fe0bc;--orange:#ffd391}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 system-ui,sans-serif}main{max-width:1280px;margin:auto;padding:46px 38px}header{border-bottom:1px solid var(--line);padding-bottom:30px}h1{font-size:clamp(36px,5.8vw,70px);line-height:1.08;letter-spacing:-.05em;margin:14px 0 23px;max-width:960px}h2{font-size:33px;line-height:1.2;letter-spacing:-.025em}h3{font-size:21px}p{max-width:940px}.eyebrow{font:12px monospace;letter-spacing:.15em;color:var(--green)}.lead{font-size:22px;color:var(--muted);max-width:1000px}.badge{display:inline-block;padding:5px 12px;border:1px solid #675134;color:var(--orange);border-radius:30px;font-size:13px}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:35px 0}.card{background:#112235;border:1px solid var(--line);border-radius:12px;padding:22px}.card b{display:block;font-size:36px;line-height:1.3}.card span{color:var(--muted);font-size:14px}section{margin:52px 0}a{color:var(--green)}nav{display:flex;gap:24px;flex-wrap:wrap;font-size:14px;margin-top:22px}img.figure{width:100%;border-radius:10px;background:white}table{width:100%;border-collapse:collapse;font-size:14px}td,th{text-align:left;padding:12px 10px;border-bottom:1px solid var(--line)}.scroll{overflow:auto}.note{color:var(--muted);font-size:14px}.callout{padding:20px 26px;border-left:3px solid var(--orange);background:#182538;border-radius:0 10px 10px 0}.controls{display:flex;gap:14px;align-items:center;flex-wrap:wrap}select,button{background:#172e44;color:var(--ink);border:1px solid #496178;padding:10px;border-radius:6px;font:inherit}canvas{display:block;width:100%;height:490px;background:radial-gradient(at 45% 45%,#17344a,#0b1927);border:1px solid var(--line);border-radius:12px;touch-action:none;margin-top:15px}.legend{display:flex;gap:20px;font-size:13px;flex-wrap:wrap;margin:12px 0}.swatch:before{content:'●';color:var(--c);padding-right:7px}.slide{padding:30px;background:#112235;border:1px solid var(--line);border-radius:12px}.slide h2{max-width:900px;font-size:38px}.slide h3{color:var(--green)}details{border:1px solid var(--line);border-radius:9px;padding:16px 22px;margin:16px 0}summary{cursor:pointer;color:var(--green)}.pitch header,.pitch #overview,.pitch #figure,.pitch #viewer,.pitch #reserves,.pitch #audit,.pitch footer{display:none}.pitch .slide{display:none;min-height:82vh;padding:6vw}.pitch .slide.active{display:block}.pitch main{max-width:1500px}.pitch h2{font-size:clamp(36px,5.4vw,76px)}.pitch .slide p{font-size:24px}.pitchbar{position:fixed;bottom:15px;right:20px;display:flex;gap:10px;z-index:5}.pitchbar button{font-size:14px}@media(max-width:760px){main{padding:30px 18px}.cards{grid-template-columns:repeat(2,1fr)}.card{padding:15px}.lead{font-size:18px}canvas{height:390px}.slide h2{font-size:29px}}@media print{body{background:white;color:#182a3a}main{padding:10px}.card,.slide{background:white}.slide{break-before:page;min-height:80vh}.pitchbar,.controls,canvas,#viewer{display:none}a{color:#13745e}.note,.lead{color:#465768}.card span{color:#465768}h1{font-size:42px}}
</style><main><header><div class="eyebrow">TEAM14 · HER2 · COMPUTATIONAL CAMPAIGN</div><h1>Design boldly.<br>Make the evidence survive.</h1><p class="lead">96 new sequences, independent structure checks and real historical affinity calibration. Three novelty-screened VHH reserves; binding remains unproven.</p><span class="badge">COMPUTATIONS COMPLETE · EXPERIMENTS PENDING</span><nav><a href="#figure">Scientific figure</a><a href="#viewer">Explore structures</a><a href="#reserves">Candidate decisions</a><a href="#audit">Evidence & scope</a><a href="#pitch" onclick="pitch(true)">Pitch mode ↗</a></nav></header>
<div id="overview"><div class="cards"><div class="card"><b>96</b><span>80 complex designs +16 sequence variants</span></div><div class="card"><b>48</b><span>completed complex predictions; includes controls/diagnostics</span></div><div class="card"><b>3</b><span>novelty-screened exploratory reserves</span></div><div class="card"><b>25</b><span>historical measured KD values in new calibration</span></div></div><div class="callout"><b>Decision:</b> keep the data-supported Fab optimization panel as the main submission case. The VHHs pass installed sequence rules, but independent models do not convincingly retain their proposed HER2 interface.</div></div>
<section id="figure"><div class="eyebrow">RESULTS · EXPORTABLE FIGURE</div><h2>The controls change the story.</h2><img class="figure" src="data:image/png;base64,IMAGEDATA" alt="Four panels:96 design sequences, blind epitope recovery, retrospective affinity calibration and likelihood versus novelty"><p class="note">The90 calibration models represent30 constructs and3 seeds each; only25 constructs have quantified KD. Related variants and historical selection bias limit inference. The paired NAC–ipTM difference interval includes zero. <a href="campaign-evidence.pdf">PDF figure</a></p></section>
<section id="viewer"><div class="eyebrow">STRUCTURE EXPLORER · OFFLINE</div><h2>A fold can survive while a binding pose does not.</h2><p>Rotate the CA traces to compare the supplied design with an independent prediction. Each cofold binder is aligned on the same109 resolved HER2 residues. The target trace remains the original design target.</p><div class="controls"><label>Candidate <select id="candidate"><option>novel2</option><option>novel1</option><option>novel3</option></select></label><label>Compare <select id="compare"><option value="mol1">Mol-1 blind docking</option><option value="openfold3">OpenFold3 blind docking</option><option value="opendde-abag">OpenDDE AbAg blind docking</option><option value="af2ig">AF2-IG: supplied design pose</option><option value="NBB2_self_aligned">NBB2 monomer, self-aligned</option></select></label><button onclick="resetView()">Reset view</button></div><canvas id="structure" aria-label="Interactive protein CA trace viewer"></canvas><div class="legend"><span class="swatch" style="--c:#75afbe">HER2 target</span><span class="swatch" style="--c:#ffcf79">WT epitope</span><span class="swatch" style="--c:#63e6b6">Design VHH</span><span class="swatch" style="--c:#c1a4ff">Independent model</span></div><p class="note">Drag to rotate; scroll to zoom. Orange residues denote the19-residue reference epitope. The unobserved10-residue target segment is not drawn as an experimentally resolved trace. NBB2 is aligned to the VHH itself and assesses monomer geometry; it does not predict antigen docking. AF2-IG is conditioned on the proposed pose. These are predictions, not experimental structures of the new binders.</p></section>
<section id="reserves"><div class="eyebrow">CANDIDATE DECISIONS</div><h2>Eligible by the installed build ≠ demonstrated binder.</h2><div class="scroll"><table><thead><tr><th>Candidate</th><th>aa</th><th>CDRH3 distance</th><th>Nearest identity*</th><th>NBB2 CA RMSD</th><th>Decision</th></tr></thead><tbody>TABLEROWS</tbody></table></div><p class="note">*Global BLOSUM62 alignment in the retrieved reference subset. All three also return zero RCSB hits at 70% identity cutoff. Neither check proves novelty against all known antibodies. Candidate ranking here is monomer fold consistency, not a binding ranking. <a href="exploratory-candidates.csv">Download exact sequences and evidence</a>.</p><div class="callout"><b>Novelty regression caught:</b> all 16 AntiFold variants improve conditional likelihood and pass installed abguard, yet exceed 70% identity to a known antibody. We held them back instead of calling better model scores a successful de novo design.</div></section>
<section id="audit"><div class="eyebrow">AUDITABLE EVIDENCE</div><h2>Make every claim traceable.</h2><details open><summary>Validation:127/131 accepted sequences is not a binder hit rate</summary><p>The131 inputs comprise 96 new designs, 15 diagnostic Cys variants and 20 existing Fab controls. The reference index has 610109 CDRH3s. All 20 existing controls pass. The raw novelty-report CLI in this build silently skips the reference; explicit-reference Python functions and team-validate agree on exactly 127 accepted IDs. A separate exact check reconstructs all525063 distinct IMGT CDRH3s from both provided HER2 tables: minimum edit distances are11,15 and18 for novel2,novel1 andnovel3. Code and reference hashes identify the restored build. Its classification is trastuzumab-relative; the challenge PDF also asks for nearest-known-antibody identity.</p></details><details><summary>Model controls and failed attempt</summary><p>Mol-1 recovers 18/19 WT epitope contacts, OpenDDE 7/19 and OpenFold3 only 2/19 in the same crop context. A first AF2-IG input attempt failed because the engine required an explicit insertion-code field. The corrected run preserved every atom, residue and coordinate value and completed 5/5. Failed attempts are preserved. No campaign job remains pending.</p></details><details><summary>Costs, tests and limits</summary><p>JapanFold billed$0.415739 for these nine job IDs. Five AMASS searches used 25 credits ($0.25 at the service credit price). Nebius and local GPU costs are not separately priced.20 provenance/data checks and8 new regression tests pass; the earlier optimization replay passed7 tests and verified193 original inputs. No new measured affinity, competition or Tm exists.</p></details><details><summary>Research and source files</summary><p><a href="https://arxiv.org/abs/2610.23136">Oct2026 filtering preprint</a>: motivated the CA-based framework-confidence adaptation, not a new RIC implementation. <a href="https://github.com/oxpig/AntiFold/tree/9918344067f34a6b026f2634fdba212fc3e6e986">AntiFold source</a>: structure-conditioned antibody inverse folding. <a href="https://arxiv.org/abs/2607.03787">OpenDDE report</a>: antibody-specific cofolding. <a href="https://japanfold.aiand.com/docs/predictions/">JapanFold docs</a>: prediction and AF2-IG contracts.</p><p><a href="RESULTATER.md">Norwegian results</a> · <a href="PITCH_SUPPLEMENT.md">Speaking notes</a> · <a href="evidence.json">Machine-readable evidence</a> · <a href="SHA256SUMS">File hashes</a></p></details></section>
<div id="pitch">SLIDEBLOCKS</div><footer><p class="note">Built from frozen team14 run011 artifacts. Final experiment selection remains with the team. Computational claims are separated from historical measurements and future experiments.</p></footer></main><div class="pitchbar"><button onclick="step(-1)">←</button><button onclick="pitch(!document.body.classList.contains('pitch'))">Pitch / report</button><button onclick="step(1)">→</button></div>
<script>const DATA=VIEWERDATA,EPITOPE=new Set(EPITOPEDATA);let rx=-.3,ry=.5,zoom=4,drag=null,slide=0;const canvas=document.getElementById('structure'),ctx=canvas.getContext('2d');function resetView(){rx=-.3;ry=.5;zoom=4;draw()}function project(p,w,h){let[x,y,z]=p;let q=x*Math.cos(ry)+z*Math.sin(ry),t=-x*Math.sin(ry)+z*Math.cos(ry),v=y*Math.cos(rx)-t*Math.sin(rx);return[q*zoom+w/2,-v*zoom+h/2,y*Math.sin(rx)+t*Math.cos(rx)]}function draw(){let rect=canvas.getBoundingClientRect();if(!rect.width)return;const dpr=devicePixelRatio||1;canvas.width=rect.width*dpr;canvas.height=rect.height*dpr;ctx.scale(dpr,dpr);let w=rect.width,h=rect.height;ctx.clearRect(0,0,w,h);let d=DATA[document.getElementById('candidate').value],m=document.getElementById('compare').value;let lines=[];function trace(arr,color,width,ids){for(let i=1;i<arr.length;i++){if(ids&&ids[i]-ids[i-1]>1)continue;let a=project(arr[i-1],w,h),b=project(arr[i],w,h);lines.push({a,b,color:ids&&(EPITOPE.has(ids[i])||EPITOPE.has(ids[i-1]))?'#ffcf79':color,width,z:(a[2]+b[2])/2})}}trace(d.target,'#75afbe',2,d.target_ids);trace(d.design,'#63e6b6',2.7);trace(d[m],'#c1a4ff',2.5);lines.sort((a,b)=>a.z-b.z);for(let l of lines){ctx.strokeStyle=l.color;ctx.lineWidth=l.width;ctx.globalAlpha=.83;ctx.beginPath();ctx.moveTo(l.a[0],l.a[1]);ctx.lineTo(l.b[0],l.b[1]);ctx.stroke()}ctx.globalAlpha=1;ctx.fillStyle='#d7e8f6';ctx.font='13px system-ui';ctx.fillText(document.getElementById('candidate').value+' / '+document.getElementById('compare').selectedOptions[0].text,18,25)}canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId)};canvas.onpointermove=e=>{if(!drag)return;ry+=(e.clientX-drag[0])*.009;rx+=(e.clientY-drag[1])*.009;drag=[e.clientX,e.clientY];draw()};canvas.onpointerup=()=>drag=null;canvas.onpointercancel=()=>drag=null;canvas.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(1,Math.min(14,zoom*Math.exp(-e.deltaY*.001)));draw()},{passive:false});document.getElementById('candidate').onchange=draw;document.getElementById('compare').onchange=draw;window.onresize=draw;function pitch(on){document.body.classList.toggle('pitch',on);if(on){step(0);window.scrollTo(0,0)}else draw()}function step(delta){const s=[...document.querySelectorAll('.slide')];slide=(slide+delta+s.length)%s.length;s.forEach((x,i)=>x.classList.toggle('active',i===slide));if(document.body.classList.contains('pitch'))window.scrollTo(0,0)}document.onkeydown=e=>{if(e.key==='Escape')pitch(false);if(document.body.classList.contains('pitch')&&['ArrowLeft','ArrowRight'].includes(e.key))step(e.key==='ArrowLeft'?-1:1)};draw();</script></html>'''
    page=page.replace('IMAGEDATA',png).replace('TABLEROWS',tr).replace('SLIDEBLOCKS',blocks).replace('VIEWERDATA',viewer_json).replace('EPITOPEDATA',json.dumps(sorted(EPITOPE)))
    (out/'report.html').write_text(page)
    # Curated owned evidence. Never copy credentials, participant ZIPs, environment or API headers.
    receipts=out/'receipts';receipts.mkdir(exist_ok=True)
    for name in ['campaign.json','quality-audit.json','provided-HER2-reference-check.json','unit-tests.log','local-candidates.json','pilot-candidates.json','pilot-summary.json',
      'antifold-candidates.json','antifold-final-known-identity.json','antifold-input-receipt.json','antifold-rcsb-sequence-searches.json',
      'expanded-antibody-references.json','variable-rcsb-sequence-searches.json','local-final-known-identity.json','regional-calibration.json',
      'regional-calibration.csv','regional-calibration-seeds.csv','nanobodybuilder-evidence.json','local-refold-evidence.json',
      'local-refold-manifest.json','initial-guess-input-receipt.json','japanfold-usage-ledger.json']:
        shutil.copy2(RUN/name,receipts/name)
    for name in ['receipt.json','explicit-reference-receipt.json','submission.csv','novelty-reference-checked.csv','validated-reference-checked.csv','liabilities.json','novelty.csv','novelty-report.log']:
        shutil.copy2(RUN/'abguard-final'/name,receipts/('abguard-'+name))
    for p in sorted(RUN.glob('*/submission.json')):
        prefix=p.parent.name
        for n in ['submission.json','job.json','usage.json','download_receipt.json','correction.json']:
            if (p.parent/n).exists():shutil.copy2(p.parent/n,receipts/(prefix+'__'+n))
    for name in ['replay.log','amass-findings.json']:
        p=Path(__file__).parent/'evidence'/name
        if p.exists():shutil.copy2(p,receipts/name)
    structures=out/'structures';structures.mkdir(exist_ok=True)
    for item in selected:
        stem=item['name'];key=item['candidate'];shutil.copy2(ROOT/local[key]['structure'],structures/(stem+'__generated.cif'))
        final=next(m for m in nbb[key]['models'] if m['native_file']=='final_model.pdb');shutil.copy2(ROOT/final['path'],structures/(stem+'__NBB2.pdb'))
        for row in evidence:
            if row['candidate']==key:shutil.copy2(ROOT/row['structure'],structures/(row['name']+'__'+row['model']+'.cif'))
    # A single entry point for offline verification/rebuild in the existing project.
    replay='''#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH="$PWD/review/denovo/.venv/lib/python3.12/site-packages${PYTHONPATH:+:$PYTHONPATH}"
.venv/bin/python -m unittest discover -s review/denovo -p 'test_*.py' -v
.venv/bin/python review/denovo/verify_campaign.py
.venv/bin/python review/denovo/build_report.py --output "${1:?Pass output directory}"
'''
    (Path(__file__).parent/'refresh.sh').write_text(replay);(Path(__file__).parent/'refresh.sh').chmod(0o755);(sources/'refresh.sh').write_text(replay)
    (out/'README.md').write_text('Open report.html for the offline evidence room and pitch mode. See RESULTATER.md for the complete Norwegian report and limits. This supplement preserves the main Fab optimization panel. Exact new VHH sequences are exploratory reserves. Source files rebuild from the team project; model weights and full input datasets are not bundled.\n')
    manifest=''.join(sha(p)+'  '+str(p.relative_to(out))+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='SHA256SUMS')
    (out/'SHA256SUMS').write_text(manifest)
    print(json.dumps({'output':str(out),'candidates':len(candidates),'figure':str(out/'campaign-evidence.png'),
                      'file_count':len(list(out.rglob('*'))),'report_html_bytes':(out/'report.html').stat().st_size},indent=2))

if __name__=='__main__':main()
