"""Descriptor-relative storage with registered and metadata-free operation locks."""

from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import hashlib
import os
from pathlib import Path
import stat
from typing import Optional
import uuid

from . import paths
from .paths import ValidationError, MAX_FILE_BYTES, validate_relative_path


@dataclass(frozen=True)
class Snapshot:
    data: Optional[bytes]
    mode: Optional[str]
    token: Optional[tuple]
    parents: tuple

    def fingerprint(self):
        if self.data is None:
            return None
        return {'size': len(self.data), 'sha256': hashlib.sha256(self.data).hexdigest(), 'mode': self.mode}


def identity(info):
    return (info.st_dev, info.st_ino, stat.S_IMODE(info.st_mode))


def _metadata_supported(fd):
    info = os.fstat(fd)
    if info.st_uid != os.geteuid() or info.st_gid != os.getegid():
        raise ValidationError('Non-default filesystem ownership requires separate metadata support')
    if not hasattr(os, 'listxattr') or os.listxattr(fd):
        raise ValidationError('ACLs/extended attributes require separate preservation support')


class Store:
    """Anchor reads/writes to a verified root; never traverse a nested checkout."""

    def __init__(self, root):
        self.root = Path(os.path.abspath(root))
        self._context = paths._open_root(root)

    def __enter__(self):
        self.fd = self._context.__enter__()
        self.identity = identity(os.fstat(self.fd))
        return self

    def __exit__(self, *args):
        return self._context.__exit__(*args)

    def _check_directory(self, fd, below_root):
        if os.fstat(fd).st_dev != self.identity[0]:
            raise ValidationError('Cross-filesystem update paths are unsupported')
        _metadata_supported(fd)
        if below_root:
            try:
                os.stat('.git', dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise ValidationError('Update path crosses an independent Git checkout')

    def _case_check(self, fd, name):
        with os.scandir(fd) as entries:
            if any(entry.name != name and entry.name.casefold() == name.casefold() for entry in entries):
                raise ValidationError('Case-alias collision in project path')

    @contextmanager
    def parent(self, path):
        parts = validate_relative_path(path).split('/')
        fd = os.dup(self.fd)
        try:
            for depth, part in enumerate(parts[:-1]):
                self._check_directory(fd, depth > 0)
                self._case_check(fd, part)
                try:
                    child = os.open(part, paths._directory_flags(no_atime=True), dir_fd=fd)
                except FileNotFoundError:
                    yield None, parts[-1]
                    return
                os.close(fd)
                fd = child
            self._check_directory(fd, len(parts) > 1)
            self._case_check(fd, parts[-1])
            yield fd, parts[-1]
        except OSError as exc:
            raise ValidationError('Unsafe or unavailable project path') from exc
        finally:
            os.close(fd)

    def directory(self, path):
        with self.parent(path) as (fd, name):
            if fd is None:
                return None
            try:
                child = os.open(name, paths._directory_flags(no_atime=True), dir_fd=fd)
            except FileNotFoundError:
                return None
            try:
                self._check_directory(child, True)
                return identity(os.fstat(child))
            finally:
                os.close(child)

    def parents(self, path):
        parts = validate_relative_path(path).split('/')
        result = [('', self.identity)]
        missing = False
        for index in range(1, len(parts)):
            prefix = '/'.join(parts[:index])
            found = None if missing else self.directory(prefix)
            missing = found is None
            result.append((prefix, found))
        return tuple(result)

    def read(self, path, limit=MAX_FILE_BYTES):
        parents = self.parents(path)
        with self.parent(path) as (fd, name):
            if fd is None:
                return Snapshot(None, None, None, parents)
            try:
                before = os.stat(name, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                return Snapshot(None, None, None, parents)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise ValidationError('Project targets must be single-link regular files')
            inspected = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME | os.O_NONBLOCK, dir_fd=fd)
            try:
                if paths._signature(before) != paths._signature(os.fstat(inspected)):
                    raise ValidationError('Project target changed before attribute inspection')
                _metadata_supported(inspected)
            finally:
                os.close(inspected)
            fingerprint, data = paths._read_file(self.fd, path, limit, collect=True)
            after = os.stat(name, dir_fd=fd, follow_symlinks=False)
            if paths._signature(before) != paths._signature(after) or parents != self.parents(path):
                raise ValidationError('Project path changed while reading')
            return Snapshot(data, fingerprint.mode, paths._signature(after), parents)

    def names(self, path):
        with self.parent(path) as (fd, name):
            if fd is None:
                return []
            try:
                child = os.open(name, paths._directory_flags(no_atime=True), dir_fd=fd)
            except FileNotFoundError:
                return []
            try:
                self._check_directory(child, True)
                return sorted(os.listdir(child))
            finally:
                os.close(child)

    def ensure_dir(self, path, created=None):
        parts = validate_relative_path(path).split('/')
        for index in range(1, len(parts) + 1):
            prefix = '/'.join(parts[:index])
            if self.directory(prefix) is not None:
                continue
            if created:
                created(prefix, None)  # Durable intent before mkdir.
            self._check_root()
            with self.parent(prefix) as (fd, name):
                if fd is None:
                    raise ValidationError('Missing directory parent')
                private = parts[0] == '.research-framework' and len(parts) > 1 and parts[1] in {
                    'transactions', 'backups', 'baselines'}
                os.mkdir(name, 0o700 if private else 0o755, dir_fd=fd)
                os.fsync(fd)
            if created:
                created(prefix, self.directory(prefix))

    def create(self, path, data, mode='0644'):
        self._check_root()
        with self.parent(path) as (parent, name):
            if parent is None:
                raise ValidationError('Missing staging directory')
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o600, dir_fd=parent)
            try:
                remaining = memoryview(data)
                while remaining:
                    count = os.write(fd, remaining)
                    if not count:
                        raise OSError('Short staging write')
                    remaining = remaining[count:]
                os.fchmod(fd, int(mode, 8))
                os.fsync(fd)
            finally:
                os.close(fd)
            os.fsync(parent)
        result = self.read(path)
        if result.data != data or result.mode != mode:
            raise ValidationError('Staged file verification failed')
        return result

    def check(self, path, expected):
        actual = self.read(path)
        if actual != expected:
            raise ValidationError(f'Stale or locally modified target: {path}')

    def _check_root(self):
        if not hasattr(self, 'lock_identity') and not hasattr(self, 'bootstrap_identity'):
            raise ValidationError('Mutation requires the registered-installation lock')
        with paths._open_root(self.root) as fd:
            if identity(os.fstat(fd)) != self.identity:
                raise ValidationError('Project root identity changed')
        if hasattr(self, 'bootstrap_identity'):
            if self.identity != self.bootstrap_identity:
                raise ValidationError('Bootstrap root changed')
        elif self.directory('.research-framework') != self.lock_identity:
            raise ValidationError('Locked installation directory identity changed')

    def publish(self, source, target, expected, source_expected):
        self._check_root()
        self.check(target, expected)
        self.check(source, source_expected)
        with self.parent(source) as (src_fd, src), self.parent(target) as (dst_fd, dst):
            if src_fd is None or dst_fd is None:
                raise ValidationError('Missing publication parent')
            self.check(target, expected)
            self.check(source, source_expected)
            os.replace(src, dst, src_dir_fd=src_fd, dst_dir_fd=dst_fd)
            os.fsync(dst_fd)
            os.fsync(src_fd)
        return self.read(target)

    def remove(self, path, expected):
        self._check_root()
        self.check(path, expected)
        with self.parent(path) as (fd, name):
            if fd is None:
                raise ValidationError('Missing removal parent')
            self.check(path, expected)
            os.unlink(name, dir_fd=fd)
            os.fsync(fd)
        return self.read(path)

    def atomic(self, path, data, expected):
        # Used only for manager-owned journals, never arbitrary payload paths.
        temp = path.rsplit('/', 1)[0] + '/pending-' + uuid.uuid4().hex
        staged = self.create(temp, data)
        return self.publish(temp, path, expected, staged)

    def remove_empty(self, path, expected_identity):
        self._check_root()
        if expected_identity is None or self.directory(path) != tuple(expected_identity):
            return
        if self.names(path):
            return
        with self.parent(path) as (fd, name):
            os.rmdir(name, dir_fd=fd)
            os.fsync(fd)

    @contextmanager
    def bootstrap_lock(self):
        """Root lock for metadata-free adoption and its external recovery store."""
        if hasattr(self, 'lock_identity') or hasattr(self, 'bootstrap_identity'):
            raise ValidationError('Store is already locked')
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValidationError('Another adoption operation holds the root lock') from exc
        self.bootstrap_identity = self.identity
        try:
            yield
        finally:
            del self.bootstrap_identity
            fcntl.flock(self.fd, fcntl.LOCK_UN)

    @contextmanager
    def lock(self):
        if hasattr(self, 'lock_identity'):
            raise ValidationError('This store is already locked')
        with self.parent('.research-framework/lock') as (fd, name):
            if fd is None:
                raise ValidationError('An existing registered installation is required')
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValidationError('Another framework operation holds the project lock') from exc
            try:
                self.lock_identity = identity(os.fstat(fd))
                yield
            finally:
                del self.lock_identity
                fcntl.flock(fd, fcntl.LOCK_UN)
