# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = ["beautifulsoup4==4.14.3", "PyYAML==6.0.3", "markdown-it-py==4.0.0"]
# ///
"""Build editable native content, search data and compatibility metadata."""
import argparse,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
from urllib.parse import unquote,urlsplit
import yaml
from bs4 import BeautifulSoup
SITE=Path(__file__).resolve().parents[1];ROOT=SITE/'.local';(ROOT/'reports').mkdir(parents=True,exist_ok=True)
def main():
    p=argparse.ArgumentParser();p.add_argument('--zola',type=Path);a=p.parse_args()
    zola=a.zola or Path(os.environ.get('ZOLA_BINARY',''))
    if not zola.is_file():zola=SITE/'.tools'/('zola.exe' if os.name=='nt' else 'zola')
    if not zola.is_file():
        found=shutil.which('zola')
        if not found:raise SystemExit('Zola 0.23.6 is required. Run scripts/bootstrap.py using uv.')
        zola=Path(found)
    from refresh_content import update,public_url
    updates=update(SITE)
    from media import prepare
    responsive_sources=prepare(SITE)
    protected_path=SITE/'data/protected-routes.json'
    protected=json.loads(protected_path.read_text(encoding='utf-8')) if protected_path.exists() else {}
    docs=[];routes={};draft_paths=[];items=[]
    for md in sorted((SITE/'content').rglob('*.md')):
        raw=md.read_text(encoding='utf-8');parts=raw.split('---',2);front=yaml.safe_load(parts[1]);extra=front.get('extra',{})
        if md.name=='_index.md':continue
        original=protected.get(str(extra.get('wordpress_id')))
        if original and unquote(front.get('path','')).rstrip('/')!=unquote(original['path']).rstrip('/'):
            front['path']=original['path']
        if front.get('draft'):
            draft_paths.append(front.get('path',''));continue
        folder=md.parent.name
        route=front.get('path') or (f'/{folder}/{md.stem}/' if folder not in {'content','pages'} else f'/{md.stem}/')
        if route.rstrip('/') in routes:
            route=f'/{folder}/{md.stem}/'
        routes[route.rstrip('/')]=str(md.relative_to(SITE));url=public_url(front,route)
        s=BeautifulSoup(parts[2],'html.parser')
        doc_type=extra.get('type','page')
        if doc_type not in {'slide','slides','feature','features','how-we-work','how_we_work'}:
            title=front.get('title') or extra.get('display_title') or 'Creatology'
            docs.append({'title':title,'url':url,'text':s.get_text(' ',strip=True)+' '+' '.join(BeautifulSoup(section.get('html',''),'html.parser').get_text(' ',strip=True) for section in extra.get('sections',[]))})
        items.append({'id':extra.get('wordpress_id'),'route':route,'url':url,'template':front.get('template'),'source':str(md.relative_to(SITE)),'type':doc_type,'title':front.get('title',''),'date':str(front.get('date',''))})
    versions={key:hashlib.sha256((SITE/'themes/creatology/static'/filename).read_bytes()).hexdigest()[:16] for key,filename in [('css','theme.css'),('js','site.js')]}
    (SITE/'data/asset-versions.json').write_text(json.dumps(versions),encoding='utf-8')
    (SITE/'static/search-data.json').write_text(json.dumps(docs,ensure_ascii=False),encoding='utf-8')
    (ROOT/'reports/local-route-map.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
    result=subprocess.run([str(zola),'--root',str(SITE),'build'],capture_output=True,text=True,encoding='utf-8',errors='replace')
    (ROOT/'reports/build.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:print((result.stdout+result.stderr).encode('ascii',errors='backslashreplace').decode('ascii'));raise SystemExit(result.returncode)
    from refresh_feeds import render
    feeds_rendered=render(SITE)
    leak=[r for r in draft_paths if r and (SITE/'public'/r.strip('/')/'index.html').exists()]
    if leak:raise SystemExit('Draft output detected: '+repr(leak))
    print(json.dumps({'feed_routes':feeds_rendered,'content_updates':updates,'zola':subprocess.check_output([str(zola),'--version'],text=True).strip(),'published_content_files':len(items),'search_entries':len(docs),'draft_routes_absent':len(draft_paths),'public_files':sum(1 for f in (SITE/'public').rglob('*') if f.is_file())},indent=2))
if __name__=='__main__':main()
