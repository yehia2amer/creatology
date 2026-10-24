# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = ["beautifulsoup4==4.14.3", "PyYAML==6.0.3", "markdown-it-py==4.0.0"]
# ///
"""Refresh native listing data after edits while preserving unchanged legacy excerpts."""
import copy, hashlib, html, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup
import yaml
from markdown_it import MarkdownIt

MARKDOWN = MarkdownIt("commonmark", {"html": True}).enable("table")
PAGE_SIZE = 20

def route_key(value):
    return unquote(urlsplit(value).path).rstrip('/') + '/'

def public_url(front, route=None):
    route = route or front.get('path') or '/'
    original = front.get('extra', {}).get('original_url', '')
    return original if original and route_key(original) == route_key(route) else 'https://draymanamer.com' + route

def timestamp(value):
    try:
        dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return dt.replace(tzinfo=timezone.utc).timestamp() if not dt.tzinfo else dt.timestamp()
    except ValueError:
        return 0

def get_taxonomies(doc):
    front = doc.get('front', {})
    extra = doc.get('extra', {})
    if extra.get('taxonomies'):
        return extra['taxonomies']
    return front.get('taxonomies') or {}

def update(site):
    baseline = json.loads((site / 'data/archives.json').read_text(encoding='utf-8'))
    home = json.loads((site / 'data/home.json').read_text(encoding='utf-8'))
    version_path = site / 'data/source-versions.json'
    versions = json.loads(version_path.read_text(encoding='utf-8')) if version_path.exists() else {}
    body_path = site / 'data/source-body-versions.json'
    body_versions = json.loads(body_path.read_text(encoding='utf-8')) if body_path.exists() else {}
    
    route_map_path = site / 'data/source-route-map.json'
    route_map = json.loads(route_map_path.read_text(encoding='utf-8')) if route_map_path.exists() else {}
    
    docs = {}
    changed = []
    known_routes = set()
    for p in (site / 'content').rglob('*.md'):
        if p.name == '_index.md':
            continue
        raw = p.read_text(encoding='utf-8')
        parts = raw.split('---', 2)
        front = yaml.safe_load(parts[1])
        extra = front.get('extra', {})
        if extra.get('runtime_generated'):
            continue
        key = p.relative_to(site).as_posix()
        h = hashlib.sha256(raw.encode()).hexdigest()
        body = parts[2].strip()
        body_h = hashlib.sha256(body.encode()).hexdigest()
        folder = p.parent.name
        fallback = f'/{folder}/{p.stem}/' if folder not in {'content', 'pages'} else f'/{p.stem}/'
        route = route_key(front.get('path') or fallback)
        known_routes.add(route)
        if not version_path.exists():
            versions[key] = h
        if not body_path.exists():
            body_versions[key] = body_h
        docs[route] = {
            'front': front,
            'extra': extra,
            'body': body,
            'changed': versions.get(key) != h,
            'body_changed': body_versions.get(key) != body_h,
            'type': extra.get('type', 'page'),
            'key': key,
            'route': route
        }
        route_map[route] = key
        if versions.get(key) != h:
            changed.append(route)
        
    deleted_routes = {r for r, k in route_map.items() if not (site / k).exists()}
    if deleted_routes:
        changed.extend(list(deleted_routes))

    if not version_path.exists():
        version_path.write_text(json.dumps(versions, ensure_ascii=False, indent=2), encoding='utf-8')
    if not body_path.exists():
        body_path.write_text(json.dumps(body_versions, ensure_ascii=False, indent=2), encoding='utf-8')

    def refresh(card):
        rk = route_key(card['url'])
        if rk in deleted_routes:
            return None
        doc = docs.get(rk)
        if not doc or not doc['changed']:
            res = copy.deepcopy(card)
            if 'actions' not in res:
                res['actions'] = [{'title': 'التفاصيل', 'url': res.get('url', '')}]
            return res
        if doc['front'].get('draft'):
            return None
        new = copy.deepcopy(card)
        new['title'] = doc['front']['title']
        new['image'] = doc['extra'].get('image', '')
        if 'actions' not in new:
            new['actions'] = [{'title': 'التفاصيل', 'url': new.get('url', '')}]
        if doc['body_changed']:
            words = BeautifulSoup(MARKDOWN.render(doc['body']), 'html.parser').get_text(' ', strip=True).split()
            new['excerpt_html'] = '<p>' + html.escape(' '.join(words[:55])) + (' […]' if len(words) > 55 else '') + '</p>'
        return new

    groups = {}
    for route, archive in baseline.items():
        root = re.sub(r'page/\d+/$', '', route)
        groups.setdefault(root, []).append((route, archive))
    output = copy.deepcopy(baseline)
    new_docs = [d for d in docs.values() if d['key'] not in versions and not d['front'].get('draft')]
    taxonomy_names = set(json.loads((site / 'data/terms.json').read_text(encoding='utf-8')))
    runtime = site / 'content/runtime'
    runtime.mkdir(exist_ok=True)
    runtime_files = set()
    
    for root, pages in groups.items():
        pages.sort(key=lambda pair: int(re.search(r'/page/(\d+)/$', pair[0])[1]) if re.search(r'/page/(\d+)/$', pair[0]) else 1)
        original_cards = [card for _, archive in pages for card in archive['cards'] if route_key(card['url']) not in deleted_routes]
        original_keys = {route_key(c['url']) for c in original_cards}
        types = {docs[route_key(c['url'])]['type'] for c in original_cards if route_key(c['url']) in docs}
        segments = root.strip('/').split('/')
        taxonomy = segments[0] if segments[0] in taxonomy_names else None
        
        additions = []
        for doc in docs.values():
            if doc['front'].get('draft') or not doc['changed']:
                continue
            doc_tax = get_taxonomies(doc)
            # Never inject generic 'page' types into standard post/archive collections
            if taxonomy and len(segments) > 1:
                fits = unquote(segments[1]) in doc_tax.get(taxonomy, [])
            elif root == '/النماذج-التنظيرية/' and doc['type'] in {'models', 'model', 'post'}:
                fits = True
            elif root == '/نحو-التأصيل-لعلم-الإبداع/' and doc['type'] in {'science', 'post'}:
                fits = True
            elif root == '/دورات-مهنية/' and doc['type'] in {'training_courses', 'courses', 'course', 'post'}:
                fits = True
            elif len(types) == 1 and doc['type'] in types and doc['type'] != 'page':
                fits = True
            else:
                fits = False
            if fits and (taxonomy or doc['route'] not in original_keys):
                additions.append(doc)
                
        all_group_cards = [card for _, archive in pages for card in archive.get('cards', [])]
        group_deleted = any(route_key(c['url']) in deleted_routes for c in all_group_cards)
        if not additions and not group_deleted and not any(docs.get(route_key(c['url']), {}).get('changed') for c in original_cards):
            continue
            
        cards = []
        seen = set()
        for doc in additions:
            url = public_url(doc['front'], doc['route'])
            card = refresh({'title': doc['front']['title'], 'url': url, 'image': doc['extra'].get('image', ''), 'excerpt_html': '', 'actions': [{'title': 'التفاصيل', 'url': url}]})
            if card:
                cards.append(card)
                seen.add(doc['route'])
        for card in original_cards:
            key = route_key(card['url'])
            if key in deleted_routes:
                continue
            doc = docs.get(key)
            if taxonomy and doc and doc['changed']:
                doc_tax = get_taxonomies(doc)
                if unquote(segments[1]) not in doc_tax.get(taxonomy, []):
                    continue
            new = refresh(card)
            if new and key not in seen:
                cards.append(new)
                seen.add(key)
                
        cards.sort(key=lambda c: timestamp(docs.get(route_key(c['url']), {}).get('front', {}).get('date', '')), reverse=True)
        count = max(1, (len(cards) + PAGE_SIZE - 1) // PAGE_SIZE)
        base = pages[0][1]
        
        for index in range(1, count + 1):
            route = root if index == 1 else root + 'page/' + str(index) + '/'
            archive = copy.deepcopy(output.get(route, base))
            archive['cards'] = cards[(index - 1) * PAGE_SIZE:index * PAGE_SIZE]
            if count > 1:
                items_html = []
                for n in range(1, count + 1):
                    pg_url = f"https://draymanamer.com{root if n == 1 else root + 'page/' + str(n) + '/'}"
                    if n == index:
                        items_html.append(f'<li class="active"><span class="page current" aria-current="page">{n}</span></li>')
                    else:
                        items_html.append(f'<li><a href="{pg_url}" class="page">{n}</a></li>')
                archive['pagination_html'] = '<ol class="wp-paginate">' + ''.join(items_html) + '</ol>'
            else:
                archive['pagination_html'] = ''
            output[route] = archive
            if route not in known_routes:
                p = runtime / ('listing-' + hashlib.sha256(route.encode()).hexdigest()[:16] + '.md')
                meta = {
                    'title': base['title'],
                    'path': route,
                    'template': 'archive-page.html',
                    'extra': {
                        'wordpress_id': 0,
                        'display_title': base['title'],
                        'archive_source_path': route,
                        'runtime_generated': True
                    }
                }
                p.write_text('---\n' + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + '---\n', encoding='utf-8')
                runtime_files.add(p.name)
                
        for r, _ in pages:
            m = re.search(r'/page/(\d+)/$', r)
            if m and int(m[1]) > count:
                output.pop(r, None)
                
        for rail in home.get('rails', []):
            if route_key(rail.get('view_all', {}).get('url', '')) == root:
                rail['cards'] = cards[:PAGE_SIZE]
                
    for rail in home.get('rails', []):
        rail['cards'] = [new for card in rail['cards'] if (new := refresh(card)) is not None]

    # Synchronize slide/feature/how-we-work edits into home
    feat_map = {'87': 0, '86': 1, '84': 2, '85': 3}
    hww_map = {'1': 0, '2': 1, '3': 2, '4': 3, '89': 0, '90': 1, '91': 2, '92': 3}
    for doc in docs.values():
        if not doc.get('changed'):
            continue
        wp_id = str(doc.get('extra', {}).get('wordpress_id', ''))
        hww_id = str(doc.get('extra', {}).get('source_metadata', {}).get('how_we_work_id_number', ''))
        doc_type = doc.get('type')
        if doc_type in {'slide', 'slides', 'home_slider'}:
            for s in home.get('slides', []):
                if s.get('image') == doc.get('extra', {}).get('image') or not s.get('title'):
                    s['title'] = doc['front']['title']
                    s['alt'] = doc['front']['title']
        elif doc_type in {'feature', 'features', 'home_features'} and wp_id in feat_map:
            idx = feat_map[wp_id]
            if idx < len(home.get('features', [])):
                home['features'][idx]['title'] = doc['front']['title']
        elif (doc_type in {'how_we_work', 'how-we-work'} or wp_id in hww_map) and (hww_id in hww_map or wp_id in hww_map):
            idx = hww_map.get(hww_id, hww_map.get(wp_id))
            if idx is not None and idx < len(home.get('how_we_work', [])):
                home['how_we_work'][idx]['title'] = doc['front']['title']
        
    for p in runtime.glob('listing-*.md'):
        if p.name not in runtime_files:
            metadata = yaml.safe_load(p.read_text(encoding='utf-8').split('---', 2)[1])
            if not metadata.get('extra', {}).get('runtime_generated'):
                raise RuntimeError('Refusing to remove unowned listing: ' + str(p))
            p.unlink()
            
    (runtime / '_index.md').write_text('---\ntitle: Listings\nrender: false\ntransparent: true\n---\n', encoding='utf-8')
    (site / 'data/build-archives.json').write_text(json.dumps(output, ensure_ascii=False), encoding='utf-8')
    (site / 'data/build-home.json').write_text(json.dumps(home, ensure_ascii=False), encoding='utf-8')
    return {'edited_records': len(changed), 'new_published_records': len(new_docs), 'runtime_listing_pages': len(runtime_files)}

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    site = root if (root / 'zola.toml').exists() else root / 'site'
    print(json.dumps(update(site)))
