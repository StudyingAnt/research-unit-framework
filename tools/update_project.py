#!/usr/bin/env python3
"""Preview a baseline-2 project update; apply only with --apply."""

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from _framework import ROOT, apply_update, plan_update
from _merge import has_markers


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('--source', type=Path, default=ROOT, help='Framework checkout/release directory')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--expect', help='Optional digest from a previously reviewed preview')
    parser.add_argument('--resolve', action='append', default=[], metavar='PATH=FILE', help='Explicit merged bytes for one tracked file')
    args = parser.parse_args(argv)
    try:
        resolutions = {}
        for value in args.resolve:
            path, filename = value.split('=', 1)
            if path in resolutions:
                raise ValueError('Duplicate resolution: ' + path)
            data = Path(filename).read_bytes()
            if has_markers(data):
                raise ValueError('Resolution contains unresolved conflict markers')
            resolutions[path] = data
        plan = plan_update(args.project, args.source, resolutions)
        description = plan.describe()
        print(json.dumps(description, ensure_ascii=False, indent=2))
        if description['conflicts']:
            return 2
        if args.apply:
            print(json.dumps(apply_update(plan, args.expect), indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('Update stopped: ' + str(exc) + '\nInspect .framework/backups if a write was interrupted.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
