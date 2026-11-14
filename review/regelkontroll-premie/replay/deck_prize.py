from pathlib import Path
import json
import pymupdf as fitz
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR
from pptx.oxml.xmlchemy import OxmlElement

folder=Path(__file__).parent
pdf=fitz.open(); ppt=Presentation(); ppt.slide_width=Inches(13.33333);ppt.slide_height=Inches(7.5)
W,H=960,540
ink='#142B36'; sub='#415E65'; green='#00776C'; pale='#DEF1EB'; white='#FFFFFF'; bg='#F9FAF5'; orange='#A84A28'; sand='#F7E7DA'; light='#E4E9E5'
reg='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def rgb(h):return RGBColor.from_string(h[1:])
def col(h):return tuple(int(h[i:i+2],16)/255 for i in (1,3,5))
def box(x,y,w,h,c):
    page.draw_rect(fitz.Rect(x,y,x+w,y+h),color=None,fill=col(c))
    shape=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,Pt(x),Pt(y),Pt(w),Pt(h));shape.fill.solid();shape.fill.fore_color.rgb=rgb(c);shape.line.fill.background()
def txt(x,y,w,s,size=16,c=ink,b=False):
    font=fitz.Font(fontfile=bold if b else reg)
    size=min(size, size*(w-.5)/max(font.text_length(line,fontsize=size) for line in s.split('\n')))
    for line in s.split('\n'):
        wid=font.text_length(line,fontsize=size)
        assert wid < w+1,(line,wid,w)
    lines=s.split('\n')
    for n,line in enumerate(lines):
        page.insert_text((x,y+size+n*size*1.28),line,fontsize=size,fontname='B' if b else 'R',color=col(c))
    tb=slide.shapes.add_textbox(Pt(x),Pt(y-1),Pt(w+2),Pt(size*(1.34*len(lines)+.4)))
    tf=tb.text_frame;tf.clear();tf.margin_left=tf.margin_top=tf.margin_right=tf.margin_bottom=0;tf.word_wrap=False
    for i,line in enumerate(lines):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.space_after=Pt(0);p.space_before=Pt(0);p.line_spacing=Pt(size*1.28)
        r=p.add_run();r.text=line;r.font.name='DejaVu Sans';r.font.size=Pt(size);r.font.bold=b;r.font.color.rgb=rgb(c)
def new(label,title,notes):
    global page,slide
    page=pdf.new_page(width=W,height=H);slide=ppt.slides.add_slide(ppt.slide_layouts[6]);slide.notes_slide.notes_text_frame.text=notes
    for k,f in [('R',reg),('B',bold)]:page.insert_font(fontname=k,fontfile=f)
    box(0,0,W,H,bg);txt(45,28,865,label,13,green,True);txt(45,58,870,title,32,ink,True)
def footer(s):box(45,486,870,1,light);txt(45,501,870,s,11,sub)
def cell(x,y,w,h,big,cap,small):
    box(x,y,w,h,pale);txt(x+15,y+14,w-28,big,38,green,True);txt(x+15,y+70,w-28,cap,17,ink,True);txt(x+15,y+107,w-25,small,14,sub)
receipt=json.loads((folder/'previous-openfold.json').read_text())
history=json.loads((folder/'previous-historical.json').read_text())
repeat={r['query']:r for r in receipt['four_repeats_hits_of19']}
def row(y,name,reason,detail):
    box(45,y,870,64,white);txt(60,y+13,175,name,20,green,True)
    txt(240,y+6,660,reason,19,ink,True);txt(240,y+35,660,detail,15,sub)

new('TEAM 14    /    HER2','Which four antibodies deserve a lab slot?',
    'Trastuzumab already binds HER2 strongly. We have four guaranteed places. We built an assay-selection experiment. We first asked what our method had actually predicted correctly on past antibodies, then reconciled the rankings across models before allocating the four slots.')
txt(45,138,859,'A lab lead has 20 designs and four guaranteed measurements.\nGetting a binding signal is easier than improving an effective drug.',21)
cell(45,234,274,169,'18','Trastuzumab variants','Paired antibody chains')
cell(333,234,274,169,'2','Exploratory designs','Single-domain antibodies')
cell(621,234,294,169,'3','Laboratory readouts','Strength, site, heat tolerance')
footer('One ranked list. Local sequence validation accepted every design. Adaptyv measures the selected designs after the event.')

new('RETROSPECTIVE CHECK    /    255 DISTINCT HISTORICAL VARIANTS','Our selection rule found measurable binding.',
    'We drew 40 constructs 5,000 times from 255 variants with four to six changes that were absent from the FACS screen. All methods saw the same draws. The statistic counts a reported, quantitative SPR binding fit. Historical sampling was partly guided by BLOSUM. None of the 82 quantified variants beat even the weakest observed WT value. A group of 45 more had inconclusive or missing outcomes. We cannot calibrate the chance of beating WT on this subset.')
for i,(label,val,c) in enumerate([('Random selection',history['methods']['random']['fits_per_four'],sub),
                                   ('FACS-trained model',history['methods']['high_FACS']['fits_per_four'],green),
                                   ('Parent sequence score',history['methods']['BLOSUM62']['fits_per_four'],green)]):
    y=148+i*59;txt(45,y,305,label,17,ink,True);box(355,y+1,390,20,light);box(355,y+1,390*val/4,20,c);txt(772,y-5,139,f'{val:.2f} / 4',21,c,True)
box(45,350,870,92,sand);txt(61,363,830,'0 of 82 quantified variants beat even the weakest historical reference.',20,ink,True)
txt(61,399,830,'Best variant 0.185 nM. Trastuzumab ranged from 0.029 to 0.178 nM over eight records.',16,sub)
footer('Lower KD means tighter binding. 5,000 draws reuse the same historical pool. Historical values span assay batches.')

new('STRUCTURAL CHECK    /    TWO WAYS TO COUNT CONTACTS','Our strongest pose claim depended on the setup.',
    'From 25.2 million eligible-by-our-screen sequences the team refolded a diverse 40. In Boltz-2, using the prepared complex template and two HER2 fragments, anas_007 matched the entire crystal footprint in five of six runs. We repeated the comparison in Apheris OpenFold3 using one continuous fragment. The target-only template preserves 109 observed residues and withholds antibody coordinates. Across providers several settings changed. Only the within-Apheris template comparison isolates that setting.')
txt(45,127,860,'anas_007 reproduced the exact 19-residue crystal surface in 5/6 Boltz-2 poses.',18,ink,True)
txt(45,172,865,'Apheris OpenFold3 recovered these numbers of crystal contacts out of 19',17,sub)
for i,(label,x) in enumerate([('Antibody',45),('Sequence only',360),('With HER2 coordinates',655)]):txt(x,222,300,label,15,sub,True)
for i,(key,label) in enumerate([('trastuzumab_wt','Trastuzumab control'),('anas_007','anas_007')]):
    y=258+73*i;box(45,y,870,58,white);txt(55,y+13,285,label,19,ink,True)
    for x,cond in [(370,'no_template'),(661,'HER2_only_template')]:
        txt(x,y+10,215,'  /  '.join(map(str,repeat[key][cond])),24,green,True)
txt(45,416,870,'Three random seeds per cell, in the same order. The control itself misses known contacts.',16,sub)
footer('One continuous 119-residue HER2 sequence. Distances use heavy atoms within 4.5 Å against the observed 1N8Z footprint.')

new('FOUR GUARANTEED PLACES    /    REVISED PRIORITY','Which four would we express first?',
    'This is an experimental priority chosen after seeing the model results. All 18 Fabs recovered 19/19 crystal contact residues in Mol-1. We looked at extra contacts, the other models, pose clashes and the partial binding-energy results. A fitted KD, competition and a thermal gain must be measured by the lab. The matched pair anas_015 and anas_009 moves to slots five and six, where it is informative if both are tested.')
row(126,'#1   anas_007','Most support for the original surface','Boltz-2 matched the exact footprint in 5/6 poses. Apheris OpenFold3 recovered 0–6/19.')
row(203,'#2   anas_003','A direct hypothesis about binding','The most favourable StaB-ddG estimate in the tested candidate batch. OpenFold3 gave 2/19 at seed 42 in both setups.')
row(280,'#3   r004_cdrh3_3','A second design method','Mol-1 and OpenDDE recovered 19 and 18 crystal contacts. Both poses clear the rest of HER2 in the overlay.')
row(357,'#4   anas_016','The most parent-like choice by BLOSUM','Sequence score 40. OpenDDE recovered 17/19. Boltz-2 kept all four loop contacts in 3/6 poses.')
footer('The matched comparison moves to ranks 5 and 6. With six slots we can still test whether contact persistence predicts competition.')

new('EXPLORATORY TRACK    /    TWO OF TWENTY','Why give a new antibody a place?',
    'We screened 96 design sequences in the de novo campaign. Three passed the installed validator and an additional sampled known-antibody identity screen. The primary and reserve VHHs test whether docking agreement across antigen lengths adds evidence. novel3 had the most consistent target evidence but the largest unbound loop discrepancy. novel1 had better loop reproduction but Mol-1 target recovery disappears on the longer HER2 sequence. novel2 had the best unbound fold but lacked target evidence. We prioritised target engagement and left it out.')
row(151,'#8   novel3','Two models point to the same region','On long HER2, Mol-1 and OpenDDE each recovered 8/19 crystal contacts.')
row(235,'#12   novel1','A test of sensitivity to antigen length','Mol-1 recovery fell from 7/19 on the short fragment to 0/19 on long HER2.')
txt(45,357,865,'Four lab slots test four optimisations. Eight slots bring in the first de novo design.\nTwelve slots test both. Final track assignment rests with the organisers.',18)
footer('VHH docking is exploratory. The unbound loop of novel3 deviated 15.0 Å from its designed pose in the monomer check.')

new('ADAPTYV    /    PROSPECTIVE LAB DECISION','What would earn S-tier?',
    'The first user is the assay lead choosing constructs for a finite laboratory budget. Submit the frozen order. Adaptyv tests the awarded top N and measures trastuzumab in the same campaign. Record expression failures, missing measurements and the three actual outcomes. For independent validation, repeat the matched-pair hypothesis on additional eligible pairs before claiming general value.')
for i,(title,details) in enumerate([('Binding strength','SPR measures how tightly each expressed antibody binds HER2.'),
                                    ('Binding site','Competition asks whether it blocks trastuzumab from binding.'),
                                    ('Heat tolerance','A direct thermal measurement compares each design with the reference.')]):
    y=149+i*56;txt(45,y,200,title,17,green,True);txt(250,y,665,details,16)
box(45,343,870,101,pale);txt(61,355,830,'The assay lead needs three readouts and a same-run control.',18,ink,True)
txt(61,390,830,'Freeze the order, record failed assays, then repeat the comparison on independent pairs.',16,sub)
footer('All candidate tiers await lab data. Team 14 provides the sequences, coordinates, model receipts and ranking rationale.')
ppt.save(folder/'PITCH_PREMIE.pptx');pdf.save(folder/'PITCH_PREMIE.pdf',garbage=4,deflate=True)
