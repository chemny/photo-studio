#!/usr/bin/env python3
import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a clean studio proof contact sheet.")
    parser.add_argument("input_dir")
    parser.add_argument("output")
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--cell-width", type=int, default=480)
    parser.add_argument("--cell-height", type=int, default=600)
    parser.add_argument("--fit", choices=["contain", "crop"], default="contain")
    parser.add_argument("--background", default="#f3f0ea")
    parser.add_argument("--title", default="选片合集")
    parser.add_argument("--watermark", default="选片小样")
    parser.add_argument("--show-labels", action="store_true", help="Show internal sequence and filename labels")
    args = parser.parse_args()

    if args.columns < 1 or args.cell_width < 100 or args.cell_height < 100:
        raise SystemExit("Invalid layout dimensions")

    source = Path(args.input_dir).resolve()
    output = Path(args.output).resolve()
    files = sorted(p for p in source.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSIONS and p.resolve() != output)
    if not files:
        raise SystemExit("No images found")

    font = ImageFont.load_default()
    label_height = 44 if args.show_labels else 0
    title_height = 64
    rows = math.ceil(len(files) / args.columns)
    sheet = Image.new("RGB", (args.columns * args.cell_width, title_height + rows * (args.cell_height + label_height)), args.background)
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 22), args.title, fill="#171717", font=font)

    for index, path in enumerate(files, start=1):
        row, column = divmod(index - 1, args.columns)
        cell_left = column * args.cell_width
        cell_top = title_height + row * (args.cell_height + label_height)
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            if args.fit == "crop":
                tile = ImageOps.fit(image, (args.cell_width, args.cell_height), method=Image.Resampling.LANCZOS)
            else:
                contained = ImageOps.contain(image, (args.cell_width, args.cell_height), method=Image.Resampling.LANCZOS)
                tile = Image.new("RGB", (args.cell_width, args.cell_height), args.background)
                tile.paste(contained, ((args.cell_width - contained.width) // 2, (args.cell_height - contained.height) // 2))
        sheet.paste(tile, (cell_left, cell_top))
        if args.show_labels:
            draw.rectangle((cell_left, cell_top + args.cell_height, cell_left + args.cell_width, cell_top + args.cell_height + label_height), fill="#ffffff")
            draw.text((cell_left + 12, cell_top + args.cell_height + 14), f"{index:02d}  {path.stem}", fill="#171717", font=font)
        if args.watermark:
            draw.rectangle((cell_left + 12, cell_top + 12, cell_left + 110, cell_top + 38), fill="#ffffff")
            draw.text((cell_left + 19, cell_top + 20), args.watermark, fill="#555555", font=font)

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=92)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
