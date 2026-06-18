from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"


APP_SH = """#!/usr/bin/env sh
set -eu
APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
"$APP_DIR/dumb-hvf-pdf" "$APP_DIR/input" --output "$APP_DIR/output/output.csv" "$@"
"""


APP_BAT = """@echo off
setlocal
set "APP_DIR=%~dp0"
"%APP_DIR%dumb-hvf-pdf.exe" "%APP_DIR%input" --output "%APP_DIR%output\\output.csv" %*
if errorlevel 1 exit /b %errorlevel%
"""


def _write_launchers() -> None:
    (DIST / "input").mkdir(parents=True, exist_ok=True)
    (DIST / "output").mkdir(parents=True, exist_ok=True)

    app_sh = DIST / "app.sh"
    app_sh.write_text(APP_SH, encoding="utf-8")
    app_sh.chmod(0o755)

    (DIST / "app.bat").write_text(APP_BAT, encoding="utf-8")


def main() -> int:
    env = os.environ.copy()
    env.setdefault("PYINSTALLER_CONFIG_DIR", str(ROOT / ".pyinstaller"))
    result = subprocess.call(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "dumb_hvf_pdf.spec",
        ],
        env=env,
    )
    if result != 0:
        return result

    _write_launchers()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
