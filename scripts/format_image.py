#!/usr/bin/env python3
import argparse
from pathlib import Path

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
    args = parser.parse_args()

    if not 1 <= args.quality <= 100:
        parser.error("--quality must be between 1 and 100")
    size = target_size(args, parser)
    source = Path(args.input).resolve()
    output = Path(args.output).resolve()
    if source == output:
        parser.error("input and output must be different files")
    output_format = FORMATS.get(output.suffix.lower())
    if not output_format:
        parser.error("output extension must be JPG, PNG, TIFF, or WEBP")

    background = parse_color(args.background)
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGBA")
    image = resize(image, size, args.fit, background)

    if output_format == "JPEG":
        flattened = Image.new("RGB", image.size, background[:3])
        flattened.paste(image, mask=image.getchannel("A"))
        image = flattened
    elif output_format in {"TIFF", "WEBP"} and image.getchannel("A").getextrema() == (255, 255):
        image = image.convert("RGB")

    output.parent.mkdir(parents=True, exist_ok=True)
    save_options = {"dpi": (args.dpi, args.dpi)}
    if output_format == "JPEG":
        save_options.update(quality=args.quality, optimize=True)
    elif output_format == "PNG":
        save_options.update(optimize=True)
    elif output_format == "TIFF":
        save_options.update(compression="tiff_lzw")
    elif output_format == "WEBP":
        save_options.update(quality=args.quality, method=6)
    image.save(output, format=output_format, **save_options)
    print(f"{output}\t{image.width}x{image.height}\t{args.dpi}dpi\t{output_format}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
