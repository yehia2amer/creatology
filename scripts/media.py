# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""Map existing local raster images for native Zola responsive derivatives."""
import json
from pathlib import Path
from urllib.parse import unquote,urlsplit
import yaml

def prepare(site):
    urls=set()
    for file in ['data/build-home.json','data/build-archives.json']:
        data=json.loads((site/file).read_text(encoding='utf-8'))
        def visit(value):
            if isinstance(value,dict):
                if value.get('image'):urls.add(value['image'])
                for child in value.values():visit(child)
            elif isinstance(value,list):
                for child in value:visit(child)
        visit(data)
    for p in (site/'content').rglob('*.md'):
        raw=p.read_text(encoding='utf-8');m=yaml.safe_load(raw.split('---',2)[1]);image=m.get('extra',{}).get('image')
        if image:urls.add(image)
    images={};base=(site/'static').resolve()
    for url in sorted(urls):
        u=urlsplit(url)
        if u.hostname not in (None,'draymanamer.com') or u.query or u.fragment:continue
        relative=unquote(u.path).lstrip('/');path=(base/relative).resolve()
        if path.is_relative_to(base) and path.is_file() and path.suffix.lower() in ('.jpg','.jpeg','.png','.webp'):images[url]='static/'+relative
    (site/'data/media.json').write_text(json.dumps(images,ensure_ascii=False),encoding='utf-8');return len(images)
if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];site=root if (root/'zola.toml').exists() else root/'site';print(prepare(site))
