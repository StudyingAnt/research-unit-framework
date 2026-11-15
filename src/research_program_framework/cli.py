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
