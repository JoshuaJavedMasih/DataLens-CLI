"""Command-line interface for DataLens."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .analyzer import profile_csv
from .report import render_html, render_terminal


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="datalens", description="Profile a CSV file without uploading your data.")
    parser.add_argument("csv_file", help="path to a CSV, TSV, or pipe-delimited file")
    parser.add_argument("--format", choices=["terminal", "json", "html"], default="terminal", help="report format (default: terminal)")
    parser.add_argument("--output", "-o", help="write the report to this file")
    parser.add_argument("--max-rows", type=int, help="inspect at most this many data rows")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        profile = profile_csv(args.csv_file, args.max_rows)
        if args.format == "json":
            report = json.dumps(profile, indent=2)
        elif args.format == "html":
            report = render_html(profile)
        else:
            report = render_terminal(profile)
        if args.output:
            Path(args.output).write_text(report, encoding="utf-8")
            print(f"Report written to {args.output}")
        else:
            print(report, end="" if report.endswith("\n") else "\n")
        return 0
    except (FileNotFoundError, ValueError, OSError) as error:
        print(f"datalens: error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
