from __future__ import annotations

from qrstudio.eyes import eye_keys
from qrstudio.masks import SHAPES
from qrstudio.presets import PALETTES, get_preset
from qrstudio.shapes import MODULE_STYLES

SIZES = {512, 1024, 2048}


def sanitize_settings(payload: object) -> dict:
    if not isinstance(payload, dict):
        return {}
    result: dict = {}
    preset_key = payload.get("preset")
    if isinstance(preset_key, str) and preset_key:
        try:
            preset = get_preset(preset_key)
        except KeyError:
            preset = None
        if preset is not None:
            result.update(
                {
                    "shape": preset.shape,
                    "module_style": preset.module_style,
                    "eye_style": preset.eye_style,
                    "palette": preset.palette,
                }
            )
    shape = payload.get("shape")
    if isinstance(shape, str) and shape in SHAPES:
        result["shape"] = shape
    module = payload.get("module_style")
    if isinstance(module, str) and module in MODULE_STYLES:
        result["module_style"] = module
    eye = payload.get("eye_style")
    if isinstance(eye, str) and eye in eye_keys():
        result["eye_style"] = eye
    palette = payload.get("palette")
    if isinstance(palette, str) and palette in PALETTES:
        result["palette"] = palette
    try:
        size = int(payload.get("size", 0))
    except (TypeError, ValueError):
        size = 0
    if size in SIZES:
        result["size"] = size
    return result


def apply_settings(draft: object, payload: dict) -> bool:
    changed = False
    for key, value in sanitize_settings(payload).items():
        if getattr(draft, key, None) != value:
            setattr(draft, key, value)
            changed = True
    return changed
