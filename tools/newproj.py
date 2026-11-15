#!/usr/bin/env python3
"""Create a research project by copying the visible template."""

import argparse
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from _framework import ROOT, create_project


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name', nargs='?', help='New project name (one directory name)')
    parser.add_argument('--destination', type=Path, help='Exact new project directory')
    parser.add_argument('--projects-dir', type=Path, help='Override the configured parent directory')
    parser.add_argument('--configure', type=Path, metavar='PROJECTS_DIR', help='Remember a default projects directory')
    args = parser.parse_args(argv)
    config = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'research-framework/config.json'
    try:
        if args.configure is not None:
            if args.name or args.destination:
                parser.error('--configure is a separate setup command')
            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text(json.dumps({'projects_dir': str(args.configure.expanduser().absolute())}, indent=2) + '\n')
            print('Projects directory configured: ' + str(args.configure.expanduser().absolute()))
            return 0
        if not args.name or args.name in {'.', '..'} or any(c in args.name for c in '/\\\0'):
            parser.error('Provide a project name without path separators; use --destination for an exact path')
        settings = json.loads(config.read_text()) if config.exists() else {}
        parent = args.projects_dir or os.environ.get('RPF_PROJECTS_DIR') or settings.get('projects_dir') or Path.home() / 'projects'
        destination = args.destination or Path(parent).expanduser() / args.name
        result = create_project(destination, ROOT)
        print('Created ' + result['project'] + ' (Framework ' + result['version'] + ')')
        print('Open that directory and start Coordination in your research assistant.')
        return 0
    except (OSError, ValueError) as exc:
        print('Project creation stopped: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
