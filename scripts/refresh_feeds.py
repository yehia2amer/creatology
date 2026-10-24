# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = ["beautifulsoup4==4.14.3", "PyYAML==6.0.3"]
# ///
"""Preserve unchanged legacy RSS bytes; refresh content feeds after editorial changes."""
import copy,hashlib,json,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import unquote,urlsplit
import yaml
from bs4 import BeautifulSoup
from refresh_content import route_key,timestamp,public_url
CONTENT='http://purl.org/rss/1.0/modules/content/'
DC='http://purl.org/dc/elements/1.1/'
for prefix,uri in [('content',CONTENT),('dc',DC),('atom','http://www.w3.org/2005/Atom'),('sy','http://purl.org/rss/1.0/modules/syndication/'),('wfw','http://wellformedweb.org/CommentAPI/'),('slash','http://purl.org/rss/1.0/modules/slash/')]:ET.register_namespace(prefix,uri)

def set_text(node,tag,value):
    child=node.find(tag)
    if child is None:child=ET.SubElement(node,tag)
    child.text=str(value)

def get_taxonomies(front,extra):
    if extra.get('taxonomies'):
        return extra['taxonomies']
    return front.get('taxonomies') or {}

def refresh(site,feed,docs):
    tree=ET.fromstring(feed['xml']);channel=tree.find('channel');items=channel.findall('item');path=feed['path'];segments=path.strip('/').split('/');old={route_key(i.findtext('link','')):i for i in items}
    # A language element distinguishes content feeds from per-page/global comment feeds.
    if channel.find('language') is None:return feed['xml'],False
    
    route_map_path=site/'data/source-route-map.json'
    route_map=json.loads(route_map_path.read_text(encoding='utf-8')) if route_map_path.exists() else {}
    deleted_routes={r for r,k in route_map.items() if not (site/k).exists()}

    taxonomy=segments[0] if len(segments)>2 and segments[0] in {'category','post_tag','books_taxonomy','lectures_taxonomy','training_courses_taxonomy','science_taxonomy','models_taxonomy'} else None
    eligible={}
    for route,doc in docs.items():
        if route in deleted_routes:continue
        front=doc['front'];extra=front.get('extra',{});fits=route in old
        if taxonomy:fits=unquote(segments[1]) in get_taxonomies(front,extra).get(taxonomy,[])
        elif path=='/feed/':fits=extra.get('type')=='post'
        if fits:eligible[route]=doc
        
    has_deletions=any(route_key(i.findtext('link','')) in deleted_routes for i in items)
    if not has_deletions and not any(d['changed'] for route,d in docs.items() if route in eligible or route in old):return feed['xml'],False
    
    candidates=[]
    for route,doc in eligible.items():
        if doc['front'].get('draft'):continue
        front=doc['front'];extra=front.get('extra',{});item=copy.deepcopy(old.get(route))
        if item is None:
            item=ET.Element('item');url=public_url(front,route)
            set_text(item,'link',url);set_text(item,'guid',url);set_text(item,'{'+DC+'}creator',extra.get('author','Ayman Amer'))
        if doc['changed'] or item is None:
            set_text(item,'title',front['title']);set_text(item,'pubDate',format_datetime(datetime.fromtimestamp(timestamp(front.get('date','')),timezone.utc)))
            if doc['body_changed'] or route not in old:
                rendered=site/'public'/route.strip('/')/'index.html'
                body=doc['body']
                if rendered.exists():
                    region=BeautifulSoup(rendered.read_text(encoding='utf-8'),'html.parser').select_one('[data-content-region]')
                    if region is not None:body=region.decode_contents()
                set_text(item,'{'+CONTENT+'}encoded',body);set_text(item,'description',BeautifulSoup(body,'html.parser').get_text(' ',strip=True)[:400])
            for category in list(item.findall('category')):item.remove(category)
            for terms in get_taxonomies(front,extra).values():
                for term in terms:ET.SubElement(item,'category').text=term
        candidates.append((timestamp(front.get('date','')),item))
        
    # Keep any legacy feed item without a corresponding native record, UNLESS it was deleted
    candidates.extend((0,copy.deepcopy(item)) for route,item in old.items() if route not in docs and route not in deleted_routes)
    for item in items:channel.remove(item)
    candidates.sort(key=lambda pair:pair[0],reverse=True)
    for _,item in candidates[:max(10,len(items))]:channel.append(item)
    if candidates:set_text(channel,'lastBuildDate',format_datetime(datetime.fromtimestamp(max(t for t,_ in candidates),timezone.utc)))
    return '<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(tree,encoding='unicode'),True

def render(site):
    feeds_spec=json.loads((site/'data/feeds.json').read_text(encoding='utf-8'))
    docs={}
    for p in (site/'content').rglob('*.md'):
        if p.name=='_index.md':continue
        raw=p.read_text(encoding='utf-8');parts=raw.split('---',2);front=yaml.safe_load(parts[1]);extra=front.get('extra',{})
        if extra.get('runtime_generated'):continue
        route=route_key(front.get('path') or '/'+p.stem+'/')
        docs[route]={'front':front,'extra':extra,'body':parts[2].strip(),'changed':True,'body_changed':True}
    rendered=0
    for item in feeds_spec:
        xml,changed=refresh(site,item,docs)
        if changed:item['xml']=xml;rendered+=1
        out=site/'static'/item['path'].strip('/')/'index.xml'
        out.parent.mkdir(parents=True,exist_ok=True);out.write_text(item['xml'],encoding='utf-8')
    (site/'data/feeds.json').write_text(json.dumps(feeds_spec,ensure_ascii=False),encoding='utf-8')
    return rendered

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];site=root if (root/'zola.toml').exists() else root/'site';print(render(site))
