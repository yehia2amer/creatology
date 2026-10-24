# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = ["beautifulsoup4==4.14.3", "PyYAML==6.0.3"]
# ///
"""Preserve unchanged legacy RSS bytes; refresh content feeds after editorial changes."""
import copy, hashlib, json, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit
import yaml
from bs4 import BeautifulSoup
from refresh_content import route_key, timestamp, public_url

CONTENT = 'http://purl.org/rss/1.0/modules/content/'
DC = 'http://purl.org/dc/elements/1.1/'
for prefix, uri in [
    ('content', CONTENT),
    ('dc', DC),
    ('atom', 'http://www.w3.org/2005/Atom'),
    ('sy', 'http://purl.org/rss/1.0/modules/syndication/'),
    ('wfw', 'http://wellformedweb.org/CommentAPI/'),
    ('slash', 'http://purl.org/rss/1.0/modules/slash/')
]:
    ET.register_namespace(prefix, uri)

def set_text(node, tag, value):
    child = node.find(tag)
    if child is None:
        child = ET.SubElement(node, tag)
    child.text = str(value)

def get_taxonomies(front, extra):
    if extra.get('taxonomies'):
        return extra['taxonomies']
    return front.get('taxonomies') or {}

def refresh(site, feed, docs, deleted_routes=None):
    deleted_routes = deleted_routes or set()
    tree = ET.fromstring(feed['xml'])
    channel = tree.find('channel')
    items = channel.findall('item')
    path = feed['path']
    segments = path.strip('/').split('/')
    old = {route_key(i.findtext('link', '')): i for i in items}
    
    # A language element distinguishes content feeds from per-page/global comment feeds.
    if channel.find('language') is None:
        return feed['xml'], False

    taxonomy = segments[0] if len(segments) > 2 and segments[0] in {
        'category', 'post_tag', 'books_taxonomy', 'lectures_taxonomy',
        'training_courses_taxonomy', 'science_taxonomy', 'models_taxonomy'
    } else None
    
    eligible = {}
    for route, doc in docs.items():
        if route in deleted_routes:
            continue
        front = doc['front']
        extra = front.get('extra', {})
        fits = route in old
        if taxonomy:
            fits = unquote(segments[1]) in get_taxonomies(front, extra).get(taxonomy, [])
        elif path == '/feed/':
            fits = extra.get('type') == 'post'
        if fits:
            eligible[route] = doc

    has_deletions = any(route_key(i.findtext('link', '')) in deleted_routes for i in items)
    if not has_deletions and not any(d['changed'] for route, d in docs.items() if route in eligible or route in old):
        return feed['xml'], False

    candidates = []
    for route, doc in eligible.items():
        if doc['front'].get('draft'):
            continue
        front = doc['front']
        extra = front.get('extra', {})
        item = copy.deepcopy(old.get(route))
        if item is None:
            item = ET.Element('item')
            url = public_url(front, route)
            set_text(item, 'link', url)
            set_text(item, 'guid', url)
            set_text(item, '{' + DC + '}creator', extra.get('author', 'Ayman Amer'))
        if doc['changed'] or route not in old:
            set_text(item, 'title', front['title'])
            set_text(item, 'pubDate', format_datetime(datetime.fromtimestamp(timestamp(front.get('date', '')), timezone.utc)))
            if doc['body_changed'] or route not in old:
                rendered = site / 'public' / route.strip('/') / 'index.html'
                body = doc['body']
                if rendered.exists():
                    region = BeautifulSoup(rendered.read_text(encoding='utf-8'), 'html.parser').select_one('[data-content-region]')
                    if region is not None:
                        body = region.decode_contents()
                set_text(item, '{' + CONTENT + '}encoded', body)
                set_text(item, 'description', BeautifulSoup(body, 'html.parser').get_text(' ', strip=True)[:400])
            for category in list(item.findall('category')):
                item.remove(category)
            for terms in get_taxonomies(front, extra).values():
                for term in terms:
                    ET.SubElement(item, 'category').text = term
        candidates.append((timestamp(front.get('date', '')), item))

    # Keep legacy feed items without corresponding native record UNLESS deleted
    candidates.extend((0, copy.deepcopy(item)) for route, item in old.items() if route not in docs and route not in deleted_routes)
    for item in items:
        channel.remove(item)
    candidates.sort(key=lambda pair: pair[0], reverse=True)
    for _, item in candidates[:max(10, len(items))]:
        channel.append(item)
    if candidates:
        set_text(channel, 'lastBuildDate', format_datetime(datetime.fromtimestamp(max(t for t, _ in candidates), timezone.utc)))
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(tree, encoding='unicode'), True

def render(site):
    p = site / 'data/feeds.json'
    if not p.exists():
        return 0
    versions = json.loads((site / 'data/source-versions.json').read_text(encoding='utf-8')) if (site / 'data/source-versions.json').exists() else {}
    body_versions = json.loads((site / 'data/source-body-versions.json').read_text(encoding='utf-8')) if (site / 'data/source-body-versions.json').exists() else {}
    
    route_map_path = site / 'data/source-route-map.json'
    route_map = json.loads(route_map_path.read_text(encoding='utf-8')) if route_map_path.exists() else {}
    deleted_routes = {r for r, k in route_map.items() if not (site / k).exists()}

    docs = {}
    for md in (site / 'content').rglob('*.md'):
        if md.name == '_index.md':
            continue
        raw = md.read_text(encoding='utf-8')
        parts = raw.split('---', 2)
        front = yaml.safe_load(parts[1])
        extra = front.get('extra', {})
        if extra.get('runtime_generated'):
            continue
        key = md.relative_to(site).as_posix()
        body = parts[2].strip()
        r = route_key(front.get('path') or '/' + md.stem + '/')
        docs[r] = {
            'front': front,
            'extra': extra,
            'body': body,
            'changed': versions.get(key) != hashlib.sha256(raw.encode()).hexdigest(),
            'body_changed': body_versions.get(key) != hashlib.sha256(body.encode()).hexdigest()
        }

    seen = set()
    updated = []
    feeds_data = json.loads(p.read_text(encoding='utf-8'))
    for feed in feeds_data:
        path = feed['path']
        target = site / 'public' / path.strip('/') / 'index.html'
        if path in seen:
            continue
        seen.add(path)
        xml, changed = refresh(site, feed, docs, deleted_routes=deleted_routes)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(xml.encode('utf-8'))
        if changed:
            updated.append(path)
        target.with_name('.htaccess').write_text('<Files "index.html">\nForceType application/rss+xml\n</Files>\n', encoding='utf-8')
    
    report = site / '.local/reports/feed-build.json'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({'routes': len(seen), 'updated_routes': updated}), encoding='utf-8')
    return len(seen)

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    site = root if (root / 'zola.toml').exists() else root / 'site'
    print(json.dumps({'feed_routes': render(site)}))
