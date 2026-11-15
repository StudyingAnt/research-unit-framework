"""Export a clean committed source tree as a browsable release, with its checksum."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode=True
from _framework import ROOT
from audit_public import audit


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'dist')
    args=parser.parse_args()
    try:
        if subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=ROOT).strip():
            raise ValueError('Commit/review the source first; releases require a clean tree')
        audit()
        version=(ROOT/'VERSION').read_text().strip()
        if json.loads((ROOT/'template-manifest.json').read_text())['version']!=version:
            raise ValueError('Version and template manifest disagree')
        output=args.output.expanduser().absolute();output.mkdir(parents=True,exist_ok=True)
        filename='research-program-framework-'+version+'.tar.gz'
        archive=output/filename
        with archive.open('xb') as stream:
            subprocess.run(['git','archive','--format=tar.gz','--prefix=research-program-framework-'+version+'/', 'HEAD'],cwd=ROOT,stdout=stream,check=True)
        checksum=hashlib.sha256(archive.read_bytes()).hexdigest()
        (output/(filename+'.sha256')).write_text(checksum+'  '+filename+'\n')
        print(str(archive))
        return 0
    except (ValueError,OSError,subprocess.CalledProcessError) as exc:
        print('Release packaging stopped: '+str(exc),file=sys.stderr);return 2


if __name__=='__main__':
    raise SystemExit(main())
