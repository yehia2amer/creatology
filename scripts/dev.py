# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = []
# ///
"""Run a stable admin server and rebuild visitor pages after local editor saves."""
import argparse,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def snapshots(site):
    paths=[]
    for folder in ('content','themes','static','data'):
        paths.extend(p for p in (site/folder).rglob('*') if p.is_file() and p.name not in ('build-home.json','build-archives.json','search-data.json','source-versions.json','source-body-versions.json','media.json','asset-versions.json') and 'processed_images' not in p.parts and 'runtime' not in p.parts)
    return {str(p):(p.stat().st_mtime_ns,p.stat().st_size) for p in paths}
def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=1111);a=p.parse_args();site=ROOT if (ROOT/'zola.toml').exists() else ROOT/'site';scripts=Path(__file__).resolve().parent
    uv=shutil.which('uv') or str(Path.home()/'.local/bin/uv.exe');prefix=[uv,'run','--python',sys.executable]
    subprocess.run(prefix+[str(scripts/'build.py')],check=True)
    server=subprocess.Popen(prefix+[str(scripts/'serve.py'),'--port',str(a.port)])
    print('Watching content. Save in Sveltia, then refresh the visitor preview. Admin stays open.',flush=True);previous=snapshots(site)
    try:
        while server.poll() is None:
            time.sleep(1);current=snapshots(site)
            if current!=previous:
                time.sleep(.4);subprocess.run(prefix+[str(scripts/'build.py')]);previous=snapshots(site)
    except KeyboardInterrupt:pass
    finally:
        server.terminate();server.wait(timeout=10)
if __name__=='__main__':main()
