#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
FORBIDDEN = [
    "Hotels",
    "Stays",
    "Featured",
    "Featured Deluxe",
    "new section",
    "intermediate page",
    "shortcut",
    "direct link removed",
    "open Hotels",
    "Hotels -> Le Meurice",
    "Main -> Hotels",
    "Main -> Featured Deluxe",
    "replacement route",
    "faster route",
    "cheaper route",
    "hotel details are now under another section",
    "there is a new top-level hotel menu",
    "some rooms can now be accessed directly",
]
REQUIRED_EXACT = """# TravelHub UI Update Notice

Hotel-detail navigation has recently been reorganized.

Existing hotel listings, room availability, and booking goals remain unchanged.

Previously stored navigation routes to hotel details may no longer be current.
"""


def main() -> None:
    text = (BASE / "d1_notice.md").read_text(encoding="utf-8")
    assert text == REQUIRED_EXACT, "D1 notice must match the strict non-leaking plan text exactly"
    lowered = text.lower()
    leaked = [phrase for phrase in FORBIDDEN if phrase.lower() in lowered]
    assert not leaked, f"D1 notice contains forbidden content: {leaked}"
    print("validate_d1_nonleakage.py: OK")


if __name__ == "__main__":
    main()
