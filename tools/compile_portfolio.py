"""Compile complete project case studies from the client's local PDF.

Run from the repository root with Python and pypdf, pdfplumber, pypdfium2,
and Pillow installed. No network access or frontend build dependencies.
"""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import html
import json
import re

import pdfplumber
import pypdfium2 as pdfium
from pypdf import PdfReader
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "LADESMA - PORTFOLIO.pdf"
OUT = ROOT / "media" / "complete"
AUDIT = ROOT / ".taste-skill" / "complete-audit"
ESC = html.escape
PROJECTS = [
    dict(slug="salupod", code="SAL", name="Salupod", start=3, end=17,
         concept=4, features=5, controls=6, elevations=16, sections=17,
         narrative=13, title="Salupod: The Community Core",
         plans={7:"Site development plan", 8:"Plan on site", 9:"Second floor plan — Area A", 10:"Second floor plan — Area B", 11:"Third floor plan — Area A", 12:"Third floor plan — Area B"},
         perspectives=[13,14,15], materials={2:"Perforated metal panels",3:"Permeable pavement",4:"Wood cladding",5:"Natural stone finish",6:"Low-E glass"},
         feature_indices=[0,1], alt={0:"Landscaped central gathering space",1:"Library facade and planting"}),
    dict(slug="lakbay", code="LAK", name="Lakbay", start=18, end=34,
         concept=19, features=20, controls=21, elevations=33, sections=34,
         narrative=30, title="Lakbay: The Journey of Learning",
         plans={22:"Site development plan",23:"Plan on site",24:"Second floor plan — Area A",25:"Second floor plan — Area B",26:"Second floor plan — Area C",27:"Third floor plan — Area A",28:"Third floor plan — Area B",29:"Third floor plan — Area C"},
         perspectives=[30,31,32], materials={0:"Wood cladding",1:"Low-E glass",2:"Rubber flooring",4:"Non slip porcelain tiles",5:"Terracota tiles"},
         feature_indices=[3,6], alt={3:"Undulating school facade",6:"School facade and pedestrian circulation"}),
    dict(slug="dalawit", code="DAL", name="Dalawit", start=35, end=47,
         concept=36, features=37, controls=38, elevations=46, sections=47,
         narrative=42, title="Dalawit: Interlocked Sanctuaries",
         plans={39:"Site development plan",40:"Plan on site — Duplex unit",41:"Second floor plan — Duplex unit"},
         perspectives=[42,43,44,45], materials={0:"Wood cladding",1:"Natural stone finish",2:"Low-E glass",3:"Woven bamboo panels",6:"Textured concrete"},
         feature_indices=[4,5], alt={4:"Duplex living room and feature wall",5:"Duplex exterior and wood cladding"}),
]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def variants(stem, image, full_cap=None, quality=72, refresh=False):
    image = image.convert("RGBA" if image.mode in ("RGBA", "LA", "P") else "RGB")
    outputs = {}
    for label, cap, q in [("640",640,quality),("1280",1280,quality),("full",full_cap or image.width,90)]:
        path = OUT / f"{stem}-{label}.webp"
        cp = image.copy()
        cp.thumbnail((cap,cap * 12))
        if refresh or not path.exists():
            cp.save(path, "WEBP", quality=q, method=4)
        outputs[label] = dict(path=path.relative_to(ROOT).as_posix(), width=cp.width, height=cp.height)
    return outputs


def source_id(project, page, kind, number=None):
    return f"{project['code']}-P{page:02}-{kind}" + (f"{number:02}" if number is not None else "")


def clean_encoding(text):
    # These replacements restore punctuation lost by PDF text extraction, not wording.
    return text.replace("student�from", "student—from").replace("students�", "students’").replace("Duality � Interlocked", "Duality – Interlocked")


def get_source():
    reader = PdfReader(PDF)
    document = pdfium.PdfDocument(str(PDF))
    content = []
    with pdfplumber.open(PDF) as plumber:
        for project in PROJECTS:
            p = dict(project)
            pages = []
            for number in range(p['start'],p['end']+1):
                page = plumber.pages[number-1]
                raw = list(reader.pages[number-1].images)
                positions = page.images
                if len(raw) != len(positions):
                    raise ValueError(f"Image inventory differs on physical page {number}")
                text = clean_encoding(page.extract_text() or "")
                sheet_img = document[number-1].render(scale=3400/page.width).to_pil().convert('RGB')
                sheet = dict(id=source_id(p,number,'SHEET'), page=number, text=text,
                             outputs=variants(f"{p['code'].lower()}-p{number:02}-sheet", sheet_img,3400),
                             width=page.width,height=page.height,images=[])
                for index, raw_image in enumerate(raw):
                    pos=positions[index]
                    item=dict(id=source_id(p,number,'I',index+1), page=number, index=index,
                              embedded_name=raw_image.name, source_size=list(raw_image.image.size),
                              bbox=[pos['x0'],pos['top'],pos['x1'],pos['bottom']],
                              outputs=variants(f"{p['code'].lower()}-p{number:02}-i{index+1:02}",raw_image.image),
                              method="embedded original, complete frame; WebP derivatives without upscaling")
                    # This sketch is rotated in the PDF. Render its final placement correctly.
                    natural=raw_image.image.width/raw_image.image.height
                    shown=(pos['x1']-pos['x0'])/(pos['bottom']-pos['top'])
                    if abs(natural*shown-1)<.05 and abs(natural-shown)>.2:
                        b=item['bbox'];sx=sheet_img.width/page.width;sy=sheet_img.height/page.height
                        corrected=sheet_img.crop((max(0,int(b[0]*sx)),max(0,int(b[1]*sy)),min(sheet_img.width,int(b[2]*sx)),min(sheet_img.height,int(b[3]*sy))))
                        item['display_outputs']=variants(f"{p['code'].lower()}-p{number:02}-i{index+1:02}-placed",corrected)
                        item['method'] += "; displayed derivative preserves the PDF placement rotation"
                    sheet['images'].append(item)
                # Original arrows and vector spiral sit between/around the raster form studies.
                if number==p['concept']:
                    sx=sheet_img.width/page.width;sy=sheet_img.height/page.height
                    crop=sheet_img.crop((int(15*sx),int(550*sy),int(869*sx),int(818*sy)))
                    sheet['diagram']=dict(id=source_id(p,number,'DIAGRAM'),page=number,
                        outputs=variants(f"{p['code'].lower()}-concept-sequence",crop,refresh=True),
                        method="rendered complete concept sequence including vector arrows and source sketches")
                # Individual completed drawings preserve the raster AND vector annotation layers.
                if number in [p['elevations'],p['sections']]:
                    if number==p['elevations'] and p['slug']=='dalawit':
                        regions=[(.015,.035,.56,.47),(.015,.48,.56,.98),(.53,.035,.995,.47),(.53,.48,.995,.98)]
                        titles=['Front elevation','Rear elevation','Left-side elevation','Right-side elevation']
                    elif number==p['elevations']:
                        regions=[(.015,.025,.995,.285),(.015,.265,.995,.525),(.015,.505,.995,.76),(.015,.74,.995,.995)]
                        titles=['Front elevation','Rear elevation','Left-side elevation','Right-side elevation']
                    else:
                        regions=[(.015,.035,.995,.48),(.015,.48,.995,.985)]
                        titles=['Longitudinal section','Cross section'] if p['slug']=='dalawit' else ['Section thru A','Section thru B']
                    sheet['drawings']=[]
                    for i,(region,title) in enumerate(zip(regions,titles),1):
                        b=tuple(int(v*(sheet_img.width if j%2==0 else sheet_img.height)) for j,v in enumerate(region))
                        sheet['drawings'].append(dict(id=source_id(p,number,'D',i),page=number,title=title,
                            outputs=variants(f"{p['code'].lower()}-p{number:02}-drawing-{i}",sheet_img.crop(b)),
                            method="completed drawing cropped from composited source sheet, retaining dimensions and title; full sheet remains inline"))
                pages.append(sheet)
                print(f"Extracted {p['name']} physical page {number}: {len(raw)} image occurrences",flush=True)
            p['pages']=pages
            cp=next(x for x in pages if x['page']==p['concept'])
            body=cp['text'].split('Software: Autocad / Revit / D5',1)[1].split('Keywords:',1)[0]
            p['concept_text']=' '.join(body.split())
            p['keywords']=[word for _,word in sorted((int(n),w) for n,w in re.findall(r'(\d+)\.([A-Za-z]+)',cp['text']))]
            p['metadata']=[['Project Title', re.search(r'Project Title: (.*)',cp['text'])[1]],['Location',re.search(r'Location: (.*)',cp['text'])[1]],['Software','Autocad / Revit / D5']]
            narrative=next(x for x in pages if x['page']==p['narrative'])['text'].split('PERSPECTIVES',1)[1]
            p['perspective_text']=' '.join(re.sub(r'\n\d+\s*$','',narrative).split())
            control=next(x for x in pages if x['page']==p['controls'])['text']
            p['comparison']=[]
            value=r'([\d,.]+(?:\s*(?:sqm|%|meters))?)'
            for label in ['AMBF','PSO','ISA','USA','TOSL','MACA','GFA','FAR','MABH','BHL']:
                found=re.search(r'\b'+label+r'\s+'+value+r'\s+'+label+r'\s+'+value,control)
                if not found:raise ValueError(f"Missing control {p['name']} {label}")
                p['comparison'].append([label,found[1],found[2]])
            names=['Total Lot Area (TLA)','Zoning Classification','Occupancy','Type of Construction','Fire Zone Classification']
            names += ['Required Duplex Units','Provided Duplex Units'] if p['slug']=='dalawit' else ['Required Parking Slots','Provided Parking Slots']
            p['general']=[[label,re.search(re.escape(label)+r' = ([^\n]+)',control)[1]] for label in names]
            p['setbacks']=re.search(r'Front = [^\n]+',control)[0]
            content.append(p)
    return content


COVERAGE=[]


def cover(project,identifier,page,kind,label,target,assets=None,notes=''):
    COVERAGE.append(dict(id=identifier,project=project['name'],page=page,kind=kind,label=label,
                         destination=f"{project['slug']}.html#{target}",assets=assets or [],
                         status='included',notes=notes))


def picture(outputs,alt,items='',cls=''):
    small,big=outputs['640'],outputs['1280']
    return f'''<picture><source media="(max-width:639px)" srcset="{small['path']}"><img class="{cls}" src="{big['path']}" width="{big['width']}" height="{big['height']}" alt="{ESC(alt)}" loading="lazy" decoding="async" data-source="client-pdf" data-coverage="{items}"></picture>'''


def visual(project,item,title,target,whole_sheet=False,moment=False,kind='image',associated=None):
    outputs=item.get('display_outputs',item['outputs'])
    ids=[item['id']]+(associated or [])
    for ident in ids:
        cover(project,ident,item['page'],kind,title,target,[x['path'] for x in outputs.values()],
              'Final composited source sheet retains all vector annotations and raster layers.' if whole_sheet else '')
    full=outputs['full']['path']
    return f'''<section class="section source-section" id="{target}" aria-labelledby="{target}-h"><div class="wrap"><div class="section-head section-head--split"><div><h2 id="{target}-h">{ESC(title)}</h2><p class="t-small muted">Portfolio page {item['page']}</p></div><a class="link" href="{full}" target="_blank" rel="noopener">Open full-size</a></div><figure class="source-figure fill" {'data-moment="picture-develops"' if moment else ''}><a class="source-image m-zoom" href="{full}" target="_blank" rel="noopener" aria-label="Open {ESC(title)} at full resolution">{picture(outputs,project['name']+' — '+title, ' '.join(ids))}</a></figure></div></section>'''


def page_link(sheet):
    return f'<a href="{sheet["outputs"]["full"]["path"]}" target="_blank" rel="noopener">Page {sheet["page"]}</a>'


def build_project(p):
    path=ROOT/(p['slug']+'.html')
    old=path.read_text(encoding='utf-8')
    prefix=old.split('<main id="top">',1)[0]
    hero=re.search(r'<section class="hero\b.*?</section>',old,re.S)[0]
    hero=hero.replace('href="#concept"','href="#contents"').replace('See design concept','See project contents')
    if p['slug']=='lakbay':
        # The split hero is ~628 CSS pixels at 1440: keep a sharp 2x source.
        hero=hero.replace('src="media/lakbay-campus-2000.webp" width="2000" height="1125"',
                          'src="media/lakbay-campus-1280.webp" width="1280" height="720"')
    footer=old[old.rindex('</main>'):]
    if 'complete-portfolio.css' not in prefix:
        prefix=prefix.replace('<link rel="stylesheet" href="site.css">','<link rel="stylesheet" href="site.css">\n<link rel="stylesheet" href="complete-portfolio.css">')
    prefix=prefix.replace('<body>','<body class="complete-project">')
    pages={x['page']:x for x in p['pages']}
    intro=pages[p['start']]
    links=[('concept','Concept'),('development','Design development'),('features','Features and materials'),('controls','Development controls'),('site-plans','Site and floor plans'),('perspectives','Perspectives'),('elevations','Elevations and sections'),('source-sheets','Source sheets')]
    body=hero
    intro_ids=' '.join([intro['id']]+[x['id'] for x in intro['images']])
    body+=f'''<section class="section source-section" id="contents" aria-labelledby="contents-h"><div class="wrap"><div class="section-head"><h2 id="contents-h">{p['name']} project contents</h2></div><div class="grid fill"><nav class="span-6 project-contents" aria-label="{p['name']} project contents">{''.join(f'<a class="m-link" href="#{anchor}"><span>{i:02}</span>{label}</a>' for i,(anchor,label) in enumerate(links,1))}</nav><figure class="source-figure span-6 start-7"><a class="source-image m-zoom" href="{intro['outputs']['full']['path']}" target="_blank" rel="noopener" aria-label="Open original project introduction">{picture(intro['outputs'],p['name']+' original project introduction',intro_ids)}</a></figure></div></div></section>'''
    cover(p,intro['id'],intro['page'],'source-sheet','Complete project introduction','contents',[x['path'] for x in intro['outputs'].values()])
    for im in intro['images']:cover(p,im['id'],intro['page'],'image','Introduction rendering','contents',[x['path'] for x in im['outputs'].values()],'Displayed in its original introduction composition; raw original also retained.')
    cp=pages[p['concept']];concept_image=cp['images'][0]
    text_id=source_id(p,p['concept'],'TEXT')
    meta_id=source_id(p,p['concept'],'META')
    body+=f'''<section class="section source-section source-story" id="concept" aria-labelledby="concept-h"><div class="wrap"><div class="section-head"><h2 id="concept-h">{ESC(p['title'])}</h2></div><div class="grid fill"><div class="span-6 source-prose"><p data-coverage="{text_id}">{ESC(p['concept_text'])}</p><dl class="source-metadata" data-coverage="{meta_id}">{''.join(f'<div><dt>{ESC(k)}</dt><dd>{ESC(v)}</dd></div>' for k,v in p['metadata'])}</dl></div><figure class="source-figure span-6 start-7"><a class="source-image m-zoom" href="{concept_image['outputs']['full']['path']}" target="_blank" rel="noopener" aria-label="Open complete concept rendering">{picture(concept_image['outputs'],p['name']+' complete concept rendering',concept_image['id'])}</a></figure></div></div></section>'''
    cover(p,text_id,cp['page'],'narrative','Complete concept narrative','concept')
    cover(p,meta_id,cp['page'],'metadata','Project title, location, and software','concept')
    cover(p,concept_image['id'],cp['page'],'image','Complete concept rendering','concept',[x['path'] for x in concept_image['outputs'].values()])
    keyword_id=source_id(p,cp['page'],'KEYWORDS')
    sketches=sorted(cp['images'][1:],key=lambda x:x['bbox'][0])
    sketch_html=''
    for i,item in enumerate(sketches,1):
        outputs=item.get('display_outputs',item['outputs']);ident=item['id']
        sketch_html+=f'''<figure class="concept-study"><h3>Concept sketch {i}</h3><a class="source-image m-zoom" href="{outputs['full']['path']}" target="_blank" rel="noopener" aria-label="Open concept sketch {i}">{picture(outputs,p['name']+f' original concept sketch {i}',ident)}</a></figure>'''
        cover(p,ident,cp['page'],'concept-sketch',f'Concept sketch {i}','development',[x['path'] for x in outputs.values()])
    body+=f'''<section class="section source-section" id="development" aria-labelledby="development-h"><div class="wrap"><div class="section-head"><h2 id="development-h">Design development</h2></div><ol class="source-keywords" data-coverage="{keyword_id}">{''.join('<li>'+ESC(k)+'</li>' for k in p['keywords'])}</ol><div class="concept-studies fill">{sketch_html}</div></div></section>'''
    cover(p,keyword_id,cp['page'],'keywords','Complete ordered keyword list','development')
    body+=visual(p,cp['diagram'],'Concept development sequence','concept-sequence',kind='vector-composition')
    feature=pages[p['features']]
    body+='''<section class="section source-section" id="features" aria-labelledby="features-h"><div class="wrap"><div class="section-head"><h2 id="features-h">Design features</h2></div><div class="source-pair fill">'''
    for i in p['feature_indices']:
        item=feature['images'][i];alt=p['alt'][i]
        feature_title='Central gathering space' if p['slug']=='salupod' and i==0 else alt
        body+=f'''<figure class="source-figure"><h3>{ESC(feature_title)}</h3><a class="source-image m-zoom" href="{item['outputs']['full']['path']}" target="_blank" rel="noopener" aria-label="Open {ESC(alt)}">{picture(item['outputs'],p['name']+' — '+alt,item['id'])}</a></figure>'''
        cover(p,item['id'],feature['page'],'design-feature',alt,'features',[x['path'] for x in item['outputs'].values()])
    body+='</div></div></section>'
    body+='''<section class="section source-section source-materials" id="materials" aria-labelledby="materials-h"><div class="wrap"><div class="section-head"><h2 id="materials-h">Material concept</h2></div><div class="material-studies fill">'''
    for index,label in p['materials'].items():
        item=feature['images'][int(index)]
        body+=f'''<figure class="material-study"><h3>{ESC(label)}</h3><a class="source-image m-zoom" href="{item['outputs']['full']['path']}" target="_blank" rel="noopener" aria-label="Open {ESC(label)} material reference">{picture(item['outputs'],label+' material reference from '+p['name'],item['id'])}</a></figure>'''
        cover(p,item['id'],feature['page'],'material',label,'materials',[x['path'] for x in item['outputs'].values()])
    body+='</div></div></section>'
    controls=pages[p['controls']];illustration=controls['images'][0]
    general_id=source_id(p,controls['page'],'GENERAL')
    body+=f'''<section class="section source-section" id="controls" aria-labelledby="controls-h"><div class="wrap"><div class="section-head"><h2 id="controls-h">Development controls</h2></div><div class="grid fill"><dl class="source-general span-6" data-coverage="{general_id}">{''.join(f'<div><dt>{ESC(k)}</dt><dd>{ESC(v)}</dd></div>' for k,v in p['general'])}</dl><figure class="source-figure span-6 start-7" data-moment="picture-develops"><a class="source-image m-zoom" href="{illustration['outputs']['full']['path']}" target="_blank" rel="noopener" aria-label="Open development-control rendering">{picture(illustration['outputs'],p['name']+' development-control rendering',illustration['id'])}</a></figure></div></div></section>'''
    cover(p,general_id,controls['page'],'project-data','All general development-control data','controls')
    cover(p,illustration['id'],controls['page'],'image','Development-control rendering','controls',[x['path'] for x in illustration['outputs'].values()])
    body+='''<section class="section source-section source-control-table" id="control-values" aria-labelledby="control-values-h"><div class="wrap"><div class="section-head"><h2 id="control-values-h">Required and actual values</h2></div><table class="control-table"><thead><tr><th scope="col">Control</th><th scope="col">Required Datas</th><th scope="col">Actual Datas</th></tr></thead><tbody>'''
    for i,(label,required,actual) in enumerate(p['comparison'],1):
        ident=source_id(p,controls['page'],'CONTROL',i)
        body+=f'<tr data-coverage="{ident}"><th scope="row">{label}</th><td>{ESC(required)}</td><td>{ESC(actual)}</td></tr>'
        cover(p,ident,controls['page'],'control-row',f'{label}: required {required}; actual {actual}','control-values')
    setbacks_id=source_id(p,controls['page'],'SETBACKS')
    body+=f'''</tbody></table><p class="source-setbacks" data-coverage="{setbacks_id}">Setbacks: {ESC(p['setbacks'])}</p></div></section>'''
    cover(p,setbacks_id,controls['page'],'setbacks',p['setbacks'],'control-values')
    for i,(number,title) in enumerate(p['plans'].items()):
        sheet=pages[int(number)];anchor='site-plans' if i==0 else f'plan-{number}'
        body+=visual(p,sheet,title,anchor,True,associated=[x['id'] for x in sheet['images']],kind='drawing-sheet')
    for page_index,number in enumerate(p['perspectives']):
        sheet=pages[number]
        for image_index,item in enumerate(sheet['images']):
            anchor='perspectives' if page_index==0 and image_index==0 else f'perspective-{number}-{image_index+1}'
            title=('Facade perspective' if p['slug']!='dalawit' else 'Interior feature wall') if number==p['narrative'] else f'{p["name"]} perspective {sum(len(pages[n]["images"]) for n in p["perspectives"][:page_index])+image_index+1}'
            if number==p['narrative']:
                ident=source_id(p,number,'COMMENTARY')
                body+=f'''<section class="section source-section source-story" id="{anchor}" aria-labelledby="{anchor}-h"><div class="wrap"><div class="section-head"><h2 id="{anchor}-h">{title}</h2></div><div class="grid fill"><p class="source-prose span-6" data-coverage="{ident}" data-moment="word-highlight">{ESC(p['perspective_text'])}</p><figure class="source-figure span-6 start-7"><a class="source-image m-zoom" href="{item['outputs']['full']['path']}" target="_blank" rel="noopener" aria-label="Open {title.lower()}">{picture(item['outputs'],p['name']+' — '+title,item['id'])}</a></figure></div></div></section>'''
                cover(p,item['id'],number,'perspective',title,anchor,[x['path'] for x in item['outputs'].values()]);cover(p,ident,number,'narrative','Complete perspective design explanation',anchor)
            else:
                body+=visual(p,item,title,anchor,kind='perspective')
    for number,anchor in [(p['elevations'],'elevations'),(p['sections'],'sections')]:
        sheet=pages[number]
        body+=visual(p,sheet,'Building '+('elevations' if anchor=='elevations' else 'sections'),anchor,True,associated=[x['id'] for x in sheet['images']],kind='drawing-sheet')
        for i,drawing in enumerate(sheet['drawings'],1):
            body+=visual(p,drawing,drawing['title'],f'{anchor}-{i}',kind='individual-drawing')
    # Every original sheet stays inspectable, including typography, complete page layouts,
    # technical annotations, vector arrows, and layer compositions. This supplements the work above.
    archive_class=' source-archive--compact' if len(p['pages'])<=14 else ''
    body+=f'''<section class="section source-section source-archive{archive_class}" id="source-sheets" aria-labelledby="source-sheets-h"><div class="wrap"><div class="section-head"><h2 id="source-sheets-h">Original portfolio sheets</h2><p>Every original project sheet, with its complete layout and annotations.</p></div><div class="grid fill"><nav class="source-sheet-index span-6" aria-label="Original portfolio sheets">'''
    for sheet in p['pages']:
        body+=f'<a class="m-link" data-coverage="{sheet["id"]}" href="{sheet["outputs"]["full"]["path"]}" target="_blank" rel="noopener">Portfolio page {sheet["page"]}</a>'
        if not any(c['id']==sheet['id'] for c in COVERAGE):
            cover(p,sheet['id'],sheet['page'],'source-sheet','Original source sheet with all annotations','source-sheets',[x['path'] for x in sheet['outputs'].values()],'Supplementary source sheet. Every independent drawing, image, narrative, and data row is also presented above.')
    last=p['pages'][-1]
    body+=f'''</nav><figure class="source-figure span-6 start-7"><a class="source-image m-zoom" href="{last['outputs']['full']['path']}" target="_blank" rel="noopener" aria-label="Open the complete original sections sheet">{picture(last['outputs'],p['name']+' original building sections sheet')}</a></figure></div></div></section>'''
    result=prefix+'<main id="top">'+body+footer
    result=result.replace('class="source-image m-zoom"','class="source-image m-zoom" data-visual')
    path.write_text(result.replace('><','>\n<'),encoding='utf-8')


def reports(content):
    expected={im['id'] for p in content for page in p['pages'] for im in page['images']}
    included={c['id'] for c in COVERAGE}
    if expected-included:raise AssertionError(f"Unmapped image occurrences: {expected-included}")
    if len(included)!=len(COVERAGE):raise AssertionError('Duplicate coverage identifiers')
    write_json(ROOT/'content-coverage.json',COVERAGE)
    write_json(ROOT/'portfolio-content.json',content)
    old_path=ROOT/'asset-manifest.json'
    old=json.loads(old_path.read_text(encoding='utf-8'))
    old=[x for x in old if not x.get('coverage_id')]
    for item in COVERAGE:
        if item['assets']:
            old.append(dict(name=item['label'],coverage_id=item['id'],page=item['page'],project=item['project'],method=item['notes'] or item['kind'],outputs=item['assets'],destination=item['destination']))
    write_json(old_path,old)
    lines=['# Complete project content coverage','', 'Source: physical PDF pages 3–47. Image occurrences are counted per placement, including repeated images and technical-sheet layers. Every independent view is showcased; the complete original sheets retain vector annotations and page composition.','', '| Project | Source pages | Embedded image occurrences | Covered image occurrences | Coverage entries |','| --- | --- | ---: | ---: | ---: |']
    for p in content:
        count=sum(len(x['images']) for x in p['pages']);items=[x for x in COVERAGE if x['project']==p['name']]
        lines.append(f"| {p['name']} | {p['start']}–{p['end']} | {count} | {len([x for x in items if x['id'] in expected])} | {len(items)} |")
    lines+=['','Every item is visible in the project page or, for the supplementary original-sheet record, opens its full original composition. No material, perspective, plan, elevation, section, keyword, narrative, or control value is removed at a mobile breakpoint. The original-sheet links supplement rather than replace individual work.','','## Source details retained','', '- Lakbay and Dalawit text extraction lost a dash and an apostrophe; punctuation was restored without shortening the wording.', '- Source values and labels are transcribed rather than recalculated, including “Terracota”, “Required Datas”, and Dalawit’s “54 slots”.', '- Salupod’s elevation TOB is 12.50 while the section TOB is 12.70; both remain as supplied.', '- Dalawit’s listed PSO is 13.11%; it does not reconcile with listed AMBF divided by lot area. The source values remain unchanged.', '- No independent code-compliance claim is made.', '', '## Item-by-item matrix','', '| ID | PDF page | Kind | Source content | Website destination | Status |','| --- | ---: | --- | --- | --- | --- |']
    for c in COVERAGE:
        lines.append(f"| {c['id']} | {c['page']} | {c['kind']} | {c['label'].replace('|','/')} | [{c['destination']}]({c['destination']}) | Included |")
    (ROOT/'CONTENT_COVERAGE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Complete coverage:',len(expected),'image occurrences;',len(COVERAGE),'total content entries.',flush=True)


def main():
    OUT.mkdir(parents=True,exist_ok=True);AUDIT.mkdir(parents=True,exist_ok=True)
    parser=argparse.ArgumentParser();parser.add_argument('--reuse-extraction',action='store_true');args=parser.parse_args()
    cache=AUDIT/'extracted-content.json'
    if args.reuse_extraction and cache.exists():
        content=json.loads(cache.read_text(encoding='utf-8'))
        # JSON object keys are strings; preserve the source order and numeric material indices.
        for p in content:p['plans']={int(k):v for k,v in p['plans'].items()};p['materials']={int(k):v for k,v in p['materials'].items()};p['alt']={int(k):v for k,v in p['alt'].items()}
        document=pdfium.PdfDocument(str(PDF))
        for p in content:
            sheet=next(x for x in p['pages'] if x['page']==p['concept'])
            im=document[p['concept']-1].render(scale=3400/sheet['width']).to_pil().convert('RGB')
            sx=im.width/sheet['width'];sy=im.height/sheet['height']
            crop=im.crop((int(15*sx),int(550*sy),int(869*sx),int(818*sy)))
            sheet['diagram']['outputs']=variants(f"{p['code'].lower()}-concept-sequence",crop,refresh=True)
            if p.get('derivative_version',0)<2:
                for number in [p['elevations'],p['sections']]:
                    source=next(x for x in p['pages'] if x['page']==number)
                    if number==p['sections']:
                        regions=[(.015,.035,.995,.48),(.015,.48,.995,.985)]
                    elif p['slug']=='dalawit':
                        regions=[(.015,.035,.56,.47),(.015,.48,.56,.98),(.53,.035,.995,.47),(.53,.48,.995,.98)]
                    else:continue
                    im=document[number-1].render(scale=3400/source['width']).to_pil().convert('RGB')
                    for i,(drawing,region) in enumerate(zip(source['drawings'],regions),1):
                        b=tuple(int(v*(im.width if j%2==0 else im.height)) for j,v in enumerate(region))
                        drawing['outputs']=variants(f"{p['code'].lower()}-p{number:02}-drawing-{i}",im.crop(b),refresh=True)
                p['derivative_version']=2
        write_json(cache,content)
    else:
        content=get_source();write_json(cache,content)
    for p in content:
        p['plans']={k:v.replace(' — ',' - ') for k,v in p['plans'].items()}
        build_project(p)
    reports(content)
    supplied=json.loads((ROOT/'SOURCE_COPY_WAIVERS.json').read_text(encoding='utf-8'))
    supplied+=json.loads((ROOT/'SOURCE_LAYOUT_WAIVERS.json').read_text(encoding='utf-8'))
    local=ROOT/'.taste-skill/waivers.json'
    existing=json.loads(local.read_text(encoding='utf-8')) if local.exists() else []
    # The gate abbreviates this source phrase in its finding label. Migrate our
    # earlier full-phrase match instead of leaving a sixth, ineffective waiver.
    existing=[x for x in existing if (x.get('check'),x.get('target')) !=
              ('copy-stock-phrase','not only academic achievement but also')]
    merged=[x for x in existing if (x.get('check'),x.get('target')) not in {(w['check'],w['target']) for w in supplied}]+supplied
    write_json(local,merged)


if __name__=='__main__':main()
