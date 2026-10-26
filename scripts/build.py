# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = ["beautifulsoup4==4.14.3", "PyYAML==6.0.3", "markdown-it-py==4.0.0"]
# ///
"""Build editable native content, search data and compatibility metadata."""
import argparse, hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path
from urllib.parse import unquote, urlsplit
import yaml
from bs4 import BeautifulSoup

SITE = Path(__file__).resolve().parents[1]
ROOT = SITE / '.local'
(ROOT / 'reports').mkdir(parents=True, exist_ok=True)

def generate_agentic_metadata(site, docs, items):
    base_url = "https://yehia2amer.github.io/creatology"
    toml_path = site / 'zola.toml'
    if toml_path.exists():
        for line in toml_path.read_text(encoding='utf-8').splitlines():
            if line.strip().startswith('base_url'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    base_url = parts[1].strip().strip('"\'').rstrip('/')
    llms_lines = [
        "# د. أيمن عامر — Creatology",
        "",
        "> بوابة علمية وأكاديمية متخصصة في علم النفس المعرفي، وسيكولوجية الإبداع، ونظرية Creatology، وحل المشكلات بطرق إبداعية وتطبيقاتها المعاصرة.",
        "",
        "## الأقسام الرئيسية",
        f"- [الرئيسية]({base_url}/): الصفحة الرئيسية والمدخل العام للبوابة الأكاديمية",
        f"- [عن الموقع]({base_url}/about/): نبذة تعريفية ورؤية البوابة وأهدافها التخصصية",
        f"- [السيرة الذاتية]({base_url}/all_about_us/): السيرة الذاتية والمسيرة العلمية للأستاذ الدكتور أيمن عامر",
        f"- [الكتب والمؤلفات]({base_url}/books/): قائمة الكتب والمؤلفات الأكاديمية في علم النفس وسيكولوجية الإبداع",
        f"- [المحاضرات]({base_url}/lectures/): محاضرات وندوات علمية في التفكير الإبداعي وحل المشكلات",
        f"- [الدورات التدريبية]({base_url}/training_courses/): برامج التدريب وورش العمل المتخصصة",
        f"- [البحوث العلمية]({base_url}/category/%D8%A7%D9%84%D8%A8%D8%AD%D9%88%D8%AB-%D8%A7%D9%84%D8%B9%D9%84%D9%85%D9%8A%D8%A9/): الأوراق البحثية والدراسات المحكمة المنشورة",
        f"- [اتصل بنا]({base_url}/contact/): معلومات التواصل والاستشارات العلمية والمهنية",
        "",
        "## أبرز الكتب والمؤلفات",
    ]
    books = [it for it in items if it.get('type') == 'books' and it.get('title')]
    for b in sorted(books, key=lambda x: str(x.get('title'))):
        llms_lines.append(f"- [{b['title']}]({b['url']})")
        
    llms_lines.extend([
        "",
        "## الدورات والورش التدريبية",
    ])
    courses = [it for it in items if it.get('type') == 'training_courses' and it.get('title')]
    for c in sorted(courses, key=lambda x: str(x.get('title'))):
        llms_lines.append(f"- [{c['title']}]({c['url']})")

    llms_lines.extend([
        "",
        "## الموارد والبيانات التقنية",
        f"- [خريطة الموقع (Sitemap)]({base_url}/sitemap.xml)",
        f"- [فهرس البحث الكامل (Search Data)]({base_url}/search-data.json)",
        f"- [كتالوج الموارد الذكية (AI Catalog)]({base_url}/ai-catalog.json)",
        f"- [خلاصة التحديثات (Feed)]({base_url}/feed/atom.xml)",
        ""
    ])
    llms_content = "\n".join(llms_lines)

    ai_catalog = {
        "specVersion": "1.0",
        "host": {
            "displayName": "د. أيمن عامر — Creatology",
            "identifier": "draymanamer.com",
            "documentationUrl": f"{base_url}/about/",
            "logoUrl": f"{base_url}/wp-content/uploads/2018/09/cropped-logo-1.png"
        },
        "entries": [
            {
                "identifier": "urn:air:draymanamer.com:skills:creatology-academic-guide",
                "displayName": "Creatology Academic & Research Guide",
                "type": "text/markdown; profile=\"urn:air:agent-skills\"",
                "url": f"{base_url}/llms.txt",
                "representativeQueries": [
                    "دكتور أيمن عامر",
                    "سيكولوجية الإبداع ونظرية Creatology",
                    "علم النفس المعرفي وحل المشكلات",
                    "مؤلفات وأبحاث الدكتور أيمن عامر"
                ]
            }
        ]
    }
    ai_catalog_content = json.dumps(ai_catalog, ensure_ascii=False, indent=2)

    for target_dir in [site / 'static', site / 'public']:
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / 'llms.txt').write_text(llms_content, encoding='utf-8')
        (target_dir / 'ai-catalog.json').write_text(ai_catalog_content, encoding='utf-8')
        wk = target_dir / '.well-known'
        wk.mkdir(parents=True, exist_ok=True)
        (wk / 'ai-catalog.json').write_text(ai_catalog_content, encoding='utf-8')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--zola', type=Path)
    a = p.parse_args()
    zola = a.zola or Path(os.environ.get('ZOLA_BINARY', ''))
    if not zola.is_file():
        zola = SITE / '.tools' / ('zola.exe' if os.name == 'nt' else 'zola')
    if not zola.is_file():
        found = shutil.which('zola')
        if not found:
            raise SystemExit('Zola 0.23.6 is required. Run scripts/bootstrap.py using uv.')
        zola = Path(found)
        
    from refresh_content import update, public_url
    updates = update(SITE)
    from media import prepare
    responsive_sources = prepare(SITE)
    protected_path = SITE / 'data/protected-routes.json'
    protected = json.loads(protected_path.read_text(encoding='utf-8')) if protected_path.exists() else {}
    
    docs = []
    routes = {}
    draft_paths = []
    items = []
    
    for md in sorted((SITE / 'content').rglob('*.md')):
        raw = md.read_text(encoding='utf-8')
        parts = raw.split('---', 2)
        front = yaml.safe_load(parts[1])
        extra = front.get('extra', {})
        if md.name == '_index.md':
            continue
            
        original = protected.get(str(extra.get('wordpress_id')))
        if original and unquote(front.get('path', '')).rstrip('/') != unquote(original['path']).rstrip('/'):
            raise SystemExit('Protected original URL changed: ' + str(md))
            
        if front.get('draft'):
            draft_paths.append(front.get('path', ''))
            continue
            
        folder = md.parent.name
        route = front.get('path') or (f'/{folder}/{md.stem}/' if folder not in {'content', 'pages'} else f'/{md.stem}/')
        if route.rstrip('/') in routes:
            raise SystemExit('Duplicate output route ' + route + ' in ' + str(md) + ' and ' + routes[route.rstrip('/')])
            
        routes[route.rstrip('/')] = str(md.relative_to(SITE))
        url = public_url(front, route)
        s = BeautifulSoup(parts[2], 'html.parser')
        doc_type = extra.get('type', 'page')
        is_internal = doc_type in {
            'slide', 'slides', 'feature', 'features', 'how-we-work', 'how_we_work',
            'home_slider', 'home_features'
        } or md.parent.name == 'generated' or '/page/' in route
        is_blog_duplicate = front.get('title') == 'المدونة' and route != '/blog/'
        if not is_internal and not is_blog_duplicate:
            title = front.get('title') or extra.get('display_title') or 'Creatology'
            docs.append({
                'title': title,
                'url': url,
                'text': s.get_text(' ', strip=True) + ' ' + ' '.join(BeautifulSoup(section.get('html', ''), 'html.parser').get_text(' ', strip=True) for section in extra.get('sections', []))
            })
        items.append({
            'id': extra.get('wordpress_id'),
            'route': route,
            'url': url,
            'template': front.get('template'),
            'source': str(md.relative_to(SITE)),
            'type': doc_type,
            'title': front.get('title', ''),
            'date': str(front.get('date', ''))
        })
        
    versions = {key: hashlib.sha256((SITE / 'themes/creatology/static' / filename).read_bytes()).hexdigest()[:16] for key, filename in [('css', 'theme.css'), ('js', 'site.js')]}
    (SITE / 'data/asset-versions.json').write_text(json.dumps(versions), encoding='utf-8')
    (SITE / 'static/search-data.json').write_text(json.dumps(docs, ensure_ascii=False), encoding='utf-8')
    (ROOT / 'reports/local-route-map.json').write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')
    generate_agentic_metadata(SITE, docs, items)
    
    result = subprocess.run([str(zola), '--root', str(SITE), 'build'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    (ROOT / 'reports/build.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    if result.returncode:
        print((result.stdout + result.stderr).encode('ascii', errors='backslashreplace').decode('ascii'))
        raise SystemExit(result.returncode)
        
    from refresh_feeds import render
    feeds_rendered = render(SITE)
    generate_agentic_metadata(SITE, docs, items)
    leak = [r for r in draft_paths if r and (SITE / 'public' / r.strip('/') / 'index.html').exists()]
    if leak:
        raise SystemExit('Draft output detected: ' + repr(leak))
        
    print(json.dumps({
        'feed_routes': feeds_rendered,
        'content_updates': updates,
        'zola': subprocess.check_output([str(zola), '--version'], text=True).strip(),
        'published_content_files': len(items),
        'search_entries': len(docs),
        'draft_routes_absent': len(draft_paths),
        'public_files': sum(1 for f in (SITE / 'public').rglob('*') if f.is_file())
    }, indent=2))

if __name__ == '__main__':
    main()
