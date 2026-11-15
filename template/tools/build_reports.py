#!/usr/bin/env python3
"""Render explicit EN/KO report revisions from Markdown; no scientific execution."""

import argparse
import base64
from collections import Counter
import hashlib
import html
import io
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit
import uuid

sys.dont_write_bytecode = True
from project_common import digest, encode, load_json, lock, read, relative, safe_path, write

ValidationError = ValueError
PROJECT = Path(__file__).resolve().parents[1]
SECTIONS = ('motivation', 'question', 'strategy', 'methods', 'specifications', 'execution',
            'evidence', 'results', 'interpretation', 'limitations', 'provenance')
STATUS = {'PLANNING', 'APPROVED', 'EXECUTING', 'WAITING', 'BLOCKED', 'FAILED', 'COMPLETED'}
OUTCOME = {'NOT_EVALUATED', 'SUPPORTED', 'NOT_SUPPORTED', 'INCONCLUSIVE'}


def _source(text, metadata):
    # Guidance comments are not scientific content and may remain in drafts.
    visible = re.sub(r'<!--(?! section:).*?-->', '', text, flags=re.S)
    if re.search(r'\{\{|\}\}|\bTODO\b|\bTBD\b|<<<<<<<|>>>>>>>', visible):
        raise ValidationError('Report contains unresolved placeholders or conflict markers')
    markers = re.findall(r'<!-- section: ([a-z]+) -->', visible)
    if tuple(markers) != SECTIONS: raise ValidationError('Report must retain eleven corresponding sections in order')
    chunks = re.split(r'<!-- section: [a-z]+ -->', visible)[1:]
    for name, chunk in zip(SECTIONS, chunks):
        if not re.match(r'^##\s+\S', chunk.strip()): raise ValidationError('Scientific section heading missing: ' + name)
        body = re.sub(r'^##[^\n]*(?:\n|$)', '', chunk.strip(), count=1).strip()
        if not body: raise ValidationError('Empty scientific section: ' + name)
    for field, expected in [('Unit ID', metadata['unit_id']), ('Status', metadata['status']),
                            ('Outcome', metadata['outcome']), ('Report revision', metadata['revision'])]:
        match = re.search(r'^\*\*' + re.escape(field) + r':\*\*\s*(\S+)\s*$', text, re.M)
        if match is None or match.group(1) != expected: raise ValidationError('Bilingual report metadata mismatch: ' + field)
    return visible


def _numbers(text):
    text = re.sub(r'^#+.*$', '', text, flags=re.M)
    text = re.sub(r'\*\*[^\n]+|!?\[[^\]]*\]\([^)]*\)|<!--.*?-->', '', text)
    return Counter(re.findall(r'[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?', text))



def _safe_svg(data):
    text = data.decode('utf-8')
    text = re.sub(r'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1\.1//EN"\s+"http://www\.w3\.org/Graphics/SVG/1\.1/DTD/svg11\.dtd">', '', text)
    if (re.search(r'<!DOCTYPE|<!ENTITY|<script|<foreignObject|@import|\son[a-z]+\s*=', text, re.I)
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



def _font(config, lang, text, preview):
    path = config.get('font_' + lang)
    family = config.get('font_family_' + lang, 'Noto Serif' if lang == 'en' else 'Noto Serif KR')
    if not path:
        try:
            from matplotlib.font_manager import FontProperties, findfont
            path = findfont(FontProperties(family=family), fallback_to_default=False)
        except ValueError:
            path = None
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


def validate_report(project, unit):
    """Check structure and numeric correspondence; semantic review remains explicit."""
    if not re.fullmatch(r'A(?!000)[0-9]{3}-S(?!00)[0-9]{2}-T(?!00)[0-9]{2}', unit):
        raise ValueError('Expected an AST identity A###-S##-T##')
    root = 'reports/' + unit
    metadata = load_json(project, root + '/report.json')
    if metadata.get('unit_id') != unit or metadata.get('status') not in STATUS or metadata.get('outcome') not in OUTCOME:
        raise ValueError('Invalid report identity/status/outcome')
    if not re.fullmatch(r'REV[0-9]{3}', metadata.get('revision', '')):
        raise ValueError('Expected report revision REV###, distinct from optional Run R###')
    if metadata['status'] == 'COMPLETED' and metadata['outcome'] == 'NOT_EVALUATED' and not metadata.get('outcome_reason', '').strip():
        raise ValueError('Completed NOT_EVALUATED work requires its actual reason')
    review = metadata.get('review', {})
    if any(type(review.get(k)) is not bool for k in ['methods', 'bilingual', 'visual']) or not isinstance(review.get('references'), list):
        raise ValueError('Record methods, bilingual and visual review explicitly')
    if any(review[k] for k in ['methods', 'bilingual', 'visual']) and not review['references']:
        raise ValueError('Recorded reviews require actual review references')
    if not isinstance(metadata.get('provenance'), list) or not isinstance(metadata.get('figures'), list):
        raise ValueError('Provenance and figures must be lists')
    watched = {}
    def take(path):
        snapshot = read(project, path)
        if snapshot is None:
            raise ValueError('Required file is missing: ' + path)
        watched[path] = snapshot
        return snapshot[0]
    take(root + '/report.json')
    sources = {lang: take(root + '/' + lang + '/report.md') for lang in ['en', 'ko']}
    visible = {lang: _source(data.decode(), metadata) for lang, data in sources.items()}
    if _numbers(visible['en']) != _numbers(visible['ko']):
        raise ValueError('Bilingual numeric tokens differ; review definitions, parameters and findings')
    figures = {}
    for item in metadata['figures']:
        path = relative(item['path']); data = take(path)
        if path in figures:
            raise ValueError('Duplicate figure declaration: ' + path)
        width = item.get('width_mm')
        if type(width) not in (int, float) or not 0 < width < float('inf'):
            raise ValueError('Figure intended physical width must be positive and finite')
        if item.get('kind') not in ['plot', 'measurement'] or type(item.get('raster_embedded')) is not bool:
            raise ValueError('Declare figure kind and embedded raster integrity')
        exception = item.get('exception')
        if exception is not None and (not isinstance(exception, str) or not exception.strip()):
            raise ValueError('Figure exceptions require an explicit reason')
        if not exception and item['kind'] == 'plot' and (item.get('font_family') != 'Arial' or not 5 <= item.get('text_size_pt', 0) <= 7):
            raise ValueError('Figure font defaults require Arial 5–7 pt or an explicit exception')
        suffix = Path(path).suffix.lower()
        if suffix == '.png':
            from PIL import Image
            with Image.open(io.BytesIO(data)) as image:
                dpi = image.info.get('dpi', ())
                physical = image.width / (width / 25.4)
            if not exception and (len(dpi) != 2 or any(abs(d - 600) > 1 for d in dpi) or physical < 590):
                raise ValueError('PNG must declare 600 dpi at its intended physical width')
        elif suffix == '.svg':
            _safe_svg(data)
        elif suffix != '.pdf' or not data.startswith(b'%PDF'):
            raise ValueError('Expected PNG, SVG or PDF figure export')
        figures[path] = item
    return {'root': root, 'metadata': metadata, 'sources': sources, 'watched': watched,
            'figures': figures, 'review_required': [k for k in ['methods', 'bilingual', 'visual'] if not review[k]]}


def transform(value, project, checked, lang, equations):
    if isinstance(value, list):
        return [transform(v, project, checked, lang, equations) for v in value]
    if not isinstance(value, dict):
        return value
    if value.get('t') == 'Math':
        mode, latex = value['c']; equations.append((mode['t'], latex))
        image = _math(latex, mode['t'] == 'DisplayMath')
        if mode['t'] == 'DisplayMath':
            image = '<span class="math-block">' + image + '</span>'
        return {'t': 'RawInline', 'c': ['html', image]}
    if value.get('t') in {'RawInline', 'RawBlock'}:
        raise ValueError('Raw HTML/TeX is unsupported; use Markdown and supported math')
    result = {k: transform(v, project, checked, lang, equations) for k, v in value.items()}
    if result.get('t') in {'Image', 'Link'}:
        target = result['c'][-1]; location = target[0]; parsed = urlsplit(location)
        image = result['t'] == 'Image'
        if parsed.scheme or parsed.netloc:
            if not image and parsed.scheme in {'https', 'http', 'doi', 'mailto'}:
                return result
            raise ValueError('External assets are not fetched; use verified local exports')
        if location.startswith('#'):
            return result
        path = os.path.normpath(checked['root'] + '/' + lang + '/' + unquote(parsed.path))
        artifact = safe_path(project, path)
        if not artifact.exists():
            raise ValueError('Referenced local artifact is missing: ' + path)
        if image:
            declared = checked['figures'].get(path)
            if declared is None:
                raise ValueError('Displayed image needs figure metadata: ' + path)
            data = checked['watched'][path][0]
            mime = {'.png': 'image/png', '.svg': 'image/svg+xml'}.get(artifact.suffix.lower())
            if mime is None:
                raise ValueError('A PDF figure needs a PNG/SVG display export')
            target[0] = 'data:' + mime + ';base64,' + base64.b64encode(data).decode()
            result['c'][0] = ['', [], [['style', 'width:' + str(declared['width_mm']) + 'mm']]]
        else:
            # Resolve relative artifact links correctly from the archived HTML too.
            # This inspects existence only and does not read large/restricted data.
            target[0] = artifact.as_uri() + ('#' + parsed.fragment if parsed.fragment else '')
    return result


def render_report(project, unit, revision=None, preview=False):
    checked = validate_report(project, unit)
    metadata = checked['metadata']; revision = revision or metadata['revision']
    if revision != metadata['revision']:
        raise ValueError('Requested and source report revisions differ')
    if not preview and metadata['status'] != 'COMPLETED':
        raise ValueError('Final rendering requires COMPLETED status; drafts use --preview')
    root = checked['root']; archive = root + '/revisions/' + revision
    if not preview and safe_path(project, archive).exists():
        raise ValueError('Report revision already exists; choose a new REV### and retain the same AST ID')
    if not preview:
        current = read(project, root + '/current.json')
        checked['watched'][root + '/current.json'] = current
        previous = json.loads(current[0]) if current else None
        if previous and (not re.fullmatch(r'REV[0-9]{3}', previous.get('revision', '')) or previous.get('directory') != root + '/revisions/' + previous['revision']):
            raise ValueError('Invalid current report revision pointer')
        for lang in ['en', 'ko']:
            for suffix in ['html', 'pdf']:
                path = root + '/' + lang + '/report.' + suffix
                latest = read(project, path)
                checked['watched'][path] = latest
                if latest is not None:
                    saved = read(project, previous['directory'] + '/' + lang + '/report.' + suffix) if previous else None
                    if saved is None or latest[0] != saved[0]:
                        raise ValueError('Latest report has unarchived local changes; preserve/review them before rendering: ' + path)
    for path in ['framework-project.json', 'tools/report.css', '.framework/manifest.json', 'tools/build_reports.py']:
        snapshot = read(project, path)
        if snapshot is None:
            raise ValueError('Missing project/report setting: ' + path)
        checked['watched'][path] = snapshot
    config = json.loads(checked['watched']['framework-project.json'][0])['reporting']
    version = json.loads(checked['watched']['.framework/manifest.json'][0])['version']
    css = checked['watched']['tools/report.css'][0].decode()
    from weasyprint import HTML, default_url_fetcher
    def fetch(url, *args, **kwargs):
        if not url.startswith('data:'):
            raise ValueError('Renderer resource fetch must be embedded data')
        return default_url_fetcher(url, *args, **kwargs)
    documents, equations, fonts, pages = {}, {}, {}, {}
    with tempfile.TemporaryDirectory(prefix='research-report-') as temporary:
        previous = os.environ.get('MPLCONFIGDIR'); os.environ['MPLCONFIGDIR'] = temporary
        try:
            for lang in ['en', 'ko']:
                source = re.sub(br'<!--.*?-->', b'', checked['sources'][lang], flags=re.S)
                reader = 'markdown-raw_attribute-header_attributes-link_attributes-fenced_divs-fenced_code_attributes'
                ast = json.loads(_pandoc(config.get('pandoc', 'pandoc'), ['--from=' + reader, '--to=json'], source))
                equations[lang] = []
                transformed = transform(ast, project, checked, lang, equations[lang])
                fragment = _pandoc(config.get('pandoc', 'pandoc'), ['--from=json', '--to=html5'], encode(transformed)).decode()
                # Keep a display equation with its preceding explanatory paragraph.
                fragment = re.sub(r'(<p>(?:(?!</p>).)*</p>)\s*(<p>\s*<span class="math-block">.*?</span>\s*</p>)',
                                  r'<div class="equation-group">\1\2</div>', fragment, flags=re.S)
                font_config = dict(config)
                location = font_config.get('font_' + lang)
                if location and not Path(location).is_absolute():
                    font_config['font_' + lang] = str(safe_path(project, location))
                visible = re.sub(r'<[^>]+>', '', html.unescape(fragment))
                font_css, fonts[lang] = _font(font_config, lang, visible, preview)
                banner = '<p class="preview">PREVIEW: draft or font substitution; not final.</p>' if preview else ''
                output = '<!doctype html><html lang="' + lang + '"><head><meta charset="utf-8"><title>' + html.escape(unit) + '</title><style>' + css + font_css + '</style></head><body>' + banner + fragment + '</body></html>'
                warnings = []
                class Capture(logging.Handler):
                    def emit(self, record):
                        warnings.append(record.getMessage())
                logger = logging.getLogger('weasyprint'); handler = Capture(); logger.addHandler(handler)
                try:
                    rendered = HTML(string=output, url_fetcher=fetch).render()
                    pdf = rendered.write_pdf(); pages[lang] = len(rendered.pages)
                finally:
                    logger.removeHandler(handler)
                if warnings and not preview:
                    raise ValueError('Renderer warnings need review: ' + '; '.join(warnings))
                documents[lang + '/report.md'] = checked['sources'][lang]
                documents[lang + '/report.html'] = output.encode()
                documents[lang + '/report.pdf'] = pdf
        finally:
            if previous is None:
                os.environ.pop('MPLCONFIGDIR', None)
            else:
                os.environ['MPLCONFIGDIR'] = previous
    if equations['en'] != equations['ko']:
        raise ValueError('Bilingual mathematical expressions differ')
    result = {'framework_version': version, 'unit_id': unit, 'revision': revision, 'preview': preview,
              'page_counts_informational': pages, 'fonts': fonts, 'review_required': checked['review_required'],
              'source_hashes': {p: digest(s[0]) for p, s in checked['watched'].items() if s is not None},
              'files': {p: digest(data) for p, data in documents.items()}}
    documents['report.json'] = encode(metadata); documents['render.json'] = encode(result)
    with lock(project):
        for path, snapshot in checked['watched'].items():
            if read(project, path) != snapshot:
                raise ValueError('Report input changed while rendering: ' + path)
        target = root + '/previews/' + uuid.uuid4().hex if preview else archive
        if safe_path(project, target).exists():
            raise ValueError('Report revision already exists')
        # One complete immutable revision is authoritative. Latest copies are conveniences.
        staging = root + '/.build-' + uuid.uuid4().hex
        safe_path(project, staging).mkdir()
        for path, data in documents.items():
            write(project, staging + '/' + path, data)
        safe_path(project, target).parent.mkdir(parents=True, exist_ok=True)
        os.rename(safe_path(project, staging), safe_path(project, target))
        result['revision_directory'] = target
        if not preview:
            for path, data in documents.items():
                if path.endswith(('.html', '.pdf')) or path == 'render.json':
                    before = read(project, root + '/' + path)
                    write(project, root + '/' + path, data, expected=before, replace=before is not None)
            before = read(project, root + '/current.json')
            write(project, root + '/current.json', encode({'revision': revision, 'directory': target}), expected=before, replace=before is not None)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('unit', help='Existing AST identity')
    parser.add_argument('--project', type=Path, default=PROJECT)
    parser.add_argument('--revision')
    parser.add_argument('--check', action='store_true', help='Read-only structural/scalar/asset checks')
    parser.add_argument('--preview', action='store_true', help='Disclosed draft/font preview in a separate directory')
    args = parser.parse_args(argv)
    try:
        if args.check:
            checked = validate_report(args.project, args.unit)
            result = {'valid': True, 'unit_id': args.unit, 'review_required': checked['review_required']}
        else:
            result = render_report(args.project, args.unit, args.revision, args.preview)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, ImportError) as exc:
        print('Report operation stopped: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
