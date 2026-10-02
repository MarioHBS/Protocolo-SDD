"""Locator for the bundled content pack (the .sdd payload + shims)."""
from pathlib import Path

CONTENT_DIR = Path(__file__).parent
KIT_VERSION = (CONTENT_DIR / "VERSION").read_text(encoding="utf-8").strip()

# Single source for the command name the CLI is invoked as. Kept here, not
# hard-coded per call site, so a future rename (kit stage 4.5.0) only edits
# this one line -- `sdd` would then become a deprecated alias of the new name.
CLI_NAME = "sdd"
