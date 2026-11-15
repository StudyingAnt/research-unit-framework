"""Portable command-line interface; commands never infer scientific approval."""

import argparse
from dataclasses import asdict, is_dataclass
from contextlib import contextmanager
import importlib.resources
import json
from pathlib import Path
import sys
import tempfile

from .initialization import create_project
from .manifests import load_release_manifest
from .paths import ValidationError
from .release import build, materialize, source_bundle, runtime
from .updates import plan_update
from .transactions import apply_update, apply_rollback, plan_rollback, plan_recovery
from .migration import plan_migration, apply_migration, plan_migration_rollback, rollback_migration


@contextmanager
def selected_release(path):
    if path:
        root = Path(path).absolute()
        yield root / 'payload', load_release_manifest(root / 'manifest.json')
        return
    # Only new project creation uses embedded materialization. Read-only planning
    # requires an explicit existing release and never enters this branch.
    with tempfile.TemporaryDirectory(prefix='framework-release-') as temporary:
        if str(sys.argv[0]).endswith('.pyz'):
            bundle = json.loads(importlib.resources.files(__package__).joinpath('bundle.json').read_text())
            data = Path(sys.argv[0]).read_bytes()
        else:
            root = Path(__file__).resolve().parents[2]
            bundle = source_bundle(root)
            data = runtime(root, bundle)
        release = materialize(bundle, data, Path(temporary) / 'release')
        yield Path(temporary) / 'release/payload', release


def parser():
    result = argparse.ArgumentParser(prog='newproj', description=__doc__)
    sub = result.add_subparsers(dest='command', required=True)
    new = sub.add_parser('new', help='Create a new project at an absent destination')
    new.add_argument('project'); new.add_argument('--release')
    release = sub.add_parser('build-release', help='Build from the development source tree')
    release.add_argument('destination'); release.add_argument('--source', default='.')
    for command in ('update-plan', 'update'):
        update = sub.add_parser(command)
        update.add_argument('project'); update.add_argument('--release', required=True)
        if command == 'update': update.add_argument('--plan-digest', required=True)
    for command in ('rollback-plan', 'rollback', 'recover-plan', 'recover'):
        rollback = sub.add_parser(command)
        rollback.add_argument('project'); rollback.add_argument('operation')
        if command in ('rollback', 'recover'): rollback.add_argument('--plan-digest', required=True)
    for command in ('migrate-plan', 'migrate'):
        migration = sub.add_parser(command)
        migration.add_argument('project'); migration.add_argument('--release', required=True)
        migration.add_argument('--bridge-policy-reviewed', action='store_true')
        migration.add_argument('--keep-local', action='append', default=[], help='Explicitly retain a recognized legacy managed file')
        if command == 'migrate':
            migration.add_argument('--plan-digest', required=True)
            migration.add_argument('--backup-root', required=True, help='Existing external private directory')
    for command in ('migration-rollback-plan', 'migration-rollback'):
        recovery = sub.add_parser(command); recovery.add_argument('backup_directory')
        if command == 'migration-rollback': recovery.add_argument('--plan-digest', required=True)
    from .commands import configure
    configure(sub)
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == 'build-release':
            result = {'version': build(args.source, args.destination).framework_version}
        elif args.command == 'new':
            with selected_release(args.release) as (payload, release):
                result = create_project(args.project, payload, release)
        elif args.command in ('update', 'update-plan'):
            with selected_release(args.release) as (payload, release):
                plan = plan_update(args.project, payload, release)
                if args.command == 'update-plan': result = plan.describe()
                else:
                    if plan.digest != args.plan_digest: raise ValidationError('Plan digest changed; review a fresh plan')
                    result = apply_update(plan)
        elif args.command in ('migrate-plan', 'migrate'):
            import base64
            # The selected release runtime owns the exact, inert legacy ancestor.
            if str(sys.argv[0]).endswith('.pyz'):
                bundle = json.loads(importlib.resources.files(__package__).joinpath('bundle.json').read_text())
            else:
                bundle = source_bundle(Path(__file__).resolve().parents[2])
            legacy_files = {p: base64.b64decode(data, validate=True) for p, data in bundle['legacy_files'].items()}
            with selected_release(args.release) as (payload, release):
                plan = plan_migration(args.project, payload, release, bundle['legacy_manifest'], legacy_files,
                                      {p: None for p in args.keep_local}, args.bridge_policy_reviewed)
                if args.command == 'migrate-plan': result = plan.describe()
                else:
                    if plan.digest != args.plan_digest: raise ValidationError('Migration plan changed')
                    result = apply_migration(plan, args.backup_root)
        elif args.command == 'migration-rollback-plan':
            result = plan_migration_rollback(args.backup_directory)
        elif args.command == 'migration-rollback':
            result = rollback_migration(args.backup_directory, args.plan_digest)
        elif args.command in __import__('research_program_framework.commands', fromlist=['COMMANDS']).COMMANDS:
            from .commands import run
            result = run(args)
        else:
            plan = (plan_recovery if args.command.startswith('recover') else plan_rollback)(args.project, args.operation)
            if args.command.endswith('-plan'):
                result = plan.describe()
            else:
                if plan.digest != args.plan_digest: raise ValidationError('Rollback/recovery plan changed')
                result = apply_rollback(plan)
        print(json.dumps(asdict(result) if is_dataclass(result) else result, ensure_ascii=False, indent=2))
    except (ValidationError, OSError, ValueError) as exc:
        print('Framework operation refused: ' + str(exc), file=sys.stderr)
        raise SystemExit(2)


if __name__ == '__main__':
    main()
