"""Fresh project creation: exclusive staging and no-clobber directory publish."""

import ctypes
import errno
import hashlib
import os
from pathlib import Path
import tempfile
import uuid

from .manifests import verify_release
from .paths import ValidationError, read_payload_file, validate_relative_path
from .storage import Store
from .updates import RECEIPT, encode, manifest_dict, validate_receipt
from .release import fingerprint


def installation(release, installed, operation=None):
    return validate_receipt({'schema_version': 1, 'kind': 'framework_installation',
        'project_id': uuid.uuid4().hex, 'generation': 0, 'release': manifest_dict(release),
        'installed': installed, 'project_owned': {f.path: f.project_owner for f in release.files if f.ownership == 'D'},
        'last_operation': operation})


def _publish_directory(source, target):
    # Linux renameat2(RENAME_NOREPLACE) prevents a racing destination overwrite.
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, 'renameat2', None)
    if rename is None:
        raise ValidationError('Atomic no-clobber directory publication requires Linux renameat2')
    result = rename(-100, os.fsencode(source), -100, os.fsencode(target), 1)
    if result:
        code = ctypes.get_errno()
        raise ValidationError('Destination exists or atomic publication is unavailable: ' + os.strerror(code))


def create_project(target, payload, release):
    verify_release(payload, release)
    target = Path(os.path.abspath(target))
    validate_relative_path(target.name)
    with Store(target.parent) as parent:
        if parent.directory(target.name) is not None:
            raise ValidationError('New project destination already exists; use inspected migration')
        parent_identity = parent.identity
    # Staging is a new disposable directory, never an overlay on existing data.
    with tempfile.TemporaryDirectory(prefix='.framework-create-', dir=target.parent) as staging:
        staged = Path(staging) / 'project'
        staged.mkdir()
        installed = {}
        for item in release.files:
            data = read_payload_file(payload, item.path)
            output = staged / item.path
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open('xb') as handle:
                handle.write(data); handle.flush(); os.fsync(handle.fileno())
            output.chmod(int(item.mode, 8))
            if item.ownership == 'A':
                installed[item.path] = fingerprint(data, item.mode)
                base = staged / '.research-framework/baselines' / item.sha256
                base.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                if not base.exists():
                    base.write_bytes(data); base.chmod(0o644)
        (staged / '.research-framework').chmod(0o700)
        receipt = installation(release, installed)
        (staged / RECEIPT).write_bytes(encode(receipt))
        # Fsync all staged files/directories before publishing their root.
        for directory, dirs, files in os.walk(staged, topdown=False):
            for name in files:
                fd = os.open(Path(directory) / name, os.O_RDONLY)
                try: os.fsync(fd)
                finally: os.close(fd)
            fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
            try: os.fsync(fd)
            finally: os.close(fd)
        with Store(target.parent) as parent:
            if parent.identity != parent_identity:
                raise ValidationError('Destination parent changed')
            _publish_directory(staged, target)
            os.fsync(parent.fd)
    return receipt
