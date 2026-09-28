"""Locator for the bundled content pack (the .sdd payload + shims)."""
from pathlib import Path

CONTENT_DIR = Path(__file__).parent
KIT_VERSION = (CONTENT_DIR / "VERSION").read_text(encoding="utf-8").strip()
