"""Scientific command adapters; file inputs keep approved prose out of shell syntax."""

import json
from pathlib import Path

from . import records


COMMANDS = {'record-new', 'new-unit', 'record-resume', 'record-links', 'record-retire',
            'record-revise', 'register-existing', 'map-adopt', 'records', 'draft-reports',
            'report-check', 'report', 'report-recover-plan', 'report-recover', 'run-record',
            'handoff', 'hpc-commands', 'launcher-check', 'inspect', 'doctor', 'audit-public'}


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
    for command in ('draft-reports', 'report-check', 'report'):
        entry = sub.add_parser(command); entry.add_argument('project'); entry.add_argument('unit')
        if command == 'report': entry.add_argument('--revision', required=True)
    for command in ('report-recover-plan', 'report-recover'):
        entry = sub.add_parser(command); entry.add_argument('project'); entry.add_argument('operation')
        if command == 'report-recover': entry.add_argument('--plan-digest', required=True)
    for command in ('run-record', 'handoff', 'hpc-commands'):
        entry = sub.add_parser(command); entry.add_argument('project'); entry.add_argument('--record-file', required=True)
        if command in ('run-record', 'handoff'): entry.add_argument('--expected-sha256')
        if command == 'run-record': entry.add_argument('--approval-file')
    entry = sub.add_parser('launcher-check'); entry.add_argument('script')
    for command in ('inspect', 'doctor'):
        entry = sub.add_parser(command); entry.add_argument('project')
    entry = sub.add_parser('audit-public'); entry.add_argument('--source', default='.')
    entry.add_argument('--archive')


def run(args):
    decision = json.loads(Path(args.approval_file).read_text()) if getattr(args, 'approval_file', None) else None
    if args.command in {'inspect', 'doctor'}:
        from . import diagnostics
        return getattr(diagnostics, 'inspect_project' if args.command == 'inspect' else 'doctor')(args.project)
    if args.command == 'audit-public':
        from . import privacy
        result = privacy.audit_archive(args.archive, privacy.local_forbidden(args.source)) if args.archive else privacy.audit_repository(args.source)
        if result['issues']: raise records.ValidationError('Public audit refused: ' + json.dumps(result['issues']))
        return result
    if args.command in {'draft-reports', 'report-check', 'report', 'report-recover-plan', 'report-recover'}:
        from . import reports
        if args.command == 'draft-reports': return reports.scaffold(args.project, args.unit)
        if args.command == 'report-check':
            result = reports.validate_report(args.project, args.unit)
            return {k: result[k] for k in ('unit', 'metadata', 'figures', 'review_required')}
        if args.command == 'report': return reports.render_report(args.project, args.unit, args.revision)
        if args.command == 'report-recover-plan': return reports.report_recovery_plan(args.project, args.operation)
        return reports.recover_report(args.project, args.operation, args.plan_digest)
    if args.command in {'run-record', 'handoff', 'hpc-commands', 'launcher-check'}:
        from . import execution
        if args.command == 'launcher-check': return execution.validate_launcher(Path(args.script).read_text())
        value = json.loads(Path(args.record_file).read_text())
        if args.command == 'run-record': return execution.record_run(args.project, value, decision, args.expected_sha256)
        if args.command == 'handoff': return execution.handoff(args.project, value, args.expected_sha256)
        return execution.hpc_commands(args.project, value)
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
