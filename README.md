# dumb-hvf-pdf

A deliberately simple extractor for Humphrey Visual Field PDF exports.

This is not OCR. It reads the text blocks already embedded in a standard HVF
PDF and maps those values onto the labels in `data/templates/HVF.json`.

## Install

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Usage

Run with the default folder structure:

```sh
python3 main.py
```

That reads every PDF under `data/input` and writes `data/output/output.csv`.

Extract one PDF. If the filename ends in `_LE.pdf` or `_RE.pdf`, the CLI uses
that eye template automatically:

```sh
python3 main.py data/input/001/001_HVF_LE.pdf
```

Extract one eye:

```sh
python3 main.py path/to/hvf.pdf --eye RE
python3 main.py path/to/hvf.pdf --eye LE
```

Write CSV to a file:

```sh
python3 main.py path/to/hvf.pdf --eye RE --output out/hvf.csv
```

Process every PDF under nested subject folders:

```sh
python3 main.py data/input --output out/batch.csv
```

Use `--strict` when you want parsing to fail if the expected map or GHT/VFI
field counts are missing. Without `--strict`, missing values are emitted as
empty strings where possible.

## Python API

```python
from pipeline import extract_pdf

data = extract_pdf("path/to/hvf.pdf", "RE")
```

## Output Shape

The command emits CSV by default. Each row is one source PDF plus one eye, with
the first columns identifying the row:

```csv
subject_id,source_file,eye,header_Fixation Monitor,header_Fixation Target,...
001,data/input/001/001_HVF_RE.pdf,RE,...,...
```

Use `--json` to emit the internal JSON extraction shape for debugging.

## Build An App

Build a command-line-only PyInstaller distribution:

```sh
python3 -m pip install -r requirements.txt
python3 build.py
```

The generated layout is:

```text
dist/
  app.sh
  app.bat
  dumb-hvf-pdf
  input/
  output/
```

Put PDFs under `dist/input`, preserving nested subject folders such as
`dist/input/001/001_HVF_LE.pdf`, then run:

```sh
./dist/app.sh
```

The CSV is written to `dist/output/output.csv`.

## Limitations

- Only the first page is parsed.
- The parser assumes the PDF text block order used by the bundled HVF template.
- Scanned/image-only PDFs need a real OCR pipeline before this tool can read
  them.
