#!/usr/bin/env python3
"""Allocate a stable AST identity and paired draft reports after scoped approval."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from project_common import encode, load_json, lock, read, safe_path, write

PROJECT = Path(__file__).resolve().parents[1]
REGISTRY = 'coordination/plans/ID_REGISTRY.json'
IDENTITY = r'A[0-9]{3}-S[0-9]{2}-T[0-9]{2}'


def create_unit(project, title, aim='A001', strategy='S01', approved_by='', unit_id=None):
    if load_json(project, '.framework/manifest.json').get('format') != 2:
        raise ValueError('This helper supports only projects created from the new baseline')
    if not title.strip() or not approved_by.strip():
        raise ValueError('A title and actual researcher approval reference are required')
    if not re.fullmatch(r'A(?!000)[0-9]{3}', aim) or not re.fullmatch(r'S(?!00)[0-9]{2}', strategy):
        raise ValueError('Expected Aim A001..A999 and Strategy S01..S99')
    with lock(project):
        registry_before = read(project, REGISTRY)
        registry = load_json(project, REGISTRY)
        if registry.get('format') != 1 or not isinstance(registry.get('units'), dict):
            raise ValueError('Invalid stable ID registry')
        occupied = set(registry['units'])
        for folder in ['reports', 'analyses']:
            directory = safe_path(project, folder)
            for path in directory.iterdir():
                match = re.match('(' + IDENTITY + ')(?:_|$)', path.name)
                if match:
                    occupied.add(match.group(1))
        prefix = aim + '-' + strategy + '-T'
        if unit_id is None:
            maximum = max([int(i[-2:]) for i in occupied if i.startswith(prefix)] or [0])
            if maximum >= 99:
                raise ValueError('Tactic capacity exhausted; discuss a distinct scientific scope')
            unit_id = prefix + str(maximum + 1).zfill(2)
        if not re.fullmatch(IDENTITY, unit_id) or not unit_id.startswith(prefix) or unit_id.endswith('T00') or unit_id in occupied:
            raise ValueError('ID is invalid or already reserved; resume existing work instead')
        reports = 'reports/' + unit_id
        analyses = 'analyses/' + unit_id
        for path in [reports, analyses]:
            if safe_path(project, path).exists():
                raise ValueError('Unit destination already exists')
        templates = {}
        for lang in ['en', 'ko']:
            snapshot = read(project, 'templates/report.' + lang + '.md')
            if snapshot is None:
                raise ValueError('Missing bilingual report template')
            templates[lang] = snapshot[0].replace(b'{{UNIT_ID}}', unit_id.encode()).replace(b'{{TITLE}}', title.encode())
        # Reserve first. A failed copy must never make an ID available for reuse.
        registry['units'][unit_id] = {'title': title, 'path': reports, 'state': 'reserved',
            'approval_reference': approved_by, 'created': datetime.now(timezone.utc).isoformat()}
        write(project, REGISTRY, encode(registry), expected=registry_before, replace=True)
        for folder in [reports + '/en', reports + '/ko', analyses + '/results', analyses + '/figures', analyses + '/logs']:
            safe_path(project, folder).mkdir(parents=True)
        for lang in ['en', 'ko']:
            write(project, reports + '/' + lang + '/report.md', templates[lang])
        metadata = {'unit_id': unit_id, 'status': 'PLANNING', 'outcome': 'NOT_EVALUATED',
                    'outcome_reason': 'Planning; scientific outcome not evaluated.', 'revision': 'REV001',
                    'figures': [], 'provenance': [],
                    'review': {'methods': False, 'bilingual': False, 'visual': False, 'references': []}}
        write(project, reports + '/report.json', encode(metadata))
        write(project, reports + '/plan.md', ('# ' + unit_id + ': ' + title + '\n\n'
            'Creation approval reference: ' + approved_by + '\n\n'
            'Scientific plan: DRAFT. Creation approval does not approve unfilled methods or specifications.\n\n'
            'Record Motivation, Aim, Strategy, the bounded Tactic question, material Specifications,\n'
            'expected evidence and explicit scientific approval here or link the approved Aim plan.\n'
            'Keep approved versions and explain consequential changes before execution.\n').encode())
        before = read(project, REGISTRY)
        registry['units'][unit_id]['state'] = 'active'
        write(project, REGISTRY, encode(registry), expected=before, replace=True)
        return {'unit_id': unit_id, 'reports': str(Path(project) / reports), 'status': 'PLANNING'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('title', nargs='?')
    parser.add_argument('--project', type=Path, default=PROJECT)
    parser.add_argument('--aim', default='A001')
    parser.add_argument('--strategy', default='S01')
    parser.add_argument('--approved-by', default='', help='Reference to actual researcher approval')
    parser.add_argument('--unit-id', help='Optional explicit unused identity')
    parser.add_argument('--resume', metavar='ID', help='Locate existing work without allocating an ID')
    args = parser.parse_args(argv)
    try:
        if args.resume:
            entry = load_json(args.project, REGISTRY)['units'].get(args.resume)
            if entry is None:
                raise ValueError('No such reserved/active ID')
            print(json.dumps({'unit_id': args.resume, **entry}, indent=2))
        else:
            if args.title is None:
                parser.error('Provide a title or --resume ID')
            print(json.dumps(create_unit(args.project, args.title, args.aim, args.strategy, args.approved_by, args.unit_id), indent=2))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        print('Unit creation stopped: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
