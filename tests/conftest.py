"""Pytest configuration and shared fixtures.

Ensures the `functions` directory is on sys.path so imports like
`shared.blob_paths` and `fn_run_ocr` work when running tests from repo root.
"""
import sys
from pathlib import Path

# Add functions dir so "shared" and function packages (fn_ingest_blob, fn_run_ocr) resolve
ROOT = Path(__file__).resolve().parent.parent
FUNCTIONS_DIR = ROOT / "functions"
if str(FUNCTIONS_DIR) not in sys.path:
    sys.path.insert(0, str(FUNCTIONS_DIR))
