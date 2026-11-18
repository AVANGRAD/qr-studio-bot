#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw

from qrstudio.emblems import emblem_image, emblem_keys
from qrstudio.eyes import eye_keys
from qrstudio.logo import font, prepare_logo
from qrstudio.masks import shape_keys
from qrstudio.presets import PRESETS, palette_keys
from qrstudio.render import RenderOptions, render
from qrstudio.shapes import MODULE_STYLES

DECODER = ROOT / "tests" / "js" / "decode.js"
OUT = Path("/tmp/qrcheck")
CONTENT = "https://example.com/qr-studio"


def test_logo() -> Path:
    path = OUT / "logo-source.png"
    if not path.exists():
        OUT.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGBA", (400, 400), "white")
        draw = ImageDraw.Draw(image)
        draw.ellipse((40, 40, 360, 360), fill=(220, 40, 60, 255))
        draw.text((120, 145), "Q", font=font(150), fill="white")
        image.convert("RGB").save(path, quality=95)
    return path


def test_photo() -> Image.Image:
    path = OUT / "photo-source.png"
    if not path.exists():
        OUT.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGB", (900, 1200), "#8fbf9f")
        draw = ImageDraw.Draw(image)
        draw.rectangle((80, 110, 820, 480), fill="#ef8fd0")
        draw.ellipse((260, 560, 620, 920), fill="#1d5a9f")
        image.save(path)
    return Image.open(path).convert("RGB")


def decode(path: Path) -> dict:
    output = subprocess.run(["node", str(DECODER), str(path)], capture_output=True, text=True, timeout=30, check=False)
    if output.returncode != 0:
        return {"ok": False, "error": output.stderr.strip()[:200]}
    try:
        return json.loads(output.stdout.strip() or "{}")
    except json.JSONDecodeError:
        return {"ok": False, "error": output.stdout[:200]}


def run(name: str, options: RenderOptions, size: int, folder: str) -> tuple[str, bool, str]:
    options = RenderOptions(**{**options.__dict__, "content": CONTENT, "size": size})
    result = render(options)
    path = OUT / folder / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    result.image.save(path)
    decoded = decode(path)
    ok = bool(decoded.get("ok")) and decoded.get("data") == CONTENT
    detail = "" if ok else decoded.get("error", "decode failed")
    if result.warnings:
        detail = (detail + " | " + "; ".join(result.warnings)).strip(" |")
    return name, ok, detail


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    logo = prepare_logo(test_logo())
    photo = test_photo()
    tests: list[tuple[str, RenderOptions, int, str]] = []

    for key in shape_keys():
        tests.append((f"shape_{key}", RenderOptions(content="", shape=key, module_style="dot", eye_style="circle", palette="blue"), 768, "shapes"))
    for key in MODULE_STYLES:
        tests.append((f"module_{key}", RenderOptions(content="", shape="square", module_style=key, eye_style="circle", palette="navy"), 512, "modules"))
    for key in eye_keys():
        tests.append((f"eye_{key}", RenderOptions(content="", shape="square", module_style="dot", eye_style=key, palette="purple"), 512, "eyes"))
    for key in palette_keys():
        tests.append((f"palette_{key}", RenderOptions(content="", shape="rounded", module_style="rounded", eye_style="rounded", palette=key), 512, "palettes"))
    for mode in ("plate", "knockout", "texture", "background", "corner"):
        tests.append((f"logo_{mode}", RenderOptions(content="", shape="cat", module_style="dot", eye_style="circle", palette="blue", logo=logo, logo_mode=mode), 768, "logos"))
    tests.append(("logo_monogram", RenderOptions(content="", shape="square", module_style="dot", eye_style="rounded", palette="mono", logo_mode="monogram", logo_text="AK"), 512, "logos"))
    for key in shape_keys():
        tests.append((f"silhouette_{key}", RenderOptions(content="", shape=key, silhouette=True, module_style="dot", eye_style="circle", palette="green"), 768, "silhouettes"))
    for key in shape_keys():
        tests.append((f"figure_{key}", RenderOptions(content="", shape=key, silhouette=True, module_style="dot", eye_style="circle", palette="blue"), 768, "figures"))
    for size in (512, 1024, 2048):
        tests.append((f"size_{size}", RenderOptions(content="", shape="rounded", module_style="dot", eye_style="circle", palette="red"), size, "sizes"))
    for size in (512, 768):
        tests.append((f"photo_{size}", RenderOptions(content="", photo=photo, module_style="dot", eye_style="circle", palette="blue"), size, "photos"))
    tests.append(("photo_logo", RenderOptions(content="", photo=photo, module_style="dot", eye_style="circle", palette="blue", logo=logo, logo_mode="plate"), 768, "photos"))
    for key, preset in PRESETS.items():
        tests.append((f"preset_{key}", RenderOptions(content="", shape=preset.shape, module_style=preset.module_style, eye_style=preset.eye_style, palette=preset.palette, silhouette=preset.shape != "square"), 768, "presets"))
    for key in emblem_keys():
        tests.append((f"emblem_{key}", RenderOptions(content="", shape="rounded", module_style="dot", eye_style="circle", palette="blue", logo=emblem_image(key, 512), logo_mode="badge"), 512, "emblems"))

    failures: list[tuple[str, str]] = []
    for name, options, size, folder in tests:
        label, ok, detail = run(name, options, size, folder)
        if not ok:
            failures.append((label, detail))
    total = len(tests)
    print(f"checked {total - len(failures)}/{total}")
    if failures:
        print("FAILURES:")
        for name, detail in failures:
            print(f"  {name}: {detail}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
