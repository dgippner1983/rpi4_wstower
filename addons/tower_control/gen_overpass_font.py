# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025-2026 David Gippner <david@gippner.eu>
# Parts of this software were developed with the assistance of
# Claude (claude.ai), an AI assistant by Anthropic.
#!/usr/bin/env python3
"""
gen_overpass_font.py
Generates overpass_font.h for use with tower_oledctl.c.

Produces three font instances on a 128x64 SSD1306 OLED:
  font_large  – single-line mode  (tower_oledctl text  "…")
  font_medium – two-line mode     (tower_oledctl text2 "…" "…")
  font_small  – three-line mode   (tower_oledctl text3 "…" "…" "…")

Usage:
  python3 gen_overpass_font.py \
      --font /tmp/overpass/fonts/ttf/Overpass-SemiBold.ttf \
      --output /tmp/overpass_font.h
"""

import argparse
import sys
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Characters to include
# ASCII printable + German umlauts/ß
# ---------------------------------------------------------------------------
CODEPOINTS = list(range(32, 127)) + [ord(c) for c in "äöüÄÖÜß°"]

# ---------------------------------------------------------------------------
# Font sizes  (name must match usage in tower_oledctl.c)
# ---------------------------------------------------------------------------
FONT_SIZES = [
    ("font_large",  32),   # 1 line  – ~32 px fits nicely in 64 px
    ("font_medium", 18),   # 2 lines – ~18 px × 2 = 36 px, centred
    ("font_small",  13),   # 3 lines – ~13 px × 3 = 39 px, centred
]


def render_glyphs(font_path: str, size: int) -> dict:
    """Render every glyph and return metrics + packed 1-bpp bitmap."""
    pil_font = ImageFont.truetype(font_path, size)
    ascent, descent = pil_font.getmetrics()
    line_height = ascent + descent

    glyphs = []
    bitmap = bytearray()

    for cp in CODEPOINTS:
        char = chr(cp)

        # Space and other non-rendering chars: width-only placeholder
        if cp == 32:
            adv = size // 3
            glyphs.append(dict(cp=cp, width=adv, height=0,
                               xoff=0, yoff=0, data_offset=len(bitmap)))
            continue

        bbox = pil_font.getbbox(char)

        # Invisible / zero-size glyphs
        if bbox is None or bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
            adv = size // 3
            glyphs.append(dict(cp=cp, width=adv, height=0,
                               xoff=0, yoff=0, data_offset=len(bitmap)))
            continue

        left, top, right, bottom = bbox
        gw = right - left    # bitmap width
        gh = bottom - top    # bitmap height

        # Render glyph into a grayscale image
        img = Image.new("L", (gw, gh), 0)
        draw = ImageDraw.Draw(img)
        draw.text((-left, -top), char, font=pil_font, fill=255)

        # Pack to 1 bpp, MSB first (matches tower_oledctl.c bit extraction)
        data_offset = len(bitmap)
        bpr = (gw + 7) // 8          # bytes per row
        pix = img.load()
        for row in range(gh):
            for bi in range(bpr):
                byte = 0
                for bit in range(8):
                    col = bi * 8 + bit
                    if col < gw and pix[col, row] > 127:
                        byte |= (1 << (7 - bit))
                bitmap.append(byte)

        glyphs.append(dict(
            cp=cp,
            width=gw,
            height=gh,
            xoff=left,        # horizontal bearing (can be negative)
            yoff=ascent - top,        # rows from bitmap top to baseline (positive = above)
            data_offset=data_offset,
        ))

    return dict(
        ascent=ascent,
        descent=descent,
        line_height=line_height,
        glyphs=glyphs,
        bitmap=bitmap,
    )


def emit_font(fp, font_name: str, data: dict) -> None:
    """Write one complete font (codepoints, glyphs, bitmap, struct) to fp."""
    glyphs = data["glyphs"]
    bitmap = data["bitmap"]
    n = len(glyphs)
    blen = len(bitmap)

    # --- codepoints array ---------------------------------------------------
    fp.write(f"static const uint32_t {font_name}_codepoints[{n}] = {{\n")
    row = []
    for i, g in enumerate(glyphs):
        row.append(f"0x{g['cp']:04X}")
        if len(row) == 16 or i == n - 1:
            sep = "," if i < n - 1 else ""
            fp.write("    " + ", ".join(row) + sep + "\n")
            row = []
    fp.write("};\n\n")

    # --- glyphs array -------------------------------------------------------
    fp.write(f"static const overpass_glyph_t {font_name}_glyphs[{n}] = {{\n")
    for g in glyphs:
        fp.write(
            f"    {{{g['width']}, {g['height']}, "
            f"{g['xoff']}, {g['yoff']}, {g['data_offset']}}},\n"
        )
    fp.write("};\n\n")

    # --- bitmap array -------------------------------------------------------
    fp.write(f"static const uint8_t {font_name}_bitmap[{blen}] = {{\n")
    for i in range(0, blen, 16):
        chunk = bitmap[i : i + 16]
        fp.write("    " + ", ".join(f"0x{b:02X}" for b in chunk) + ",\n")
    fp.write("};\n\n")

    # --- font struct instance -----------------------------------------------
    fp.write(f"static const overpass_font_t {font_name} = {{\n")
    fp.write(f"    .glyph_count = {n},\n")
    fp.write(f"    .codepoints  = {font_name}_codepoints,\n")
    fp.write(f"    .glyphs      = {font_name}_glyphs,\n")
    fp.write(f"    .bitmap      = {font_name}_bitmap,\n")
    fp.write(f"    .ascent      = {data['ascent']},\n")
    fp.write(f"    .descent     = {data['descent']},\n")
    fp.write(f"    .line_height = {data['line_height']},\n")
    fp.write("};\n\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate overpass_font.h for tower_oledctl.c"
    )
    parser.add_argument("--font",   required=True, help="Path to .ttf file")
    parser.add_argument("--output", required=True, help="Output .h file path")
    args = parser.parse_args()

    with open(args.output, "w") as fp:
        fp.write("/* Auto-generated by gen_overpass_font.py — do not edit */\n")
        fp.write("#pragma once\n")
        fp.write("#include <stdint.h>\n\n")

        # Type definitions (must match tower_oledctl.c exactly)
        fp.write("typedef struct {\n")
        fp.write("    int width, height;\n")
        fp.write("    int xoff, yoff;\n")
        fp.write("    int data_offset;\n")
        fp.write("} overpass_glyph_t;\n\n")

        fp.write("typedef struct {\n")
        fp.write("    int glyph_count;\n")
        fp.write("    const uint32_t *codepoints;\n")
        fp.write("    const overpass_glyph_t *glyphs;\n")
        fp.write("    const uint8_t *bitmap;\n")
        fp.write("    int ascent, descent, line_height;\n")
        fp.write("} overpass_font_t;\n\n")

        for font_name, size in FONT_SIZES:
            print(f"  Rendering {font_name} at {size} px …", flush=True)
            data = render_glyphs(args.font, size)
            emit_font(fp, font_name, data)
            print(
                f"    → {len(data['glyphs'])} glyphs, "
                f"{len(data['bitmap'])} bytes bitmap, "
                f"ascent={data['ascent']} descent={data['descent']}"
            )

    print(f"\nWrote: {args.output}")


if __name__ == "__main__":
    main()
