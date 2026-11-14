#!/usr/bin/env python3
"""Create a draft Aim/Strategy/Tactic research unit without touching code repositories."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UNIT_RE = re.compile(r"^(A\d{3})-(S\d{2})-(T\d{2})$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("unit_id", help="For example A001-S01-T01")
    parser.add_argument("slug", help="Short snake_case label, for example barcode_distribution")
    args = parser.parse_args()

    match = UNIT_RE.fullmatch(args.unit_id)
    if not match:
        parser.error("unit_id must have the form A###-S##-T##")
    if not SLUG_RE.fullmatch(args.slug):
        parser.error("slug must be lowercase snake_case")

    unit_folder = f"{args.unit_id}_{args.slug}"
    report_base = PROJECT_ROOT / "reports" / unit_folder
    analysis_base = PROJECT_ROOT / "analyses" / unit_folder

    existing_id_matches = list((PROJECT_ROOT / "reports").glob(f"{args.unit_id}_*"))
    existing_id_matches += list((PROJECT_ROOT / "analyses").glob(f"{args.unit_id}_*"))
    if report_base.exists() or analysis_base.exists() or existing_id_matches:
        print(f"Refusing to overwrite or reuse an existing unit ID: {args.unit_id}", file=sys.stderr)
        return 2

    replacements = {
        "{{UNIT_ID}}": args.unit_id,
        "{{UNIT_FOLDER}}": unit_folder,
        "{{AIM_ID}}": match.group(1),
        "{{STRATEGY_ID}}": match.group(2),
        "{{TACTIC_ID}}": match.group(3),
        "{{DATE}}": date.today().isoformat(),
    }

    for lang in ("en", "ko"):
        source_template = PROJECT_ROOT / "templates" / f"report.{lang}.md"
        source = source_template.read_text(encoding="utf-8")
        for marker, value in replacements.items():
            source = source.replace(marker, value)
        report_dir = report_base / lang
        report_dir.mkdir(parents=True)
        (report_dir / "report.md").write_text(source, encoding="utf-8")

    for subdir in ("results", "figures", "logs"):
        folder = analysis_base / subdir
        folder.mkdir(parents=True)
        (folder / ".gitkeep").touch()

    print(f"Created draft unit: {unit_folder}")
    print(f"English source: {report_base / 'en' / 'report.md'}")
    print(f"Korean source:  {report_base / 'ko' / 'report.md'}")
    print(f"Output folder:  {analysis_base}")
    print("Status: PLANNING. Obtain explicit plan approval before implementation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
