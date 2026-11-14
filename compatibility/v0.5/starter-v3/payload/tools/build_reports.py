#!/usr/bin/env python3
"""Build English/Korean report HTML and PDF from editable Markdown sources."""

from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_ROOT = PROJECT_ROOT / "reports"
PLACEHOLDER_RE = re.compile(r"\[\[[^\]]+\]\]")
STATUS_RE = re.compile(r"(?m)^\*\*Status:\*\*\s*(\w+)")
OUTCOME_RE = re.compile(r"(?m)^\*\*Scientific outcome:\*\*\s*(\w+)")


def available_font_families() -> str | None:
    if not shutil.which("fc-list"):
        return None
    try:
        return subprocess.run(
            ["fc-list", ":", "family"], check=True, capture_output=True, text=True
        ).stdout.casefold()
    except (OSError, subprocess.CalledProcessError):
        return None


def verify_fonts(allow_substitution: bool) -> None:
    available = available_font_families()
    if available is None:
        if allow_substitution:
            print("WARNING: Cannot check installed fonts; PDF font substitution is possible.")
            return
        raise RuntimeError("Fontconfig/fc-list is required to verify Noto Serif fonts.")
    en_ok = "noto serif" in available
    ko_ok = "noto serif kr" in available or "noto serif cjk kr" in available
    missing = []
    if not en_ok:
        missing.append("Noto Serif")
    if not ko_ok:
        missing.append("Noto Serif KR or Noto Serif CJK KR")
    if missing and not allow_substitution:
        raise RuntimeError(
            "Required report fonts missing: " + ", ".join(missing)
            + ". Install the fonts or pass --allow-font-substitution for a preview only."
        )
    if missing:
        print("WARNING: Missing fonts; preview may substitute: " + ", ".join(missing))


def find_unit(folder_or_id: str) -> Path:
    exact = REPORTS_ROOT / folder_or_id
    if exact.is_dir():
        return exact
    matches = list(REPORTS_ROOT.glob(folder_or_id + "_*"))
    if len(matches) == 1 and matches[0].is_dir():
        return matches[0]
    if not matches:
        raise RuntimeError(f"Report unit not found: {folder_or_id}")
    raise RuntimeError(f"Ambiguous unit ID: {folder_or_id}. Use the complete folder name.")


def read_png_dpi(path: Path) -> tuple[float, float] | None:
    # Read the PNG pHYs chunk without requiring a third-party imaging package.
    with path.open("rb") as stream:
        if stream.read(8) != b"\x89PNG\r\n\x1a\n":
            raise RuntimeError(f"Invalid PNG signature: {path}")
        while True:
            header = stream.read(8)
            if len(header) != 8:
                return None
            size, chunk = struct.unpack(">I4s", header)
            if size > 50_000_000:
                raise RuntimeError(f"Implausible PNG chunk length in {path}")
            content = stream.read(size)
            if len(content) != size or len(stream.read(4)) != 4:
                raise RuntimeError(f"Truncated PNG: {path}")
            if chunk == b"pHYs":
                if size != 9:
                    raise RuntimeError(f"Invalid pHYs chunk in {path}")
                xppm, yppm, unit = struct.unpack(">IIB", content)
                return (xppm * 0.0254, yppm * 0.0254) if unit == 1 else None
            if chunk in (b"IDAT", b"IEND"):
                return None


def verify_unit(unit: Path, allow_draft: bool) -> dict[str, str]:
    sources = {}
    for lang in ("en", "ko"):
        source = unit / lang / "report.md"
        if not source.is_file():
            raise RuntimeError(f"Missing source: {source}")
        content = source.read_text(encoding="utf-8")
        sources[lang] = content
        if not allow_draft:
            status = STATUS_RE.search(content)
            outcome = OUTCOME_RE.search(content)
            if not status or status.group(1) != "COMPLETED":
                raise RuntimeError(f"{source}: status must be COMPLETED for a final build.")
            if not outcome or outcome.group(1) not in ("SUPPORTED", "NOT_SUPPORTED", "INCONCLUSIVE"):
                raise RuntimeError(f"{source}: set a valid scientific outcome before finalizing.")
            pending = PLACEHOLDER_RE.search(content)
            if pending:
                raise RuntimeError(f"{source}: unresolved placeholder {pending.group(0)}")

    if not allow_draft:
        figures = PROJECT_ROOT / "analyses" / unit.name / "figures"
        missing = [str(figures / f"figure_01.{ext}") for ext in ("png", "pdf", "svg")
                   if not (figures / f"figure_01.{ext}").is_file()]
        if missing:
            raise RuntimeError("Missing required main figure exports: " + ", ".join(missing))
        png_path = figures / "figure_01.png"
        dpi = read_png_dpi(png_path)
        if dpi is None or any(abs(axis - 600.0) > 1.0 for axis in dpi):
            raise RuntimeError(
                f"Main PNG must declare 600 dpi in pHYs metadata, found {dpi}: {png_path}"
            )
    return sources


def html_document(body: str, lang: str, title: str, stylesheet: str) -> str:
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<style>\n{stylesheet}\n</style>
</head>
<body>
{body}
</body>
</html>
"""


def render_markdown(content: str) -> str:
    proc = subprocess.run(
        ["pandoc", "--from=gfm+tex_math_dollars", "--to=html5", "--mathml", "--wrap=none"],
        input=content, check=True, capture_output=True, text=True
    )
    return proc.stdout


def build_unit(unit: Path, sources: dict[str, str], stylesheet: str) -> None:
    from weasyprint import HTML

    for lang, content in sources.items():
        target_dir = unit / lang
        html_path = target_dir / "report.html"
        pdf_path = target_dir / "report.pdf"
        body = render_markdown(content)
        html_path.write_text(html_document(body, lang, unit.name, stylesheet), encoding="utf-8")
        document = HTML(filename=str(html_path)).render()
        document.write_pdf(str(pdf_path))
        page_count = len(document.pages)
        print(f"Wrote {html_path}")
        print(f"Wrote {pdf_path} ({page_count} page(s))")
        if page_count > 2:
            print(f"WARNING: {lang} report exceeds the 1-2 page target; revise for concision.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("unit", nargs="?", help="Complete folder name or unique A###-S##-T##")
    parser.add_argument("--all", action="store_true", help="Build all complete units")
    parser.add_argument("--allow-draft", action="store_true", help="Preview incomplete reports")
    parser.add_argument(
        "--allow-font-substitution", action="store_true",
        help="Preview without verified Noto Serif font families"
    )
    args = parser.parse_args()
    if args.all == bool(args.unit):
        parser.error("Pass exactly one unit or --all")
    if not shutil.which("pandoc"):
        parser.error("Pandoc is required: install it in the WSL environment")
    try:
        import weasyprint  # noqa: F401
    except ImportError:
        parser.error("WeasyPrint is required: python3 -m pip install weasyprint")

    try:
        verify_fonts(args.allow_font_substitution)
        css = (PROJECT_ROOT / "tools" / "report.css").read_text(encoding="utf-8")
        if args.all:
            units = sorted(folder for folder in REPORTS_ROOT.iterdir() if folder.is_dir())
            if not units:
                print("No report units found.")
                return 0
        else:
            units = [find_unit(args.unit)]

        built = 0
        for unit in units:
            if args.all and not args.allow_draft:
                content_path = unit / "en" / "report.md"
                if not content_path.is_file() or not STATUS_RE.search(content_path.read_text(encoding="utf-8")):
                    continue
                if STATUS_RE.search(content_path.read_text(encoding="utf-8")).group(1) != "COMPLETED":
                    print(f"Skipped draft unit: {unit.name}")
                    continue
            sources = verify_unit(unit, args.allow_draft)
            build_unit(unit, sources, css)
            built += 1
        print(f"Built {built} unit(s). Inspect page counts, typography, and figure rendering.")
        return 0
    except (RuntimeError, subprocess.CalledProcessError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
