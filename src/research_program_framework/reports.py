"""Detailed paired reporting with explicit assets, math and revision provenance."""

import base64
from collections import Counter
import copy
import hashlib
import html
import io
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid

from .paths import ValidationError, validate_relative_path
from .records import configuration, read_registry, _replace, STATUS, OUTCOME
from .release import fingerprint
from .storage import Store
from .updates import decode, encode, read_receipt, MAX_METADATA


SECTIONS = ('motivation', 'question', 'strategy', 'methods', 'specifications', 'execution',
            'evidence', 'results', 'interpretation', 'limitations', 'provenance')
UNIT = r'A[0-9]{3}-S[0-9]{2}-T[0-9]{2}(?:_[a-z0-9_]+)?'


def _unit(store, unit):
    if not re.fullmatch(UNIT, unit): raise ValidationError('Expected a stable Tactic ID and optional descriptive suffix')
    return configuration(store)['paths']['reports'] + '/' + unit


def scaffold(project, identity):
    with Store(project) as store, store.lock():
        registry, _ = read_registry(store)
        record = next((r for r in registry['records'] if r['id'] == identity and r['kind'] == 'T' and r['state'] == 'active'), None)
        if record is None: raise ValidationError('An approved registered Tactic is required before draft reports')
        root = _unit(store, identity); files = {}
        for lang in ('en', 'ko'):
            content = store.read('templates/report.' + lang + '.md').data
            if content is None: raise ValidationError('Paired report template is missing')
            files[root + '/' + lang + '/report.md'] = content.replace(b'{{UNIT_ID}}', identity.encode()).replace(b'{{TITLE}}', record['title'].encode())
        files[root + '/report.json'] = encode({'schema_version': 1, 'unit_id': identity, 'status': 'PLANNING',
            'outcome': 'NOT_EVALUATED', 'outcome_reason': 'Draft; scientific outcome has not been evaluated.',
            'revision': 'REV001', 'figures': [], 'provenance': [],
            'review': {'methods': False, 'bilingual': False, 'visual': False, 'references': []}})
        for path, data in files.items():
            current = store.read(path)
            if current.data is not None and current.data != data:
                raise ValidationError('Draft destination contains existing work; resume it instead')
        for path, data in files.items():
            current = store.read(path)
            if current.data is None: _replace(store, path, data, current)
        return list(files)


def _metadata(data, unit):
    required = {'schema_version', 'unit_id', 'status', 'outcome', 'outcome_reason', 'revision', 'figures', 'provenance', 'review'}
    if type(data) is not dict or set(data) != required or data['schema_version'] != 1:
        raise ValidationError('Invalid report metadata fields')
    if data['unit_id'] != unit.split('_', 1)[0] or data['status'] not in STATUS or data['outcome'] not in OUTCOME:
        raise ValidationError('Invalid report identity/status/outcome')
    if not re.fullmatch(r'REV[0-9]{3}', data['revision']): raise ValidationError('Report revisions use REV###, separately from Runs')
    if data['status'] == 'COMPLETED' and data['outcome'] == 'NOT_EVALUATED' and not str(data['outcome_reason']).strip():
        raise ValidationError('Completed NOT_EVALUATED work requires its actual reason')
    if type(data['figures']) is not list or type(data['provenance']) is not list:
        raise ValidationError('Report figures/provenance must be lists')
    review = data['review']
    if type(review) is not dict or set(review) != {'methods', 'bilingual', 'visual', 'references'} or any(type(review[k]) is not bool for k in ('methods', 'bilingual', 'visual')) or type(review['references']) is not list:
        raise ValidationError('Explicit review fields required; rendering never sets scientific approval')
    from .execution import validate_provenance
    for item in data['provenance']: validate_provenance(item)
    return data


def _source(text, metadata):
    # Guidance comments are not scientific content and may remain in drafts.
    visible = re.sub(r'<!--(?! section:).*?-->', '', text, flags=re.S)
    if re.search(r'\{\{|\}\}|\bTODO\b|\bTBD\b|<<<<<<<|>>>>>>>', visible):
        raise ValidationError('Report contains unresolved placeholders or conflict markers')
    markers = re.findall(r'<!-- section: ([a-z]+) -->', visible)
    if tuple(markers) != SECTIONS: raise ValidationError('Report must retain eleven corresponding sections in order')
    chunks = re.split(r'<!-- section: [a-z]+ -->', visible)[1:]
    for name, chunk in zip(SECTIONS, chunks):
        body = re.sub(r'^##[^\n]*\n', '', chunk.strip(), count=1).strip()
        if not body: raise ValidationError('Empty scientific section: ' + name)
    for field, expected in [('Unit ID', metadata['unit_id']), ('Status', metadata['status']),
                            ('Outcome', metadata['outcome']), ('Report revision', metadata['revision'])]:
        match = re.search(r'^\*\*' + re.escape(field) + r':\*\*\s*(\S+)\s*$', text, re.M)
        if match is None or match.group(1) != expected: raise ValidationError('Bilingual report metadata mismatch: ' + field)
    return visible


def _numbers(text):
    text = re.sub(r'^#+.*$', '', text, flags=re.M)
    text = re.sub(r'\*\*[^\n]+|!?\[[^\]]*\]\([^)]*\)|<!--.*?-->', '', text)
    return Counter(re.findall(r'(?<![A-Za-z0-9_])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?![A-Za-z0-9_])', text))


def validate_report(project, unit):
    """Structural/scalar checks only; never asserts scientific equivalence."""
    with Store(project) as store:
        root = _unit(store, unit)
        metadata_snapshot = store.read(root + '/report.json', 1024 * 1024)
        if metadata_snapshot.data is None: raise ValidationError('Report metadata is missing')
        metadata = _metadata(decode(metadata_snapshot.data), unit)
        sources = {}; visible = {}
        for lang in ('en', 'ko'):
            snapshot = store.read(root + '/' + lang + '/report.md')
            if snapshot.data is None: raise ValidationError('Paired Markdown source is missing')
            sources[lang] = snapshot; visible[lang] = _source(snapshot.data.decode(), metadata)
        if _numbers(visible['en']) != _numbers(visible['ko']):
            raise ValidationError('Bilingual numeric tokens differ; review parameters/results and translation')
        figures = _figures(store, metadata['figures'])
        return {'unit': unit, 'metadata': metadata, 'sources': sources, 'metadata_snapshot': metadata_snapshot,
                'root': root, 'figures': figures, 'config_snapshot': store.read('framework-project.json'),
                'review_required': [k for k in ('methods', 'bilingual', 'visual') if not metadata['review'][k]]}


def _figures(store, figures):
    result = []
    for item in figures:
        required = {'path', 'width_mm', 'kind', 'font_family', 'text_size_pt', 'exception', 'raster_embedded'}
        if type(item) is not dict or set(item) != required or item['kind'] not in {'plot', 'measurement'}:
            raise ValidationError('Figure metadata must describe construction/display and raster integrity')
        validate_relative_path(item['path'])
        source = store.read(item['path'])
        if source.data is None: raise ValidationError('Required figure is missing')
        if type(item['width_mm']) not in (float, int) or item['width_mm'] <= 0: raise ValidationError('Figure intended width must be positive')
        if not item['exception'] and item['kind'] == 'plot' and (item['font_family'] != 'Arial' or not 5 <= item['text_size_pt'] <= 7):
            raise ValidationError('Figure default deviation requires an explicit justification')
        if item['path'].lower().endswith('.png'):
            try:
                from PIL import Image
                with Image.open(io.BytesIO(source.data)) as image:
                    actual = image.width / (item['width_mm'] / 25.4)
                    declared = image.info.get('dpi', (None, None))[0]
            except ImportError as exc: raise ValidationError('PNG inspection requires the optional Pillow reporting dependency') from exc
            if not item['exception'] and (declared is None or not 590 <= declared <= 610 or actual < 590):
                raise ValidationError('PNG does not meet 600 dpi at intended physical width')
        elif item['path'].lower().endswith('.svg'):
            _safe_svg(source.data)
        elif item['path'].lower().endswith('.pdf'):
            if not source.data.startswith(b'%PDF'): raise ValidationError('Invalid PDF figure')
        else: raise ValidationError('Unsupported publication figure format')
        result.append({'path': item['path'], **source.fingerprint(), 'declared': item})
    return result


def _safe_svg(data):
    text = data.decode('utf-8')
    text = re.sub(r'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1\.1//EN"\s+"http://www\.w3\.org/Graphics/SVG/1\.1/DTD/svg11\.dtd">', '', text)
    if (re.search(r'<!DOCTYPE|<!ENTITY|<script|<foreignObject|\son[a-z]+\s*=', text, re.I)
            or re.search(r'(?:href|src)\s*=\s*["\'](?!#|data:)', text, re.I)
            or re.search(r'url\(\s*["\']?(?!#|data:)', text, re.I)):
        raise ValidationError('SVG contains active content or external references')


def _pandoc(command, args, content):
    try:
        result = subprocess.run([command, *args], input=content, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError as exc: raise ValidationError('Pandoc is unavailable; configure an existing reporting environment') from exc
    if result.returncode: raise ValidationError('Pandoc failed: ' + result.stderr.decode(errors='replace'))
    return result.stdout


def _math(latex, display):
    try:
        from matplotlib.mathtext import math_to_image
        output = io.BytesIO()
        math_to_image('$' + latex + '$', output, format='svg', dpi=600, color='black')
        data = output.getvalue()
    except Exception as exc: raise ValidationError('Unsupported mathematical expression: ' + latex) from exc
    # Matplotlib emits a static SVG with a standard DOCTYPE; strip it before
    # embedding. Internal path references are retained, never external fetches.
    data = re.sub(br'<!DOCTYPE[^>]*>', b'', data)
    _safe_svg(data)
    text = data.decode(); width = float(re.search(r'width="([0-9.]+)pt"', text).group(1))
    css = 'math-display' if display else 'math-inline'
    return '<img class="' + css + '" alt="' + html.escape(latex, quote=True) + '" style="width:' + str(width) + 'pt" src="data:image/svg+xml;base64,' + base64.b64encode(data).decode() + '">'


def _asset(store, root, lang, location, image):
    from urllib.parse import urlsplit, unquote
    parsed = urlsplit(location)
    if parsed.scheme or parsed.netloc:
        if not image and parsed.scheme in {'https', 'http', 'doi', 'mailto'}: return location
        raise ValidationError('External report assets are not fetched; use verified local exports')
    if location.startswith('#'): return location
    path = Path(os.path.normpath(str(Path(root) / lang / unquote(parsed.path))))
    relative = path.as_posix()
    validate_relative_path(relative)
    snapshot = store.read(relative)
    if snapshot.data is None: raise ValidationError('Referenced local report artifact is missing: ' + relative)
    store.report_references[relative] = snapshot
    if not image: return location
    store.report_images.add(relative)
    suffix = path.suffix.lower()
    if suffix == '.svg': _safe_svg(snapshot.data)
    mime = {'.png': 'image/png', '.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}.get(suffix)
    if mime is None: raise ValidationError('Unsupported embedded image format; PDF figures need a display export')
    return 'data:' + mime + ';base64,' + base64.b64encode(snapshot.data).decode()


def _transform(value, store, root, lang, equations):
    if isinstance(value, list): return [_transform(v, store, root, lang, equations) for v in value]
    if not isinstance(value, dict): return value
    if value.get('t') == 'Math':
        mode, latex = value['c']; equations.append((mode['t'], latex))
        return {'t': 'RawInline', 'c': ['html', _math(latex, mode['t'] == 'DisplayMath')]}
    result = {k: _transform(v, store, root, lang, equations) for k, v in value.items()}
    if result.get('t') in {'Image', 'Link'}:
        target = result['c'][-1]; target[0] = _asset(store, root, lang, target[0], result['t'] == 'Image')
    if result.get('t') in {'RawInline', 'RawBlock'}:
        if result['c'][0] != 'html' or not result['c'][1].startswith('<img class="math-'):
            raise ValidationError('Raw executable/HTML content is not accepted in report sources')
    return result


def _font(config, lang, text, preview):
    path = config.get('font_' + lang)
    family = config.get('font_family_' + lang, 'Noto Serif' if lang == 'en' else 'Noto Serif KR')
    if not path or not Path(path).is_file():
        if preview: return 'body { font-family: serif; }', {'preview_fallback': True, 'requested': family}
        raise ValidationError('Required report font is unavailable; configure font_' + lang + ' or explicitly request preview')
    from fontTools.ttLib import TTFont
    font = TTFont(path); cmap = font.getBestCmap()
    missing = {ord(c) for c in text if not c.isspace() and ord(c) >= 0x100 and ord(c) not in cmap}
    if missing and not preview: raise ValidationError('Required report font lacks source glyphs: ' + str(sorted(missing)[:10]))
    names = ' '.join(n.toUnicode() for n in font['name'].names if n.nameID in (1, 4, 6)).replace(' ', '').lower()
    if family.replace(' ', '').replace('/', '').lower() not in names and not preview:
        raise ValidationError('Configured font family does not match the requested report font')
    font.close(); data = Path(path).read_bytes()
    css = '@font-face { font-family: ReportBody; src: url(data:font/ttf;base64,' + base64.b64encode(data).decode() + '); } body { font-family: ReportBody; }'
    return css, {'requested': family, 'sha256': hashlib.sha256(data).hexdigest(), 'missing_glyphs': sorted(missing)}


def _checkpoint(event, index=None):
    """Failure-injection seam for staged paired output publication."""


def render_report(project, unit, revision):
    checked = validate_report(project, unit)
    if checked['metadata']['revision'] != revision: raise ValidationError('Source and requested report revision differ')
    with Store(project) as store:
        store.report_references = {}; store.report_images = set()
        config = configuration(store)['reporting']; root = checked['root']
        pandoc = config.get('pandoc', 'pandoc'); preview = config.get('preview', False)
        css_snapshot = store.read('tools/report.css')
        if css_snapshot.data is None: raise ValidationError('Report stylesheet is missing')
        css = css_snapshot.data.decode()
        documents, equations, fonts, pages = {}, {}, {}, {}
        try:
            from weasyprint import HTML, default_url_fetcher
        except ImportError as exc: raise ValidationError('Rendering requires the optional WeasyPrint environment') from exc
        def fetch(url, *args, **kwargs):
            if not url.startswith('data:'): raise ValidationError('Rendering refused an external resource fetch')
            return default_url_fetcher(url, *args, **kwargs)
        # Isolate optional renderer caches from the project and user configuration.
        with tempfile.TemporaryDirectory(prefix='framework-report-') as temporary:
            previous = os.environ.get('MPLCONFIGDIR'); os.environ['MPLCONFIGDIR'] = temporary
            try:
                for lang in ('en', 'ko'):
                    source = checked['sources'][lang].data
                    clean_source = re.sub(br'<!--.*?-->', b'', source, flags=re.S)
                    ast = decode(_pandoc(pandoc, ['--from=markdown-raw_html', '--to=json'], clean_source))
                    equations[lang] = []
                    transformed = _transform(ast, store, root, lang, equations[lang])
                    fragment = _pandoc(pandoc, ['--from=json', '--to=html5'], encode(transformed)).decode()
                    # Check rendered Unicode text rather than markup/TeX commands.
                    visible = re.sub(r'<[^>]+>', '', html.unescape(fragment))
                    font_css, fonts[lang] = _font(config, lang, visible, preview)
                    banner = '<p>PREVIEW: font substitutions or glyph limitations may apply.</p>' if preview else ''
                    output = '<!doctype html><html lang="' + lang + '"><head><meta charset="utf-8"><title>' + html.escape(unit) + '</title><style>' + css + font_css + '</style></head><body>' + banner + fragment + '</body></html>'
                    warnings = []
                    class Capture(logging.Handler):
                        def emit(self, record): warnings.append(record.getMessage())
                    handler = Capture(); logger = logging.getLogger('weasyprint'); logger.addHandler(handler)
                    try:
                        document = HTML(string=output, url_fetcher=fetch).render()
                        pdf = document.write_pdf(); pages[lang] = len(document.pages)
                    finally: logger.removeHandler(handler)
                    if warnings and not preview: raise ValidationError('Renderer warnings require review: ' + '; '.join(warnings))
                    stem = 'report.preview' if preview else 'report'
                    documents[lang + '/' + stem + '.html'] = output.encode()
                    documents[lang + '/' + stem + '.pdf'] = pdf
                    documents[lang + '/report.md'] = source
            finally:
                if previous is None: os.environ.pop('MPLCONFIGDIR', None)
                else: os.environ['MPLCONFIGDIR'] = previous
        if equations['en'] != equations['ko']: raise ValidationError('Bilingual mathematical expressions differ')
        if not store.report_images <= {f['path'] for f in checked['figures']}:
            raise ValidationError('Every displayed scientific image requires figure display/provenance metadata')
        checked['references'] = store.report_references
        receipt, checked['installation_snapshot'] = read_receipt(store)
        rendered = {'schema_version': 1, 'unit_id': checked['metadata']['unit_id'], 'revision': revision,
            'preview': bool(preview), 'page_counts_informational': pages, 'fonts': fonts,
            'framework_version': receipt['release']['framework_version'],
            'review_required': checked['review_required'],
            'files': {p: fingerprint(data) for p, data in documents.items()}}
        documents['report.json'] = checked['metadata_snapshot'].data
        documents['render.json'] = encode(rendered)
    return _publish(project, checked, css_snapshot, documents, rendered)


def _publish(project, checked, css_snapshot, documents, rendered):
    with Store(project) as store, store.lock():
        for operation in store.names('.research-framework/report-builds'):
            previous, _, _ = _report_journal(store, operation)
            if previous['unit'] == checked['unit'] and previous['status'] == 'PREPARED':
                raise ValidationError('An interrupted report build requires guarded recovery first')
        for lang in ('en', 'ko'): store.check(checked['root'] + '/' + lang + '/report.md', checked['sources'][lang])
        store.check(checked['root'] + '/report.json', checked['metadata_snapshot'])
        store.check('tools/report.css', css_snapshot)
        store.check('framework-project.json', checked['config_snapshot'])
        store.check('.research-framework/installation.json', checked['installation_snapshot'])
        for path, snapshot in checked['references'].items(): store.check(path, snapshot)
        for figure in checked['figures']:
            if store.read(figure['path']).fingerprint() != {k: figure[k] for k in ('size', 'sha256', 'mode')}:
                raise ValidationError('Figure changed during rendering')
        root = checked['root']; archive = root + '/revisions/' + rendered['revision']
        if store.directory(archive) is not None: raise ValidationError('Report revision already exists; preserve it and choose a new REV###')
        store.ensure_dir(archive)
        for path, data in documents.items():
            store.ensure_dir(archive + '/' + path.rsplit('/', 1)[0]) if '/' in path else None
            store.create(archive + '/' + path, data)
        operation = uuid.uuid4().hex; directory = '.research-framework/report-builds/' + operation
        store.ensure_dir(directory)
        outputs = [p for p in documents if p.endswith(('.html', '.pdf'))] + ['render.json']
        entries = []
        for index, relative in enumerate(outputs):
            path = root + '/' + relative; before = store.read(path)
            if before.data is not None:
                store.create(directory + '/before-' + str(index), before.data)
                if store.read(directory + '/before-' + str(index)).data != before.data: raise ValidationError('Report backup verification failed')
            entries.append({'path': path, 'before': before.fingerprint(), 'before_token': before.token,
                            'parents': before.parents,
                            'after': fingerprint(documents[relative], before.mode or '0644'), 'archive': archive + '/' + relative,
                            'progress': 'pending', 'after_token': None, 'restore_token': None, 'restored': False})
        journal = {'schema_version': 1, 'unit': checked['unit'], 'root': root, 'root_identity': store.identity,
                   'status': 'PREPARED', 'entries': entries}
        _save_report(store, directory, journal)
        try:
            for index, entry in enumerate(entries):
                current = store.read(entry['path'])
                if current.fingerprint() != entry['before'] or current.token != (tuple(entry['before_token']) if entry['before_token'] else None):
                    raise ValidationError('Report output changed before publication')
                entry['progress'] = 'writing'; _save_report(store, directory, journal)
                _checkpoint('before_publish', index)
                after = _replace(store, entry['path'], documents[outputs[index]], current)
                _checkpoint('published', index)
                entry.update(progress='done', after_token=after.token); _save_report(store, directory, journal)
            journal['status'] = 'COMMITTED'; _save_report(store, directory, journal)
            return {**rendered, 'operation_id': operation, 'revision_directory': archive,
                    'acceptance': 'Rendering complete; scientific, bilingual and visual review remain explicit record decisions.'}
        except Exception:
            _recover_report(store, operation)
            raise


def _save_report(store, directory, journal):
    signed = {**journal, 'checksum': hashlib.sha256(encode(journal)).hexdigest()}
    store.atomic(directory + '/journal.json', encode(signed), store.read(directory + '/journal.json', MAX_METADATA))


def _report_journal(store, operation):
    if not re.fullmatch(r'[0-9a-f]{32}', operation): raise ValidationError('Invalid report operation ID')
    directory = '.research-framework/report-builds/' + operation
    snapshot = store.read(directory + '/journal.json', MAX_METADATA)
    if snapshot.data is None: raise ValidationError('Report journal is missing')
    journal = decode(snapshot.data); checksum = journal.pop('checksum', None)
    if checksum != hashlib.sha256(encode(journal)).hexdigest(): raise ValidationError('Report journal checksum mismatch')
    if journal['root'] != _unit(store, journal['unit']): raise ValidationError('Report recovery root mismatch')
    if tuple(journal['root_identity']) != store.identity: raise ValidationError('Report recovery project identity changed')
    if journal['status'] not in {'PREPARED', 'COMMITTED', 'ROLLED_BACK'}: raise ValidationError('Unknown report journal state')
    allowed = {journal['root'] + '/' + lang + '/report' + preview + suffix
               for lang in ('en', 'ko') for preview in ('', '.preview') for suffix in ('.html', '.pdf')}
    allowed.add(journal['root'] + '/render.json')
    if any(e['path'] not in allowed for e in journal['entries']): raise ValidationError('Unregistered report recovery target')
    return journal, directory, snapshot


def report_recovery_plan(project, operation):
    with Store(project) as store:
        journal, directory, snapshot = _report_journal(store, operation)
        targets = []
        for index, entry in enumerate(journal['entries']):
            current = store.read(entry['path'])
            for path, token in entry['parents']:
                if token is not None and dict(current.parents).get(path) != tuple(token):
                    raise ValidationError('Report recovery parent changed')
            expected = entry['before'] if entry['restored'] or entry['progress'] == 'pending' else entry['after']
            token = entry['restore_token'] if entry['restored'] else entry['before_token'] if entry['progress'] == 'pending' else entry['after_token']
            valid = current.fingerprint() == expected and (token is None or current.token == tuple(token))
            if entry['progress'] == 'writing': valid = valid or current.fingerprint() == entry['before']
            if not valid: raise ValidationError('Report recovery would overwrite later local work: ' + entry['path'])
            if entry['before'] is not None:
                blob = store.read(directory + '/before-' + str(index))
                if blob.data is None or fingerprint(blob.data, entry['before']['mode']) != entry['before']:
                    raise ValidationError('Report recovery backup mismatch')
            targets.append({'path': entry['path'], 'fingerprint': current.fingerprint(), 'token': current.token})
        return {'plan_digest': hashlib.sha256(encode({'journal': snapshot.fingerprint(), 'targets': targets})).hexdigest(),
                'status': journal['status'], 'targets': targets}


def _recover_report(store, operation):
    report_recovery_plan(store.root, operation)
    journal, directory, _ = _report_journal(store, operation)
    for index in reversed(range(len(journal['entries']))):
        entry = journal['entries'][index]
        if entry['restored']: continue
        current = store.read(entry['path'])
        entry['progress'] = 'writing'; _save_report(store, directory, journal)
        if current.fingerprint() != entry['before']:
            if entry['before'] is None: store.remove(entry['path'], current)
            else:
                blob = store.read(directory + '/before-' + str(index))
                _replace(store, entry['path'], blob.data, current)
        entry.update(restored=True, restore_token=store.read(entry['path']).token)
        _save_report(store, directory, journal)
    journal['status'] = 'ROLLED_BACK'; _save_report(store, directory, journal)
    return {'status': 'ROLLED_BACK', 'retained_revision': journal['root'] + '/revisions'}


def recover_report(project, operation, digest):
    with Store(project) as store, store.lock():
        if report_recovery_plan(project, operation)['plan_digest'] != digest: raise ValidationError('Report recovery plan changed')
        return _recover_report(store, operation)
