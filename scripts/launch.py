# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = []
# ///
"""Start the native toolchain through uv without changing shell security policy."""
import os,shutil,subprocess,sys
from pathlib import Path
SITE=Path(__file__).resolve().parents[1]
def main():
 uv=shutil.which('uv') or str(Path.home()/'.local/bin/uv.exe');prefix=[uv,'run','--python',sys.executable];binary=SITE/'.tools'/('zola.exe' if os.name=='nt' else 'zola')
 if not binary.exists():subprocess.run(prefix+[str(SITE/'scripts/bootstrap.py')],check=True,cwd=SITE)
 script='build.py' if len(sys.argv)>1 and sys.argv[1]=='build' else 'dev.py'
 print('Repository: '+str(SITE),flush=True)
 if script=='dev.py':print('Admin: http://localhost:1111/admin/  Preview: http://localhost:1111/',flush=True)
 return subprocess.call(prefix+[str(SITE/'scripts'/script)],cwd=SITE)
if __name__=='__main__':raise SystemExit(main())
