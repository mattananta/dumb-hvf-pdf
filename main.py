from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Iterable

from pipeline import DEFAULT_TEMPLATE_PATH, extract_pdf, extract_pdf_both_eyes


def _default_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path("data")


DEFAULT_INPUT_PATH = _default_base_dir() / "input"
DEFAULT_OUTPUT_PATH = _default_base_dir() / "output" / "output.csv"


def _pdf_inputs(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted(path.rglob("*.pdf"))
    return [path]


def _subject_id(path: Path) -> str:
    return path.parent.name


def _eye_from_filename(path: Path) -> str | None:
    match = re.search(r"(?:^|[_\-\s])(LE|RE)(?:$|[_\-\s.])", path.stem, re.IGNORECASE)
    return match.group(1).upper() if match else None


def _load_template(template_path: Path) -> dict[str, object]:
    return json.loads(template_path.read_text(encoding="utf-8"))


def _csv_fieldnames(template_path: Path) -> list[str]:
    template = _load_template(template_path)

    fields = ["subject_id", "source_file", "eye"]
    for section in ["header", "threshold_map", "total_deviation", "pattern_deviation", "ght_vfi"]:
        prefix = "header" if section == "header" else section
        for eye_template in template.values():
            for label in eye_template[section]["labels"]:
                field = f"{prefix}_{label}"
                if field not in fields:
                    fields.append(field)
    return fields


def _rows_from_extraction(source_file: Path, extracted: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for eye, values in extracted.items():
        row = {
            "subject_id": _subject_id(source_file),
            "source_file": str(source_file),
            "eye": eye,
        }
        row.update(values)
        rows.append(row)
    return rows


def _write_csv(rows: list[dict[str, str]], fieldnames: list[str], output_path: Path | None) -> None:
    if output_path is None:
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(data: object, output_path: Path | None) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False)
    if output_path is None:
        print(text)
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text + "\n", encoding="utf-8")


def _extract_path(
    path: Path,
    eye: str,
    template_path: Path,
    strict: bool,
) -> dict[str, dict[str, str]]:
    inferred_eye = _eye_from_filename(path) if eye == "BOTH" else None
    if inferred_eye:
        return extract_pdf(path, inferred_eye, template_path, strict=strict)
    if eye == "BOTH":
        return extract_pdf_both_eyes(path, template_path, strict=strict)
    return extract_pdf(path, eye, template_path, strict=strict)


def _extract_many(
    paths: Iterable[Path],
    eye: str,
    template_path: Path,
    strict: bool,
) -> dict[str, object]:
    results: dict[str, object] = {}
    for path in paths:
        results[str(path)] = _extract_path(path, eye, template_path, strict)
    return results


def _extract_csv_rows(
    paths: Iterable[Path],
    eye: str,
    template_path: Path,
    strict: bool,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.extend(_rows_from_extraction(path, _extract_path(path, eye, template_path, strict)))
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dumb text-block extractor for Humphrey Visual Field PDFs."
    )
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        default=DEFAULT_INPUT_PATH,
        help="PDF file or directory containing PDF files.",
    )
    parser.add_argument(
        "--eye",
        choices=["RE", "LE", "BOTH"],
        default="BOTH",
        help="Eye template to apply. Defaults to BOTH.",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=DEFAULT_TEMPLATE_PATH,
        help=f"Template JSON path. Defaults to {DEFAULT_TEMPLATE_PATH}.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Write CSV to this file instead of stdout.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit legacy JSON instead of CSV.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if expected map or GHT/VFI values are missing.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    paths = _pdf_inputs(args.input)
    if not paths:
        parser.error(f"No PDF files found in directory: {args.input}")

    try:
        if args.json:
            if len(paths) == 1 and args.input.is_file():
                data = _extract_path(paths[0], args.eye, args.template, args.strict)
            else:
                data = _extract_many(paths, args.eye, args.template, args.strict)
            _write_json(data, args.output)
        else:
            rows = _extract_csv_rows(paths, args.eye, args.template, args.strict)
            _write_csv(rows, _csv_fieldnames(args.template), args.output)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
