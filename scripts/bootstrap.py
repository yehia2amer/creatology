# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = []
# ///
"""Install the pinned official Zola release into this repository's private .tools directory."""
import hashlib,io,json,platform,tarfile,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    target=ROOT/'.tools';target.mkdir(parents=True,exist_ok=True)
    system=platform.system();machine=platform.machine().lower();suffix='x86_64-pc-windows-msvc.zip' if system=='Windows' else ('aarch64-apple-darwin.tar.gz' if machine in ('arm64','aarch64') else 'x86_64-apple-darwin.tar.gz') if system=='Darwin' else 'x86_64-unknown-linux-gnu.tar.gz'
    name='zola-v0.23.6-'+suffix;release=json.load(urllib.request.urlopen('https://api.github.com/repos/getzola/zola/releases/tags/v0.23.6'));asset=next(a for a in release['assets'] if a['name']==name);blob=urllib.request.urlopen(asset['browser_download_url']).read();hash=hashlib.sha256(blob).hexdigest()
    if asset.get('digest') and asset['digest']!='sha256:'+hash:raise SystemExit('Official asset digest mismatch')
    if suffix.endswith('.zip'):
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:data=archive.read('zola.exe')
    else:
        with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as archive:data=archive.extractfile(next(m for m in archive.getmembers() if Path(m.name).name=='zola')).read()
    binary=target/('zola.exe' if system=='Windows' else 'zola');binary.write_bytes(data)
    if system!='Windows':binary.chmod(0o755)
    (target/'provenance.json').write_text(json.dumps({'version':'0.23.6','source':asset['browser_download_url'],'download_sha256':hash},indent=2),encoding='utf-8')
    if not (ROOT/'.git').exists():
        import subprocess
        subprocess.run(['git','init'],cwd=ROOT,check=False)
        subprocess.run(['git','config','core.longpaths','true'],cwd=ROOT,check=False)
    print(str(binary))
if __name__=='__main__':main()
