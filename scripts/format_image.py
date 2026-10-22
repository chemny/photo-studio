#!/usr/bin/env python3
import argparse
from io import BytesIO
import os
from pathlib import Path
import tempfile

from PIL import Image, ImageColor, ImageOps


FORMATS = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".tif": "TIFF",
    ".tiff": "TIFF",
    ".webp": "WEBP",
}


def parse_color(value: str, alpha: int = 255):
    rgb = ImageColor.getrgb(value)
    return (*rgb, alpha)


def target_size(args, parser):
    pixel_values = (args.width, args.height)
    mm_values = (args.width_mm, args.height_mm)
    if any(v is not None for v in pixel_values) and not all(v is not None for v in pixel_values):
        parser.error("--width and --height must be used together")
    if any(v is not None for v in mm_values) and not all(v is not None for v in mm_values):
        parser.error("--width-mm and --height-mm must be used together")
    if all(v is not None for v in pixel_values) and all(v is not None for v in mm_values):
        parser.error("choose pixel dimensions or millimetres, not both")
    if all(v is not None for v in pixel_values):
        if args.width < 1 or args.height < 1:
            parser.error("pixel dimensions must be positive")
        return args.width, args.height
    if all(v is not None for v in mm_values):
        if args.width_mm <= 0 or args.height_mm <= 0 or args.dpi < 1:
            parser.error("millimetres and DPI must be positive")
        return round(args.width_mm / 25.4 * args.dpi), round(args.height_mm / 25.4 * args.dpi)
    return None


def resize(image, size, fit, background):
    if not size:
        return image
    if fit == "crop":
        return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS)
    contained = ImageOps.contain(image, size, method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, background)
    x = (size[0] - contained.width) // 2
    y = (size[1] - contained.height) // 2
    if contained.mode == "RGBA":
        canvas.alpha_composite(contained, (x, y))
    else:
        canvas.paste(contained, (x, y))
    return canvas


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert studio finals to exact dimensions and file formats.")
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--width-mm", type=float)
    parser.add_argument("--height-mm", type=float)
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--fit", choices=["crop", "contain"], default="crop")
    parser.add_argument("--background", default="#FFFFFF")
    parser.add_argument("--quality", type=int, default=95)
    parser.add_argument("--crop-box", nargs=4, type=int, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
                        help="Explicit source crop after EXIF orientation, before proportional resizing")
    parser.add_argument("--max-bytes", type=int, help="Fail if the encoded file exceeds this byte limit")
    parser.add_argument("--min-quality", type=int, default=75, help="JPEG compression floor when --max-bytes is set")
    args = parser.parse_args()

    if not 1 <= args.quality <= 100:
        parser.error("--quality must be between 1 and 100")
    if args.dpi < 1:
        parser.error("--dpi must be positive")
    if not 1 <= args.min_quality <= 100:
        parser.error("--min-quality must be between 1 and 100")
    if args.max_bytes is not None and args.max_bytes < 1:
        parser.error("--max-bytes must be positive")
    size = target_size(args, parser)
    source = Path(args.input).resolve()
    output = Path(args.output).resolve()
    if source == output:
        parser.error("input and output must be different files")
    output_format = FORMATS.get(output.suffix.lower())
    if not output_format:
        parser.error("output extension must be JPG, PNG, TIFF, or WEBP")
    if args.max_bytes and output_format == "JPEG" and args.min_quality > args.quality:
        parser.error("--min-quality must not exceed --quality for bounded JPEG export")

    background = parse_color(args.background)
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGBA")
    if args.crop_box:
        left, top, right, bottom = args.crop_box
        if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
            parser.error("--crop-box must have positive area entirely within the oriented source")
        image = image.crop((left, top, right, bottom))
    image = resize(image, size, args.fit, background)

    if output_format == "JPEG":
        flattened = Image.new("RGB", image.size, background[:3])
        flattened.paste(image, mask=image.getchannel("A"))
        image = flattened
    elif output_format in {"TIFF", "WEBP"} and image.getchannel("A").getextrema() == (255, 255):
        image = image.convert("RGB")

    save_options = {"dpi": (args.dpi, args.dpi)}
    if output_format == "JPEG":
        save_options.update(quality=args.quality, optimize=True)
    elif output_format == "PNG":
        save_options.update(optimize=True)
    elif output_format == "TIFF":
        save_options.update(compression="tiff_lzw")
    elif output_format == "WEBP":
        save_options.update(quality=args.quality, method=6)
    qualities = range(args.quality, args.min_quality - 1, -1) if args.max_bytes and output_format == "JPEG" else [args.quality]
    for quality in qualities:
        if output_format == "JPEG":
            save_options["quality"] = quality
        buffer = BytesIO()
        image.save(buffer, format=output_format, **save_options)
        encoded = buffer.getvalue()
        if args.max_bytes is None or len(encoded) <= args.max_bytes:
            break
    else:
        parser.error(f"cannot meet {args.max_bytes}-byte limit at JPEG quality >= {args.min_quality}; dimensions were not reduced")
    if args.max_bytes is not None and len(encoded) > args.max_bytes:
        parser.error(f"encoded {output_format} is {len(encoded)} bytes, above {args.max_bytes}; output was not written")

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix=".photo-export-", delete=False) as staged:
            temporary = Path(staged.name)
            staged.write(encoded)
        os.replace(temporary, output)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    print(f"{output}\t{image.width}x{image.height}\t{args.dpi}dpi\t{output_format}\t{len(encoded)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
