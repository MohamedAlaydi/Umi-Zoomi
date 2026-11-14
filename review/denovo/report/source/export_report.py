import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright
parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path);root=parser.parse_args().output.resolve()
errors=[];checks=[]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto((root/'report.html').as_uri(),wait_until='load')
 assert page.title()=='HER2 / evidence room';checks.append('report loads offline')
 assert page.locator('#reserves tbody tr').count()==3;checks.append('three reserve rows')
 initial=page.locator('#structure').screenshot(path=str(root/'structure-preview.png'))
 page.select_option('#candidate','novel1');page.select_option('#compare','af2ig')
 changed=page.locator('#structure').screenshot()
 assert changed!=initial;checks.append('candidate/model selectors redraw canvas')
 page.locator('#structure').scroll_into_view_if_needed();box=page.locator('#structure').bounding_box()
 page.mouse.move(box['x']+220,box['y']+160);page.mouse.down();page.mouse.move(box['x']+360,box['y']+210);page.mouse.up()
 assert page.locator('#structure').screenshot()!=changed;checks.append('pointer rotation redraws canvas')
 page.evaluate('pitch(true)');assert page.locator('.slide:visible').count()==1
 page.keyboard.press('ArrowRight');assert page.locator('.slide.active .eyebrow').inner_text().startswith('02')
 page.keyboard.press('Escape');assert not page.locator('body').evaluate('(x)=>x.classList.contains("pitch")');checks.append('pitch navigation and Escape')
 page.set_viewport_size({'width':390,'height':844})
 assert page.evaluate('document.documentElement.scrollWidth')<=390;checks.append('mobile width has no page overflow')
 page.set_viewport_size({'width':1440,'height':1000});page.evaluate('window.scrollTo(0,0)')
 page.screenshot(path=str(root/'report-preview.png'))
 # Export the actual five-slide supplement; no report chrome or interactive controls.
 page.evaluate('''()=>{let slides=document.getElementById('pitch').innerHTML;document.querySelector('main').innerHTML=slides;document.querySelector('.pitchbar').remove()}''')
 page.add_style_tag(content='''@media print { @page {size:A4 landscape;margin:10mm} body{background:white;color:#182a3a}main{padding:0;max-width:none}.slide{display:block!important;height:188mm;min-height:0;margin:0;padding:28px;break-before:auto;break-after:page;background:white;color:#182a3a;border:1px solid #bbc9d3}.slide:last-child{break-after:auto}.slide h2{font-size:45px;line-height:1.15;max-width:100%}.slide h3{font-size:24px;color:#13745e}.slide p{font-size:22px;line-height:1.6;max-width:100%}.eyebrow{color:#13745e}}''')
 page.pdf(path=str(root/'PITCH_SUPPLEMENT.pdf'),landscape=True,prefer_css_page_size=True,print_background=True)
 checks.append('five-slide PDF exported')
 assert not errors,errors
 browser.close()
(root/'browser-checks.json').write_text(json.dumps({'passed':True,'checks':checks,'page_errors':errors},indent=2))
print(json.dumps({'passed':True,'checks':checks,'page_errors':errors},indent=2))
