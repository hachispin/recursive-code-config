"""Add pixel-equivalent line gap to generated desktop fonts.

Font metrics are stored in units, not pixels. The conversion therefore needs
the intended point size and logical DPI. This module is also importable by the
main Recursive Code Config build.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from fontTools.ttLib import TTFont


def pixels_to_font_units(
    units_per_em: int, extra_pixels: float, font_size: float, dpi: float
) -> int:
    if extra_pixels < 0:
        raise ValueError("extra_pixels must be zero or greater")
    if font_size <= 0:
        raise ValueError("font_size must be greater than zero")
    if dpi <= 0:
        raise ValueError("dpi must be greater than zero")

    pixels_per_em = font_size * dpi / 72
    return round(extra_pixels * units_per_em / pixels_per_em)


def adjust_line_height(
    font_path: str | Path,
    *,
    extra_pixels: float,
    font_size: float,
    dpi: float = 96,
    output_path: str | Path | None = None,
) -> int:
    """Add line gap and return the number of font units added."""
    source = Path(font_path)
    target = Path(output_path) if output_path else source
    font = TTFont(source, recalcTimestamp=True)

    try:
        extra_units = pixels_to_font_units(
            font["head"].unitsPerEm, extra_pixels, font_size, dpi
        )
        font["hhea"].lineGap += extra_units
        font["OS/2"].sTypoLineGap += extra_units
        target.parent.mkdir(parents=True, exist_ok=True)
        font.save(target)
    finally:
        font.close()

    return extra_units


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fonts", nargs="+", type=Path, help="TTF files to adjust")
    parser.add_argument("--pixels", type=float, default=1)
    parser.add_argument("--font-size", type=float, required=True, help="Target size in pt")
    parser.add_argument("--dpi", type=float, default=96, help="Logical DPI")
    output = parser.add_mutually_exclusive_group(required=True)
    output.add_argument("--in-place", action="store_true")
    output.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for source in args.fonts:
        target = source if args.in_place else args.output_dir / source.name
        extra_units = adjust_line_height(
            source,
            extra_pixels=args.pixels,
            font_size=args.font_size,
            dpi=args.dpi,
            output_path=target,
        )
        print(f"{target}: added {extra_units} units of line gap")


if __name__ == "__main__":
    main()
