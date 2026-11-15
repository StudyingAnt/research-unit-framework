"""Deterministic, self-contained release builds from one editable source tree."""

import base64
import hashlib
import io
import gzip
import json
from pathlib import Path
import subprocess
import tarfile
import zipfile

from .manifests import validate_release_manifest, verify_release, load_legacy_baseline
from .paths import ValidationError, validate_path_set, validate_payload, read_payload_file, FileFingerprint
from .updates import encode, manifest_dict


def fingerprint(data, mode='0644'):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'mode': mode}


def source_bundle(root):
    root = Path(root)
    ownership = json.loads((root / 'starter/ownership.json').read_text())
    files = {p.relative_to(root / 'starter/payload').as_posix(): read_payload_file(root / 'starter/payload', p.relative_to(root / 'starter/payload').as_posix())
             for p in (root / 'starter/payload').rglob('*') if p.is_file()}
    if set(files) != set(ownership):
        raise ValidationError('Starter ownership must cover exactly the editable payload')
    validate_path_set(files)
    validate_payload(root / 'starter/payload', tuple(FileFingerprint(path=p, **fingerprint(data)) for p, data in sorted(files.items())))
    legacy = root / 'compatibility/v0.5/starter-v3'
    ancestor = load_legacy_baseline(legacy / 'manifest.json')
    validate_payload(legacy / 'payload', ancestor.files)
    return {'version': (root / 'VERSION').read_text().strip(),
            'source_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
            'files': {p: base64.b64encode(data).decode() for p, data in sorted(files.items())},
            'ownership': ownership,
            'legacy_manifest': json.loads((legacy / 'manifest.json').read_text()),
            'legacy_files': {f.path: base64.b64encode(read_payload_file(legacy / 'payload', f.path)).decode() for f in ancestor.files}}


def runtime(root, bundle):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        entries = {'__main__.py': b'from research_program_framework.cli import main\nmain()\n',
                   'research_program_framework/bundle.json': encode(bundle)}
        package = Path(root) / 'src/research_program_framework'
        entries.update({'research_program_framework/' + p.name: p.read_bytes() for p in package.glob('*.py')})
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return output.getvalue()


def materialize(bundle, runtime_bytes, destination):
    destination = Path(destination)
    if destination.exists():
        raise ValidationError('Release destination must not exist')
    files = {p: base64.b64decode(data, validate=True) for p, data in bundle['files'].items()}
    files['.research-framework/runtime.pyz'] = runtime_bytes
    roles = {**bundle['ownership'], '.research-framework/runtime.pyz': {'ownership': 'A'}}
    release = validate_release_manifest({'schema_version': 1, 'kind': 'framework_release',
        'framework_version': bundle['version'], 'specification_version': '1.1',
        'source_revision': bundle['source_revision'],
        'files': [{'path': path, **fingerprint(data), **roles[path]} for path, data in sorted(files.items())]})
    destination.mkdir(parents=True)
    for path, data in files.items():
        target = destination / 'payload' / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o644)
    (destination / 'manifest.json').write_bytes(encode(manifest_dict(release)))
    (destination / 'newproj.pyz').write_bytes(runtime_bytes)
    verify_release(destination / 'payload', release)
    return release


def build(root, destination, require_clean=False):
    """Build an independently usable directory and reproducible tar archive.

    Source revision identifies the checked-out commit; a dirty-source build is
    a development artifact and must never be presented as a tagged release.
    """
    if require_clean and subprocess.check_output(['git', 'status', '--porcelain'], cwd=root):
        raise ValidationError('Published release artifacts require a clean source checkout')
    bundle = source_bundle(root)
    release = materialize(bundle, runtime(root, bundle), destination)
    destination = Path(destination)
    (destination / 'README.txt').write_text(
        'Python 3.9+ on Linux/WSL. No development checkout required.\n'
        'Create: python3 newproj.pyz new /absolute/new/project --release .\n'
        'Plan: python3 newproj.pyz update-plan /absolute/project --release .\n'
        'Checksums establish integrity, not publisher authentication.\n'
        'No license grant is supplied; redistribution rights must be established separately.\n')
    checksums = ''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.relative_to(destination).as_posix() + '\n'
                        for p in sorted(destination.rglob('*')) if p.is_file())
    (destination / 'SHA256SUMS').write_text(checksums)
    def public_header(info):
        info.uid = info.gid = 0; info.uname = info.gname = ''; info.mtime = 0
        info.pax_headers = {}; info.mode = 0o755 if info.isdir() else 0o644
        return info
    with open(str(destination) + '.tar.gz', 'xb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w') as archive:
                for p in sorted(destination.rglob('*')):
                    archive.add(p, arcname=destination.name + '/' + p.relative_to(destination).as_posix(), recursive=False, filter=public_header)
    return release
