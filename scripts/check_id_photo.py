#!/usr/bin/env python3
"""Check exported ID-file parameters; identity and full-background review stay visual."""

import argparse
from datetime import date
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageColor


REVIEW_CHECKS = ("source_suitability", "identity", "source_detail", "pose",
                 "entire_background_and_edges", "head_and_shoulders", "natural_proportions",
                 "hair_and_ears", "accessories", "attire", "makeup_and_eyes", "expression",
                 "purpose_geometry", "processing_allowed", "submission_channel")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review_errors(review, image, source, purpose, test_sample):
    """Validate recorded visual evidence, not the truth of its visual judgments."""
    errors = []
    if review.get("image_sha256") != digest(image):
        errors.append("review does not match the exact exported image")
    if review.get("source_sha256") != digest(source):
        errors.append("review does not match the source image")
    if review.get("method") not in {"assistant_visual", "human_visual"} or not review.get("reviewer"):
        errors.append("review must identify its visual method and reviewer")
    if review.get("source_kind") not in {"real_photo", "synthetic_test_source"}:
        errors.append("review must distinguish real photos from synthetic test sources")
    processing = review.get("processing")
    if processing not in {"unmodified_capture", "non_generative", "generative_test"}:
        errors.append("processing must be explicitly recorded")
    if not test_sample and (review.get("source_kind") != "real_photo" or processing == "generative_test"):
        errors.append("synthetic or generated images require --test-sample and cannot be submission-ready")
    profiles = json.loads((Path(__file__).resolve().parents[1] / "assets/id-photo-purpose-profiles.json").read_text())["profiles"]
    profile = profiles.get(purpose)
    if not profile or review.get("purpose_profile") != purpose:
        errors.append("a known --purpose must match the recorded purpose_profile")
    else:
        if not test_sample and not profile["submission_eligible"]:
            errors.append("generic styling/size samples are not eligible for official submission")
        if not test_sample and profile.get("requires_unmodified_capture") and processing != "unmodified_capture":
            errors.append("this paper-passport reference prohibits edited or composite captures")
        requirements = review.get("requirements", {})
        if not isinstance(requirements, dict):
            raise ValueError("requirements must be an object")
        if requirements.get("verified") is not True or not isinstance(requirements.get("scope"), str) or not requirements["scope"].strip():
            errors.append("purpose requirements must be verified with an explicit scope")
        try:
            checked_on = date.fromisoformat(requirements.get("checked_on", ""))
            if checked_on > date.today():
                raise ValueError("future verification date")
        except (ValueError, TypeError):
            errors.append("requirements need a valid non-future checked_on date")
        sources = requirements.get("official_sources", [])
        if purpose != "generic_sample" and (not isinstance(sources, list) or not sources or
                any(not isinstance(url, str) or not url.startswith("https://") for url in sources)):
            errors.append("official purpose requires recorded HTTPS source URLs")
        context = requirements.get("context", {})
        if not isinstance(context, dict):
            raise ValueError("requirements context must be an object")
        for key in profile["required_context"]:
            if not isinstance(context.get(key), str) or not context[key].strip():
                errors.append(f"missing purpose context: {key}")
    checks = review.get("checks", {})
    if not isinstance(checks, dict):
        raise ValueError("review checks must be an object")
    for key in REVIEW_CHECKS:
        check = checks.get(key)
        if not isinstance(check, dict) or check.get("status") != "pass" or not isinstance(check.get("note"), str) or not check["note"].strip():
            errors.append(f"visual review missing, failed or unexplained: {key}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--format", choices=["JPEG", "PNG", "TIFF", "WEBP"], default="JPEG")
    parser.add_argument("--max-bytes", type=int)
    parser.add_argument("--background", help="Expected corner color; not whole-background validation")
    parser.add_argument("--color-tolerance", type=int, default=12)
    parser.add_argument("--landmarks", type=Path, help="Manually observed normalized head landmarks, not detector output")
    parser.add_argument("--source", type=Path, help="Canonical source for exact-file visual review")
    parser.add_argument("--review", type=Path, help="Recorded visual review; does not perform face recognition")
    parser.add_argument("--require-review", action="store_true", help="Fail delivery unless exact-file visual review passes")
    parser.add_argument("--purpose", help="Purpose profile ID from assets/id-photo-purpose-profiles.json")
    parser.add_argument("--test-sample", action="store_true", help="Evaluate a labeled test sample; never mark it submission-ready")
    args = parser.parse_args()
    if min(args.width, args.height, args.dpi) < 1 or (args.max_bytes is not None and args.max_bytes < 1):
        parser.error("dimensions, DPI and any byte limit must be positive")
    if not 0 <= args.color_tolerance <= 255:
        parser.error("--color-tolerance must be in 0..255")
    errors = []
    result = {"image": str(args.image), "file_checks_passed": False,
              "visual_review_required": list(REVIEW_CHECKS),
              "delivery_ready": False, "visual_review_status": "not_reviewed",
              "test_sample_ready": False, "local_checks_passed": False,
              "purpose_profile": args.purpose,
              "official_acceptance": "not_evaluated", "errors": errors}
    try:
        with Image.open(args.image) as im:
            im.verify()
        with Image.open(args.image) as im:
            im.load()
            size = im.size
            dpi = im.info.get("dpi")
            mode = im.mode
            actual_format = im.format
            size_bytes = args.image.stat().st_size
            result.update(size=list(size), format=actual_format, mode=mode, dpi=dpi, size_bytes=size_bytes)
            if size != (args.width, args.height):
                errors.append("pixel dimensions do not match")
            if actual_format != args.format:
                errors.append("actual encoded format does not match")
            if not dpi or len(dpi) != 2 or any(not math.isfinite(float(v)) or abs(float(v) - args.dpi) > 1 for v in dpi):
                errors.append("DPI metadata missing or mismatched")
            if mode not in {"RGB", "RGBA"}:
                errors.append("expected RGB color space")
            if mode == "RGBA" and im.getchannel("A").getextrema() != (255, 255):
                errors.append("transparent pixels are not valid for an opaque ID file")
            if args.max_bytes is not None and size_bytes > args.max_bytes:
                errors.append("file exceeds byte limit")
            if args.background:
                expected = ImageColor.getrgb(args.background)
                rgb = im.convert("RGB")
                # Lower corners often contain shoulders. Sample only the upper corners,
                # and report subject/background ambiguity rather than claiming segmentation.
                points = [(x, y) for x0 in (0, max(0, size[0]-3))
                          for x in range(x0, min(x0+3, size[0])) for y in range(min(3, size[1]))]
                deviation = max(max(abs(a-b) for a, b in zip(rgb.getpixel(point), expected)) for point in points)
                result["corner_samples"] = {"max_channel_deviation": deviation, "passed": deviation <= args.color_tolerance,
                                            "coverage": "upper_corners_only"}
                if deviation > args.color_tolerance:
                    errors.append("corner colors differ from requested background; review composition/background")
        if args.landmarks:
            if args.purpose and args.purpose != "generic_sample":
                raise ValueError("generic landmarks cannot certify purpose-specific geometry; record purpose_geometry separately")
            observed = json.loads(args.landmarks.read_text(encoding="utf-8"))
            profile = json.loads((Path(__file__).resolve().parents[1] / "assets/id-photo-composition.json").read_text(encoding="utf-8"))
            values = {key: observed[key] for key, rule in profile["numeric_rules"].items() if rule["severity"] == "required"}
            if any(isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) or not 0 <= v <= 1 for v in values.values()):
                raise ValueError("landmarks must be finite normalized numbers in 0..1")
            for key, value in values.items():
                rule = profile["numeric_rules"][key]
                if not rule.get("min", 0) <= value <= rule.get("max", 1):
                    errors.append(f"supplied landmark outside generic range: {key}")
            if abs(values["head_top_y"] + values["head_height_ratio"] - values["chin_y"]) > profile["consistency"]["max_absolute_error"]:
                errors.append("supplied vertical landmarks are inconsistent")
            result["composition_observations"] = {"source": "supplied_manual_landmarks", "values": values,
                                                   "profile": profile["profile_id"], "face_detection_performed": False}
    except (OSError, ValueError, KeyError, TypeError, Image.DecompressionBombError) as exc:
        errors.append(str(exc))
    result["file_checks_passed"] = not errors
    review_problems = []
    review = None
    if args.review:
        try:
            if not args.source:
                raise ValueError("--source is required with --review")
            review = json.loads(args.review.read_text(encoding="utf-8"))
            if not isinstance(review, dict):
                raise ValueError("review must be an object")
            review_problems = review_errors(review, args.image, args.source, args.purpose, args.test_sample)
            result["visual_review_status"] = "failed" if review_problems else "recorded_pass"
            result["review_validation_scope"] = "record completeness and file hashes only; visual judgments are supplied"
        except (OSError, ValueError, TypeError, KeyError) as exc:
            review_problems.append(str(exc))
            result["visual_review_status"] = "invalid"
    elif args.require_review:
        review_problems.append("exact-file visual review is required before delivery")
    result["review_errors"] = review_problems
    result["local_checks_passed"] = result["file_checks_passed"] and result["visual_review_status"] == "recorded_pass"
    result["test_sample_ready"] = result["local_checks_passed"] and args.test_sample
    result["delivery_ready"] = result["local_checks_passed"] and not args.test_sample
    result["evaluation_scope"] = "labeled_test_sample_only" if args.test_sample else "local_submission_checks_only"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors and not review_problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
