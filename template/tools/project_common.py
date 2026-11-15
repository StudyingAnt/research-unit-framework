"""Small filesystem helpers shared by the ordinary project scripts."""

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tempfile


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def relative(value):
    if not isinstance(value, str) or not value or '\\' in value or '\0' in value:
        raise ValueError('Expected a relative project path')
    parts = value.split('/')
    if any(p in ('', '.', '..') for p in parts) or PurePosixPath(value).is_absolute():
        raise ValueError('Unsafe relative path: ' + value)
    return value


def safe_path(root, value):
    """Reject link traversal and unusual file types before any read or write."""
    relative(value)
    root = Path(root).absolute()
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Project root must be an existing real directory')
    current = root
    for part in value.split('/'):
        current = current / part
        if current.is_symlink():
            raise ValueError('Symbolic links are not script targets: ' + value)
        try:
            info = current.stat()
        except FileNotFoundError:
            continue
        if current != root / value and not stat.S_ISDIR(info.st_mode):
            raise ValueError('A parent is not a directory: ' + value)
        if current == root / value and not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
            raise ValueError('Not a regular file/directory: ' + value)
    return root / value


def read(root, value):
    path = safe_path(root, value)
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NOATIME', 0))
    except FileNotFoundError:
        return None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError('Expected a single-link regular file: ' + value)
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            data = stream.read()
        after = os.fstat(fd)
        if (info.st_size, info.st_mtime_ns, info.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError('File changed while reading: ' + value)
        return data, stat.S_IMODE(info.st_mode)
    finally:
        os.close(fd)


def fingerprint(snapshot):
    return None if snapshot is None else {'sha256': digest(snapshot[0]), 'mode': snapshot[1]}


def write(root, value, data, mode=0o644, expected=None, replace=False):
    """Stage one file and recheck its prior bytes immediately before replacement."""
    path = safe_path(root, value)
    if read(root, value) != expected:
        raise ValueError('Destination changed or already exists: ' + value)
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_path(root, value)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        if read(root, value) != expected:
            raise ValueError('Destination changed before replacement: ' + value)
        if replace:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def load_json(root, value):
    snapshot = read(root, value)
    if snapshot is None:
        raise ValueError('Missing file: ' + value)
    return json.loads(snapshot[0])


@contextmanager
def lock(root, directory='.framework'):
    """Serialize cooperating script writers; read-only commands never lock."""
    import fcntl
    safe_path(root, directory + '/lock')
    (Path(root) / directory).mkdir(exist_ok=True)
    fd = os.open(Path(root) / directory / 'lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)
