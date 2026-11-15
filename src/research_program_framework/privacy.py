"""Pre-push/public-artifact checks without printing matched sensitive content."""

import base64
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import zipfile

from .paths import ValidationError, validate_relative_path


SECRET_PATTERNS = (
    rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
    rb'gh[pousr]_[A-Za-z0-9]{32,}',
    rb'github_pat_[A-Za-z0-9_]{40,}',
    rb'AKIA[0-9A-Z]{16}',
)


def local_forbidden(root):
    context = Path(root) / 'DEVELOPMENT_CONTEXT.local.md'
    if not context.is_file(): return ()
    text = context.read_text()
    paths = re.findall(r'`(/[^`\n]+)`', text)
    forbidden = set(paths)
    # Protected-project identifiers come from local context, never shared code.
    for line in text.splitlines():
        if line.startswith('|') and ('Strictly read-only' in line or 'Read-only during development' in line):
            locations = re.findall(r'`(/[^`]+)`', line)
            for location in locations:
                path = Path(location)
                forbidden.add(path.name if path.name != 'project_A' else path.parent.name)
    return tuple(sorted(forbidden))


def audit_bytes(data, label, forbidden=(), depth=0):
    if depth > 4 or len(data) > 128 * 1024 * 1024:
        raise ValidationError('Public content inspection exceeds bounds: ' + label)
    issues = []
    for secret in SECRET_PATTERNS:
        if re.search(secret, data): issues.append({'file': label, 'category': 'credential-pattern'})
    if any(value and value.encode() in data for value in forbidden):
        issues.append({'file': label, 'category': 'checkout-local-information'})
    if label.endswith('DEVELOPMENT_CONTEXT.local.md'):
        issues.append({'file': label, 'category': 'excluded-local-context'})
    if zipfile.is_zipfile(io.BytesIO(data)):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if len(archive.infolist()) > 10000 or sum(i.file_size for i in archive.infolist()) > 128 * 1024 * 1024:
                raise ValidationError('Public zip inventory exceeds bounds')
            for entry in archive.infolist():
                validate_relative_path(entry.filename)
                issues += audit_bytes(archive.read(entry), label + ':' + entry.filename, forbidden, depth + 1)
    elif label.endswith('.json'):
        try: value = json.loads(data)
        except (ValueError, UnicodeError): value = None
        if isinstance(value, dict):
            for key in ('files', 'legacy_files', 'schemas'):
                if key in value and isinstance(value[key], dict):
                    for name, encoded in value[key].items():
                        if isinstance(encoded, str):
                            try: decoded = base64.b64decode(encoded, validate=True)
                            except ValueError: continue
                            issues += audit_bytes(decoded, label + ':' + name, forbidden, depth + 1)
    return issues


def audit_repository(root, history=True):
    root = Path(root); forbidden = local_forbidden(root)
    raw = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root)
    issues, count = [], 0
    for name in raw.decode().split('\0'):
        if not name: continue
        path = root / name
        if path.is_symlink():
            issues.append({'file': name, 'category': 'unreviewed-source-symlink'}); continue
        if not path.exists(): continue
        issues += audit_bytes(path.read_bytes(), name, forbidden); count += 1
    if history:
        pending = subprocess.check_output(['git', 'rev-list', '--objects', 'HEAD', '--not', '--remotes=origin'], cwd=root, text=True)
        for line in pending.splitlines():
            parts = line.split(' ', 1)
            if len(parts) != 2: continue
            digest, name = parts
            if subprocess.check_output(['git', 'cat-file', '-t', digest], cwd=root).strip() != b'blob': continue
            data = subprocess.check_output(['git', 'cat-file', 'blob', digest], cwd=root)
            issues += audit_bytes(data, 'pending-history:' + name, forbidden)
    return {'candidate_files': count, 'pending_history_checked': bool(history), 'issues': issues,
            'limits': 'Pattern/context checks supplement manual review; they do not prove absence of all confidential content or establish redistribution rights.'}


def audit_archive(path, forbidden=()):
    issues = []
    with tarfile.open(path, 'r:gz') as archive:
        entries = archive.getmembers()
        if len(entries) > 10000 or sum(i.size for i in entries) > 256 * 1024 * 1024:
            raise ValidationError('Public archive exceeds bounds')
        for entry in entries:
            validate_relative_path(entry.name)
            if not (entry.isfile() or entry.isdir()) or entry.uname or entry.gname or entry.uid or entry.gid:
                raise ValidationError('Public archive contains unsafe types or workstation ownership metadata')
            if entry.isfile(): issues += audit_bytes(archive.extractfile(entry).read(), entry.name, forbidden)
    return {'entries': len(entries), 'issues': issues}
