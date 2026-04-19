"""CLI module — exports the Click CLI group."""
from __future__ import annotations

import os
import sys

# Dynamically import the cli module (cli.py) using its file path to avoid
# the package/module name conflict (cli/ package vs cli.py module).
# We save and restore sys.path so that cli.py's sys.path.insert doesn't
# clobber the site-packages entries that were set up by the installer.
_orig_path = sys.path[:]
_cli_module_path = os.path.join(os.path.dirname(__file__), "..", "cli.py")
import importlib.util
_spec = importlib.util.spec_from_file_location("aft.cli_module", _cli_module_path)
_cli = importlib.util.module_from_spec(_spec)
try:
    _spec.loader.exec_module(_cli)
finally:
    sys.path[:] = _orig_path

cli = _cli.cli

def main():
    """Entry point for the aft CLI (console_scripts entry point)."""
    cli()

__all__ = ["cli", "main"]
