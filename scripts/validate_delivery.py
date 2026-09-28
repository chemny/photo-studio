#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


REQUIRED_FOLDERS = [
    "00-封面", "01-证件照", "02-个人形象照", "03-婚纱照",
    "04-艺术写真", "05-表情包", "06-宠物写真", "07-高清成片", "08-选片合集"
]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a portrait-studio delivery collection.")
    parser.add_argument("job_dir")
    parser.add_argument("--stage", choices=["structure", "final"], default="final")
    args = parser.parse_args()

    root = Path(args.job_dir).resolve()
    errors = []
    manifest_path = root / "job-manifest.json"
    for folder in REQUIRED_FOLDERS:
        if not (root / folder).is_dir():
            errors.append(f"Missing folder: {folder}")
    if not manifest_path.is_file():
        errors.append("Missing job-manifest.json")
        manifest = {}
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Invalid manifest: {exc}")
            manifest = {}

    if args.stage == "final":
        finals = [p for p in (root / "07-高清成片").rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS] if (root / "07-高清成片").is_dir() else []
        sheets = [p for p in (root / "08-选片合集").rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS] if (root / "08-选片合集").is_dir() else []
        confirmed = {item.get("stage") for item in manifest.get("confirmations", []) if item.get("decision") == "confirmed"}
        final_quantity = manifest.get("final_quantity")
        proof_quantity = manifest.get("proof_quantity")
        production_mode = manifest.get("production_mode")
        if not isinstance(final_quantity, int) or final_quantity < 1:
            errors.append("Manifest has no valid final_quantity")
        elif len(finals) != final_quantity:
            errors.append(f"Final image count is {len(finals)}; expected {final_quantity}")
        if (not isinstance(proof_quantity, int) or proof_quantity < 1 or
                (isinstance(final_quantity, int) and proof_quantity < final_quantity)):
            errors.append("Manifest has no valid proof_quantity")
        if production_mode not in {"direct", "proof"}:
            errors.append("Manifest has no valid production_mode")
        elif production_mode == "direct" and proof_quantity != final_quantity:
            errors.append("Direct mode requires proof_quantity to equal final_quantity")
        if production_mode == "proof":
            if not sheets:
                errors.append("Proof mode requires a contact sheet in 08-选片合集")
            if "proof-selection" not in confirmed:
                errors.append("Proof mode requires a recorded proof-selection confirmation")

    result = {"ok": not errors, "job_dir": str(root), "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
