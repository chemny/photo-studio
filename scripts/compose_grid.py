#!/usr/bin/env python3
"""Compose portrait previews without resizing or stretching their cells."""

import argparse
from pathlib import Path

from PIL import Image, ImageOps


LAYOUTS = {
    "3x3": (3, 3, 2, 3, 12, 18),
    "2x2": (2, 2, 3, 2, 18, 12),
    "3x2": (3, 2, 3, 2, 18, 16),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layout", choices=LAYOUTS, required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--panel-aspect-ratio", choices=["2:3", "3:2"],
                        help="Override the default panel ratio; use 3:2 for a nine-panel family layout")
    parser.add_argument("images", nargs="+", type=Path, help="Cell images in reading order")
    args = parser.parse_args()

    columns, rows, ratio_w, ratio_h, gap_x, gap_y = LAYOUTS[args.layout]
    if args.panel_aspect_ratio:
        ratio_w, ratio_h = map(int, args.panel_aspect_ratio.split(":"))
    if len(args.images) != columns * rows:
        parser.error(f"{args.layout} requires exactly {columns * rows} images")

    cells = []
    expected_size = None
    for path in args.images:
        with Image.open(path) as source:
            cell = ImageOps.exif_transpose(source).convert("RGB")
        width, height = cell.size
        if width * ratio_h != height * ratio_w:
            parser.error(f"{path}: expected {ratio_w}:{ratio_h}, got {width}x{height}")
        if expected_size is not None and cell.size != expected_size:
            parser.error(f"{path}: expected {expected_size[0]}x{expected_size[1]}, got {width}x{height}; no resizing is performed")
        expected_size = cell.size
        cells.append(cell)

    width, height = expected_size
    board = Image.new(
        "RGB",
        (columns * width + (columns - 1) * gap_x, rows * height + (rows - 1) * gap_y),
        "white",
    )
    for index, cell in enumerate(cells):
        x = (index % columns) * (width + gap_x)
        y = (index // columns) * (height + gap_y)
        board.paste(cell, (x, y))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    board.save(args.output)
    print(f"{args.output} ({board.width}x{board.height}; cells {width}x{height}, no resizing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
