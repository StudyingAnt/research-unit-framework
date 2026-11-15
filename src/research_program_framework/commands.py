"""Scientific command adapters; file inputs keep approved prose out of shell syntax."""

import json
from pathlib import Path

from . import records


COMMANDS = {'record-new', 'new-unit', 'record-resume', 'record-links', 'record-retire',
            'record-revise', 'register-existing', 'map-adopt', 'records'}


def configure(sub):
    for command in ('record-new', 'new-unit', 'register-existing'):
        entry = sub.add_parser(command)
        entry.add_argument('project')
        if command != 'new-unit': entry.add_argument('kind', choices=tuple(records.PATTERNS))
        entry.add_argument('--title', required=True); entry.add_argument('--parent')
        entry.add_argument('--link', action='append', default=[])
        entry.add_argument('--id', required=command == 'register-existing')
        entry.add_argument('--approval-file', required=True)
        if command == 'register-existing': entry.add_argument('--path', required=True)
        else: entry.add_argument('--body-file', required=True)
    for command in ('record-resume', 'record-links', 'record-retire', 'record-revise'):
        entry = sub.add_parser(command); entry.add_argument('project'); entry.add_argument('identity')
        if command != 'record-resume': entry.add_argument('--approval-file', required=True)
        if command in ('record-links', 'record-retire'): entry.add_argument('--revision', type=int, required=True)
        if command == 'record-links': entry.add_argument('--link', action='append', default=[])
        if command == 'record-revise':
            entry.add_argument('--body-file', required=True); entry.add_argument('--expected-sha256', required=True)
    entry = sub.add_parser('map-adopt'); entry.add_argument('project')
    entry.add_argument('--body-file', required=True); entry.add_argument('--approval-file', required=True)
    entry.add_argument('--expected-sha256', required=True, help='Current SHA-256 or absent')
    entry = sub.add_parser('records'); entry.add_argument('project')


def run(args):
    decision = json.loads(Path(args.approval_file).read_text()) if hasattr(args, 'approval_file') else None
    if args.command in ('record-new', 'new-unit'):
        result = records.adopt_record(args.project, 'T' if args.command == 'new-unit' else args.kind,
            args.title, Path(args.body_file).read_text(), decision, args.parent, args.link, args.id)
        if args.command == 'new-unit':
            from .reports import scaffold
            result = {'record': result, 'reports': scaffold(args.project, result['id'])}
        return result
    if args.command == 'register-existing':
        return records.register_existing(args.project, args.kind, args.id, args.path, args.title, decision, args.parent, args.link)
    if args.command == 'record-resume': return records.resume_record(args.project, args.identity)
    if args.command == 'record-links': return records.set_links(args.project, args.identity, args.link, decision, args.revision)
    if args.command == 'record-retire': return records.retire_record(args.project, args.identity, decision, args.revision)
    if args.command == 'record-revise':
        return records.revise_record(args.project, args.identity, Path(args.body_file).read_text(), decision, args.expected_sha256)
    if args.command == 'map-adopt':
        return records.adopt_map(args.project, Path(args.body_file).read_text(), decision,
                                 None if args.expected_sha256 == 'absent' else args.expected_sha256)
    with records.Store(args.project) as store: return records.read_registry(store)[0]
