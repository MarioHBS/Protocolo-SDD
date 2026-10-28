"""Locator for the bundled content pack (the .sdd payload + shims)."""
from pathlib import Path

CONTENT_DIR = Path(__file__).parent
KIT_VERSION = (CONTENT_DIR / "VERSION").read_text(encoding="utf-8").strip()

# Single source for the command name the CLI is invoked as. `sdd` is the
# previous name: still installed as an alias that warns on stderr (kit 4.5.0),
# to be removed in v5.
CLI_NAME = "sddkit"
LEGACY_CLI_NAME = "sdd"
