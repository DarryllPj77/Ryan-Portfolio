"""Independently verify the built site against the PDF and the coverage ledger."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import re
import sys

import pdfplumber
from pypdf import PdfReader
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
PROJECTS=[('salupod','SAL',3,17,4,6,13),('lakbay','LAK',18,34,19,21,30),('dalawit','DAL',35,47,36,38,42)]
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}


class Node:
    def __init__(self,tag,attrs=None,parent=None):
        self.tag=tag;self.attrs=dict(attrs or []);self.parent=parent;self.children=[]
    def text(self):
        return ''.join(c if isinstance(c,str) else c.text() for c in self.children)


class Document(HTMLParser):
    def __init__(self,path):
        super().__init__();self.root=Node('root');self.stack=[self.root];self.nodes=[]
        self.feed(path.read_text(encoding='utf-8'))
    def handle_starttag(self,tag,attrs):
        n=Node(tag,attrs,self.stack[-1]);self.stack[-1].children.append(n);self.nodes.append(n)
        if tag not in VOID:self.stack.append(n)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:self.stack=self.stack[:i];break
    def handle_data(self,data):self.stack[-1].children.append(data)


def normalized(text):return ' '.join(text.split())
def repaired(text):return text.replace('student�from','student—from').replace('students�','students’').replace('Duality � Interlocked','Duality – Interlocked')


def main():
    errors=[];counts={};references=0
    ledger=json.loads((ROOT/'content-coverage.json').read_text(encoding='utf-8'))
    records={r['id']:r for r in ledger}
    if len(records)!=len(ledger):errors.append('Duplicate identifiers in coverage ledger')
    docs={p.name:Document(p) for p in ROOT.glob('*.html')}
    reader=PdfReader(ROOT/'LADESMA - PORTFOLIO.pdf')
    with pdfplumber.open(ROOT/'LADESMA - PORTFOLIO.pdf') as pdf:
        for slug,code,start,end,concept,controls,commentary in PROJECTS:
            doc=docs[slug+'.html'];ids=[n.attrs['id'] for n in doc.nodes if 'id'in n.attrs]
            if len(ids)!=len(set(ids)):errors.append(slug+': duplicate HTML id')
            if sum(n.tag=='h1' for n in doc.nodes)!=1:errors.append(slug+': expected exactly one h1')
            located={}
            for n in doc.nodes:
                for item in n.attrs.get('data-coverage','').split():located.setdefault(item,[]).append(n)
            expected=[]
            for page in range(start,end+1):
                for i,_ in enumerate(reader.pages[page-1].images,1):
                    identifier=f'{code}-P{page:02}-I{i:02}';expected.append(identifier)
                    if identifier not in records:errors.append(identifier+': absent from ledger')
                    if not any(n.tag=='img' for n in located.get(identifier,[])):
                        errors.append(identifier+': not associated with an inline image')
                sheet=f'{code}-P{page:02}-SHEET'
                if sheet not in located:errors.append(sheet+': original sheet not reachable')
            text=repaired(pdf.pages[concept-1].extract_text())
            original=normalized(text.split('Software: Autocad / Revit / D5',1)[1].split('Keywords:',1)[0])
            ident=f'{code}-P{concept:02}-TEXT'
            actual=normalized(' '.join(n.text() for n in located.get(ident,[])))
            if actual!=original:errors.append(ident+': full concept narrative differs from source')
            source_comment=repaired(pdf.pages[commentary-1].extract_text()).split('PERSPECTIVES',1)[1]
            source_comment=normalized(re.sub(r'\n\d+\s*$','',source_comment))
            ident=f'{code}-P{commentary:02}-COMMENTARY'
            actual=normalized(' '.join(n.text() for n in located.get(ident,[])))
            if actual!=source_comment:errors.append(ident+': full perspective narrative differs from source')
            keyword_pairs=sorted((int(i),word) for i,word in re.findall(r'(\d+)\.([A-Za-z]+)',text))
            ident=f'{code}-P{concept:02}-KEYWORDS'
            nodes=located.get(ident,[])
            actual=[normalized(c.text()) for n in nodes for c in n.children if isinstance(c,Node) and c.tag=='li']
            if actual!=[w for _,w in keyword_pairs]:errors.append(ident+': keyword list incomplete or reordered')
            source_control=pdf.pages[controls-1].extract_text()
            metrics=['AMBF','PSO','ISA','USA','TOSL','MACA','GFA','FAR','MABH','BHL']
            for i,label in enumerate(metrics,1):
                ident=f'{code}-P{controls:02}-CONTROL{i:02}'
                nodes=located.get(ident,[])
                cells=[normalized(c.text()) for n in nodes for c in n.children if isinstance(c,Node) and c.tag in ['th','td']]
                if len(cells)!=3 or cells[0]!=label:
                    errors.append(ident+': comparison row missing');continue
                pattern=re.escape(label)+r'\s+'+re.escape(cells[1])+r'\s+'+re.escape(label)+r'\s+'+re.escape(cells[2])
                if not re.search(pattern,source_control):errors.append(ident+': comparison values differ from PDF')
            for record in (r for r in ledger if r['project'].lower()==slug):
                ident=record['id'];target=record['destination'].split('#')[1]
                if target not in ids:errors.append(ident+': destination missing')
                if ident not in located:errors.append(ident+': no DOM coverage marker')
                for filename in record['assets']:
                    if not (ROOT/filename).is_file():errors.append(ident+': asset missing '+filename)
            for n in doc.nodes:
                if n.tag=='img':
                    if not n.attrs.get('alt'):errors.append(slug+': unnamed image')
                    for p in [n.parent,n.parent.parent if n.parent else None]:
                        if p and re.search(r'display\s*:\s*none|visibility\s*:\s*hidden',p.attrs.get('style','')):
                            errors.append(slug+': hidden work '+n.attrs.get('src',''))
                if n.tag=='a' and 'source-image' in n.attrs.get('class','').split():
                    if n.attrs.get('target')!='_blank':errors.append(slug+': full-size image lacks native inspection link')
            counts[slug]={'source_pages':end-start+1,'embedded_image_occurrences':len(expected),
                          'covered_image_occurrences':sum(any(n.tag=='img' for n in located.get(i,[])) for i in expected),
                          'coverage_entries':sum(r['project'].lower()==slug for r in ledger),
                          'html_sections':sum(n.tag=='section' for n in doc.nodes)}
    for name,doc in docs.items():
        for n in doc.nodes:
            paths=[n.attrs[k] for k in ['href','src'] if k in n.attrs]
            paths += [p.strip().split()[0] for p in n.attrs.get('srcset','').split(',') if p.strip()]
            for ref in paths:
                url=urlsplit(ref)
                if url.scheme or url.netloc:continue
                target=ROOT/unquote(url.path) if url.path else ROOT/name;references+=1
                if not target.is_file():errors.append(name+': missing reference '+ref)
                elif url.fragment and target.name in docs:
                    if not any(x.attrs.get('id')==url.fragment for x in docs[target.name].nodes):errors.append(name+': missing anchor '+ref)
                if target.suffix=='.webp' and target.is_file():
                    with Image.open(target) as im:im.verify()
    css=(ROOT/'complete-portfolio.css').read_text(encoding='utf-8')
    if re.search(r'display\s*:\s*none|visibility\s*:\s*hidden',css):errors.append('Project stylesheet hides content')
    if '.wall > :nth-child(2) { display: none; }' in (ROOT/'site.css').read_text():errors.append('Homepage work still hidden on phones')
    report={'projects':counts,'references':references,'errors':errors}
    dest=ROOT/'.taste-skill/complete-audit/coverage-verification.json';dest.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    if errors:sys.exit(1)


if __name__=='__main__':main()
