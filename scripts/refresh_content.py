# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = ["beautifulsoup4==4.14.3", "PyYAML==6.0.3", "markdown-it-py==4.0.0"]
# ///
"""Refresh native listing data after edits while preserving unchanged legacy excerpts."""
import copy,hashlib,html,json,re
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import unquote,urlsplit
from bs4 import BeautifulSoup
import yaml
from markdown_it import MarkdownIt
MARKDOWN=MarkdownIt("commonmark",{"html":True}).enable("table")
PAGE_SIZE=20

def route_key(value):return unquote(urlsplit(value).path).rstrip('/')+'/'
def public_url(front,route=None):
    route=route or front.get('path') or '/'
    original=front.get('extra',{}).get('original_url','')
    return original if original and route_key(original)==route_key(route) else 'https://draymanamer.com'+route

def timestamp(value):
    try:return datetime.fromisoformat(str(value).replace('Z','+00:00')).replace(tzinfo=timezone.utc).timestamp() if not datetime.fromisoformat(str(value).replace('Z','+00:00')).tzinfo else datetime.fromisoformat(str(value).replace('Z','+00:00')).timestamp()
    except ValueError:return 0

def update(site):
    baseline=json.loads((site/'data/archives.json').read_text(encoding='utf-8'));home=json.loads((site/'data/home.json').read_text(encoding='utf-8'));version_path=site/'data/source-versions.json';versions=json.loads(version_path.read_text(encoding='utf-8')) if version_path.exists() else {};body_path=site/'data/source-body-versions.json';body_versions=json.loads(body_path.read_text(encoding='utf-8')) if body_path.exists() else {};docs={};changed=[];known_routes=set()
    for p in (site/'content').rglob('*.md'):
        if p.name=='_index.md':continue
        raw=p.read_text(encoding='utf-8');parts=raw.split('---',2);front=yaml.safe_load(parts[1]);extra=front.get('extra',{})
        if extra.get('runtime_generated'):continue
        key=p.relative_to(site).as_posix();hash=hashlib.sha256(raw.encode()).hexdigest();body=parts[2].strip();body_hash=hashlib.sha256(body.encode()).hexdigest();route=route_key(front.get('path') or '/'+p.stem+'/');known_routes.add(route)
        if not version_path.exists():versions[key]=hash
        if not body_path.exists():body_versions[key]=body_hash
        docs[route]={'front':front,'extra':extra,'body':body,'changed':versions.get(key)!=hash,'body_changed':body_versions.get(key)!=body_hash,'type':extra.get('type','page'),'key':key,'route':route}
        if versions.get(key)!=hash:changed.append(route)
    if not version_path.exists():version_path.write_text(json.dumps(versions,ensure_ascii=False,indent=2),encoding='utf-8')
    if not body_path.exists():body_path.write_text(json.dumps(body_versions,ensure_ascii=False,indent=2),encoding='utf-8')
    def refresh(card):
        doc=docs.get(route_key(card['url']))
        if not doc or not doc['changed']:return copy.deepcopy(card)
        if doc['front'].get('draft'):return None
        new=copy.deepcopy(card);new['title']=doc['front']['title'];new['image']=doc['extra'].get('image','')
        if doc['body_changed']:
            words=BeautifulSoup(MARKDOWN.render(doc['body']),'html.parser').get_text(' ',strip=True).split();new['excerpt_html']='<p>'+html.escape(' '.join(words[:55]))+(' […]' if len(words)>55 else '')+'</p>'
        return new
    groups={}
    for route,archive in baseline.items():
        root=re.sub(r'page/\d+/$','',route);groups.setdefault(root,[]).append((route,archive))
    output=copy.deepcopy(baseline);new_docs=[d for d in docs.values() if d['key'] not in versions and not d['front'].get('draft')]
    taxonomy_names=set(json.loads((site/'data/terms.json').read_text(encoding='utf-8')))
    runtime=site/'content/runtime';runtime.mkdir(exist_ok=True);runtime_files=set()
    for root,pages in groups.items():
        pages.sort(key=lambda pair:int(re.search(r'/page/(\d+)/$',pair[0])[1]) if re.search(r'/page/(\d+)/$',pair[0]) else 1)
        original_cards=[card for _,archive in pages for card in archive['cards']];original_keys={route_key(c['url']) for c in original_cards};types={docs[route_key(c['url'])]['type'] for c in original_cards if route_key(c['url']) in docs};segments=root.strip('/').split('/');taxonomy=segments[0] if segments[0] in taxonomy_names else None
        additions=[]
        for doc in docs.values():
            if doc['front'].get('draft') or not doc['changed']:continue
            fits=(unquote(segments[1]) in doc['front'].get('taxonomies',{}).get(taxonomy,[])) if taxonomy and len(segments)>1 else len(types)==1 and doc['type'] in types
            if fits and (taxonomy or doc['route'] not in original_keys):additions.append(doc)
        if not additions and not any(docs.get(route_key(c['url']),{}).get('changed') for c in original_cards):continue
        cards=[];seen=set()
        for doc in additions:
            url=public_url(doc['front'],doc['route']);card=refresh({'title':doc['front']['title'],'url':url,'image':doc['extra'].get('image',''),'excerpt_html':''})
            if card:cards.append(card);seen.add(doc['route'])
        for card in original_cards:
            key=route_key(card['url']);doc=docs.get(key)
            if taxonomy and doc and doc['changed'] and unquote(segments[1]) not in doc['front'].get('taxonomies',{}).get(taxonomy,[]):continue
            new=refresh(card)
            if new and key not in seen:cards.append(new);seen.add(key)
        cards.sort(key=lambda c:timestamp(docs.get(route_key(c['url']),{}).get('front',{}).get('date','')),reverse=True)
        count=max(len(pages),(len(cards)+PAGE_SIZE-1)//PAGE_SIZE,1);base=pages[0][1]
        for index in range(1,count+1):
            route=root if index==1 else root+'page/'+str(index)+'/'
            archive=copy.deepcopy(output.get(route,base));archive['cards']=cards[(index-1)*PAGE_SIZE:index*PAGE_SIZE]
            if count!=len(pages):archive['pagination_html']='<ol>'+''.join('<li><a href="https://draymanamer.com'+(root if n==1 else root+'page/'+str(n)+'/')+'">'+str(n)+'</a></li>' for n in range(1,count+1))+'</ol>'
            output[route]=archive
            if route not in known_routes:
                p=runtime/('listing-'+hashlib.sha256(route.encode()).hexdigest()[:16]+'.md');meta={'title':base['title'],'path':route,'template':'archive-page.html','extra':{'wordpress_id':0,'display_title':base['title'],'archive_source_path':route,'runtime_generated':True}};p.write_text('---\n'+yaml.safe_dump(meta,allow_unicode=True,sort_keys=False)+'---\n',encoding='utf-8');runtime_files.add(p.name)
        for rail in home['rails']:
            if route_key(rail.get('view_all',{}).get('url',''))==root:rail['cards']=cards[:PAGE_SIZE]
    for rail in home['rails']:rail['cards']=[new for card in rail['cards'] if (new:=refresh(card)) is not None]
    for p in runtime.glob('listing-*.md'):
        if p.name not in runtime_files:
            metadata=yaml.safe_load(p.read_text(encoding='utf-8').split('---',2)[1])
            if not metadata.get('extra',{}).get('runtime_generated'):raise RuntimeError('Refusing to remove unowned listing: '+str(p))
            p.unlink()
    (runtime/'_index.md').write_text('---\ntitle: Listings\nrender: false\ntransparent: true\n---\n',encoding='utf-8')
    (site/'data/build-archives.json').write_text(json.dumps(output,ensure_ascii=False),encoding='utf-8');(site/'data/build-home.json').write_text(json.dumps(home,ensure_ascii=False),encoding='utf-8')
    return {'edited_records':len(changed),'new_published_records':len(new_docs),'runtime_listing_pages':len(runtime_files)}
if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];site=root if (root/'zola.toml').exists() else root/'site';print(json.dumps(update(site)))
