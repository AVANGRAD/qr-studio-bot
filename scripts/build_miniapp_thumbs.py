from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.miniapp import THUMBS_DIR, catalog, thumb_bytes


def main() -> None:
    catalog_data = catalog()
    items: list[tuple[str, str]] = []
    for group in catalog_data["shapes"]:
        items.extend(("shape", item["key"]) for item in group["items"])
    for kind in ("modules", "eyes", "palettes", "presets"):
        items.extend((kind[:-1], item["key"]) for item in catalog_data[kind])
    for kind, key in items:
        path = THUMBS_DIR / kind / f"{key}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(thumb_bytes(kind, key))
    print(f"built {len(items)} thumbnails in {THUMBS_DIR}")


if __name__ == "__main__":
    main()
