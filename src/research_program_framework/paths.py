"""Validate portable payload names and read files without following links.

These functions never extract, create, replace, or delete files. Linux/WSL
descriptor-relative operations are required for filesystem inspection.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import stat
from typing import Iterable, Iterator


class ValidationError(ValueError):
    """An untrusted path, file, or manifest violates the validation contract."""


MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
COMPONENT_PATTERN = r"[A-Za-z0-9_.-]+"
_COMPONENT = re.compile(COMPONENT_PATTERN, re.ASCII)
_DEVICE = re.compile(r"(?:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\..*)?", re.I)
_FORBIDDEN = {".git", ".gitmodules", ".gitconfig", ".hg", ".svn", "development_context.local.md"}


def validate_relative_path(value: str) -> str:
    """Require an unambiguous, portable ASCII path relative to a payload root.

    This contract is for framework payload names, not researchers' data paths.
    It also applies to archive member names before any future extraction.
    """
    if type(value) is not str or not value or len(value) > 4096 or len(value.split('/')) > 128:
        raise ValidationError("Payload path must be a nonempty bounded string")
    parts = value.split("/")
    for part in parts:
        if (part in ("", ".", "..") or not _COMPONENT.fullmatch(part)
                or len(part) > 255 or part.endswith((".", " "))
                or part.casefold() in _FORBIDDEN or _DEVICE.fullmatch(part)):
            raise ValidationError(f"Unsafe payload path: {value!r}")
    return value


def validate_path_set(values: Iterable[str]) -> tuple[str, ...]:
    """Reject duplicate/case-colliding names and file/directory conflicts."""
    paths = tuple(validate_relative_path(value) for value in values)
    folded = set()
    spellings = {}
    for path in paths:
        key = path.casefold()
        if key in folded:
            raise ValidationError(f"Duplicate or case-colliding payload path: {path!r}")
        folded.add(key)
        parts = path.split('/')
        for n in range(1, len(parts) + 1):
            prefix = '/'.join(parts[:n])
            previous = spellings.setdefault(prefix.casefold(), prefix)
            if previous != prefix:
                raise ValidationError(f"Case-colliding payload component: {path!r}")
    for path in paths:
        parts = path.casefold().split("/")
        if any("/".join(parts[:n]) in folded for n in range(1, len(parts))):
            raise ValidationError(f"File/directory path conflict: {path!r}")
    return paths


@dataclass(frozen=True)
class FileFingerprint:
    path: str
    size: int
    sha256: str
    mode: str


def _signature(info: os.stat_result) -> tuple:
    # Access time is not content identity; no-atime descriptors suppress updates.
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _directory_flags(no_atime: bool = False) -> int:
    if (os.name != "posix" or not hasattr(os, "O_NOFOLLOW")
            or os.open not in os.supports_dir_fd
            or os.stat not in os.supports_dir_fd or os.listdir not in os.supports_fd
            or os.scandir not in os.supports_fd):
        raise ValidationError("Secure filesystem validation requires POSIX descriptor support")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    if no_atime:
        if not hasattr(os, 'O_NOATIME'):
            raise ValidationError('Side-effect-free reads require Linux O_NOATIME support')
        flags |= os.O_NOATIME
    return flags


@contextmanager
def _open_root(root: Path) -> Iterator[int]:
    """Open every component from /, rejecting symlinked root ancestors."""
    flags = _directory_flags()
    if '..' in Path(root).parts:
        raise ValidationError("Payload root must not contain parent traversal")
    absolute = Path(os.path.abspath(os.fspath(root)))
    fd = os.open(absolute.anchor, flags)
    try:
        for part in absolute.parts[1:]:
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        # Ancestors are only opened, never listed. Suppress access-time updates
        # on the actual root and every directory/file subsequently read.
        child = os.open('.', _directory_flags(no_atime=True), dir_fd=fd)
        os.close(fd)
        fd = child
        yield fd
    except OSError as exc:
        raise ValidationError("Cannot inspect payload root safely") from exc
    finally:
        os.close(fd)


@contextmanager
def _open_parent(root_fd: int, relative: str) -> Iterator[tuple[int, str]]:
    fd = os.dup(root_fd)
    try:
        parts = validate_relative_path(relative).split("/")
        for part in parts[:-1]:
            child = os.open(part, _directory_flags(no_atime=True), dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd, parts[-1]
    except OSError as exc:
        raise ValidationError(f"Cannot inspect payload path safely: {relative!r}") from exc
    finally:
        os.close(fd)


def _read_file(root_fd: int, relative: str, max_bytes: int,
               collect: bool = False) -> tuple[FileFingerprint, bytes]:
    if type(max_bytes) is not int or max_bytes < 0:
        raise ValidationError("File byte limit must be a nonnegative integer")
    with _open_parent(root_fd, relative) as (parent, name):
        before = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValidationError(f"Payload must contain single-link regular files: {relative!r}")
        mode = stat.S_IMODE(before.st_mode)
        if mode not in (0o644, 0o755):
            raise ValidationError(f"Unsupported payload file permissions: {relative!r}")
        if before.st_size > max_bytes:
            raise ValidationError(f"Payload file exceeds byte limit: {relative!r}")
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK | os.O_NOATIME
        fd = os.open(name, flags, dir_fd=parent)
        try:
            opened = os.fstat(fd)
            if _signature(before) != _signature(opened):
                raise ValidationError(f"Payload file changed before reading: {relative!r}")
            digest = hashlib.sha256()
            chunks = []
            total = 0
            while True:
                chunk = os.read(fd, min(1024 * 1024, max_bytes - total + 1))
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValidationError(f"Payload file exceeds byte limit: {relative!r}")
                digest.update(chunk)
                if collect:
                    chunks.append(chunk)
            after = os.fstat(fd)
            named = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if (total != before.st_size or _signature(before) != _signature(after)
                    or _signature(after) != _signature(named)):
                raise ValidationError(f"Payload file changed while reading: {relative!r}")
            return FileFingerprint(relative, total, digest.hexdigest(), f"{mode:04o}"), b"".join(chunks)
        finally:
            os.close(fd)


def fingerprint_file(root: Path, relative: str,
                     max_bytes: int = MAX_FILE_BYTES) -> FileFingerprint:
    """Hash a bounded regular file through a link-free descriptor chain."""
    with _open_root(root) as fd:
        return _read_file(fd, relative, max_bytes)[0]


def read_payload_file(root: Path, relative: str,
                      max_bytes: int = MAX_FILE_BYTES) -> bytes:
    """Read bounded bytes with the same file-kind and race checks as hashing."""
    with _open_root(root) as fd:
        return _read_file(fd, relative, max_bytes, collect=True)[1]


def _walk(fd: int, allowed: set[str], prefix: str = "") -> tuple[set[str], set[str], dict]:
    before = os.fstat(fd)
    # Stop at an unexpected entry rather than walking unrelated project trees.
    names = []
    with os.scandir(fd) as entries:
        for entry in entries:
            relative = f"{prefix}/{entry.name}" if prefix else entry.name
            validate_relative_path(relative)
            if relative not in allowed:
                raise ValidationError("Unlisted payload entry")
            names.append(entry.name)
    names.sort()
    files, directories = set(), set()
    signatures = {prefix: _signature(before)}
    for name in names:
        relative = f"{prefix}/{name}" if prefix else name
        validate_relative_path(relative)
        info = os.stat(name, dir_fd=fd, follow_symlinks=False)
        signatures[relative] = _signature(info)
        if stat.S_ISDIR(info.st_mode):
            child = os.open(name, _directory_flags(no_atime=True), dir_fd=fd)
            try:
                if _signature(info) != _signature(os.fstat(child)):
                    raise ValidationError(f"Payload directory changed: {relative!r}")
                child_files, child_dirs, child_signatures = _walk(child, allowed, relative)
                files.update(child_files)
                directories.update(child_dirs)
                signatures.update(child_signatures)
                directories.add(relative)
            finally:
                os.close(child)
        elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
            files.add(relative)
        else:
            raise ValidationError(f"Unsupported payload entry: {relative!r}")
    if _signature(before) != _signature(os.fstat(fd)) or names != sorted(os.listdir(fd)):
        raise ValidationError("Payload directory changed during inventory")
    validate_path_set(files)
    # Directories must also be portable across case-insensitive filesystems.
    if len({p.casefold() for p in directories}) != len(directories):
        raise ValidationError("Case-colliding payload directories")
    return files, directories, signatures


def validate_payload(root: Path, records: Iterable[FileFingerprint],
                     max_file_bytes: int = MAX_FILE_BYTES,
                     max_total_bytes: int = MAX_TOTAL_BYTES) -> tuple[FileFingerprint, ...]:
    """Verify the exact regular-file inventory, content, size, and permissions.

    This grants no installation/write permission. No code in the payload is run.
    A second inventory and descriptor-based file checks detect observed changes;
    callers needing mutation safety must later revalidate at the write boundary.
    """
    records = tuple(records)
    for record in records:
        if (not isinstance(record, FileFingerprint) or type(record.size) is not int
                or record.size < 0 or type(record.sha256) is not str
                or not re.fullmatch(r'[0-9a-f]{64}', record.sha256)
                or record.mode not in ('0644', '0755')):
            raise ValidationError("Invalid payload fingerprint record")
    validate_path_set(record.path for record in records)
    if (type(max_file_bytes) is not int or max_file_bytes < 0
            or type(max_total_bytes) is not int or max_total_bytes < 0):
        raise ValidationError("Payload byte limits must be nonnegative integers")
    if sum(record.size for record in records) > max_total_bytes:
        raise ValidationError("Payload exceeds total byte limit")
    expected = {record.path for record in records}
    parents = {"/".join(path.split("/")[:n]) for path in expected
               for n in range(1, len(path.split("/")))}
    try:
        with _open_root(root) as fd:
            inventory = _walk(fd, expected | parents)
            if inventory[:2] != (expected, parents):
                raise ValidationError("Payload inventory differs from manifest")
            verified = []
            for record in records:
                actual = _read_file(fd, record.path, min(max_file_bytes, record.size))[0]
                if (actual.size, actual.sha256, actual.mode) != (record.size, record.sha256, record.mode):
                    raise ValidationError(f"Payload fingerprint mismatch: {record.path!r}")
                verified.append(actual)
            if _walk(fd, expected | parents) != inventory:
                raise ValidationError("Payload inventory changed during verification")
            return tuple(verified)
    except OSError as exc:
        raise ValidationError("Cannot validate payload safely") from exc
