"""Check publication candidates for local paths, secrets and unwanted artifacts."""
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def audit(root=ROOT, paths=None):
    root=Path(root)
    if paths is None:
        paths=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=root).decode().split('\0')
    patterns=[r'/home/[A-Za-z0-9_-]+/',r'/mnt/[a-z]/Users/',r'/gpfs/(?:home|projects)/[A-Za-z0-9_-]+/',
              r'gh[pousr]_[A-Za-z0-9]{20,}',r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----']
    private_terms=[v for v in os.environ.get('RPF_PRIVATE_TERMS','').split(';') if v]
    errors=[]
    for name in sorted(set(paths)-{''}):
        path=root/name
        if not path.exists():
            continue
        if path.is_symlink() or path.suffix in {'.pyz','.pdf','.png','.pyc'} or '__pycache__' in path.parts or name=='DEVELOPMENT_CONTEXT.local.md':
            errors.append(name+': unexpected publication artifact');continue
        text=path.read_text()
        if any(re.search(pattern,text) for pattern in patterns) or any(term in text for term in private_terms):
            errors.append(name+': possible private content')
    if errors:
        raise ValueError('\n'.join(errors))
    return len(set(paths)-{''})


if __name__=='__main__':
    try:
        print('Public candidate audit passed ('+str(audit())+' paths checked).')
    except (ValueError,OSError) as exc:
        print(str(exc),file=sys.stderr);raise SystemExit(2)
