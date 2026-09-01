"""Core CSV profiling logic."""

from __future__ import annotations

import csv
import statistics
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Iterable

MISSING_VALUES = {"", "na", "n/a", "null", "none", "-"}
TRUE_VALUES = {"true", "yes", "y"}
FALSE_VALUES = {"false", "no", "n"}


def _is_missing(value: str) -> bool:
    return value.strip().lower() in MISSING_VALUES


def _to_number(value: str) -> int | float:
    clean = value.strip().replace(",", "")
    try:
        return int(clean)
    except ValueError:
        return float(clean)


def infer_type(values: Iterable[str]) -> str:
    """Infer the narrowest useful type for a sequence of strings."""
    present = [value.strip() for value in values if not _is_missing(value)]
    if not present:
        return "empty"
    lowered = {value.lower() for value in present}
    if lowered <= TRUE_VALUES | FALSE_VALUES:
        return "boolean"
    try:
        numbers = [_to_number(value) for value in present]
        return "integer" if all(isinstance(value, int) for value in numbers) else "number"
    except ValueError:
        pass
    try:
        for value in present:
            date.fromisoformat(value)
        return "date"
    except ValueError:
        return "text"


def _numeric_summary(values: list[str]) -> dict[str, float | int]:
    numbers = [float(_to_number(value)) for value in values if not _is_missing(value)]
    summary: dict[str, float | int] = {
        "min": min(numbers),
        "max": max(numbers),
        "mean": round(statistics.fmean(numbers), 3),
        "median": round(statistics.median(numbers), 3),
    }
    if len(numbers) > 1:
        summary["std_dev"] = round(statistics.stdev(numbers), 3)
    return summary


def _column_summary(name: str, values: list[str], row_count: int) -> dict[str, Any]:
    present = [value for value in values if not _is_missing(value)]
    inferred_type = infer_type(values)
    counts = Counter(present)
    result: dict[str, Any] = {
        "name": name,
        "type": inferred_type,
        "missing": row_count - len(present),
        "missing_percent": round(((row_count - len(present)) / row_count * 100), 1) if row_count else 0,
        "unique": len(counts),
        "top_values": [{"value": value, "count": count} for value, count in counts.most_common(5)],
    }
    if inferred_type in {"integer", "number"} and present:
        result["numeric"] = _numeric_summary(present)
    if inferred_type == "text" and present:
        lengths = [len(value) for value in present]
        result["text"] = {"min_length": min(lengths), "max_length": max(lengths), "average_length": round(statistics.fmean(lengths), 1)}
    return result


def profile_csv(path: str | Path, max_rows: int | None = None) -> dict[str, Any]:
    """Read a CSV file and return a JSON-serializable profile."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"CSV file not found: {source}")
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(8192)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(handle, dialect=dialect)
        if not reader.fieldnames:
            raise ValueError("CSV file must include a header row.")
        rows = []
        for index, row in enumerate(reader):
            if max_rows is not None and index >= max_rows:
                break
            rows.append({name: (row.get(name) or "") for name in reader.fieldnames})

    columns = [_column_summary(name, [row[name] for row in rows], len(rows)) for name in reader.fieldnames]
    row_signatures = [tuple(row[name] for name in reader.fieldnames) for row in rows]
    return {
        "file": source.name,
        "rows": len(rows),
        "columns_count": len(reader.fieldnames),
        "duplicate_rows": len(row_signatures) - len(set(row_signatures)),
        "delimiter": "TAB" if dialect.delimiter == "\t" else dialect.delimiter,
        "columns": columns,
    }
