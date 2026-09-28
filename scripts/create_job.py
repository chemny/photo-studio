#!/usr/bin/env python3
import argparse
import json
import re
from datetime import datetime
from pathlib import Path


FOLDERS = [
    "00-封面", "01-证件照", "02-个人形象照", "03-婚纱照",
    "04-艺术写真", "05-表情包", "06-宠物写真", "07-高清成片", "08-选片合集"
]


def safe_name(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", value).strip(" .")
    return value or "未命名客户"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a confirmed portrait-studio job folder.")
    parser.add_argument("--root", required=True, help="Parent delivery directory")
    parser.add_argument("--client", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--subject", choices=["person", "couple", "family", "child", "pet"], required=True)
    parser.add_argument("--final-quantity", type=int, required=True)
    parser.add_argument("--production-mode", choices=["direct", "proof"], default="direct")
    parser.add_argument("--proof-quantity", type=int)
    parser.add_argument("--spec-file", help="UTF-8 JSON file containing the confirmed production specification")
    parser.add_argument("--date", default=datetime.now().strftime("%Y%m%d"))
    args = parser.parse_args()

    if args.final_quantity < 1:
        parser.error("--final-quantity must be at least 1")
    if args.proof_quantity is None:
        args.proof_quantity = args.final_quantity
    if args.proof_quantity < args.final_quantity:
        parser.error("--proof-quantity must be greater than or equal to --final-quantity")
    if args.production_mode == "direct" and args.proof_quantity != args.final_quantity:
        parser.error("direct mode requires --proof-quantity to equal --final-quantity")

    specification = {}
    if args.spec_file:
        try:
            specification = json.loads(Path(args.spec_file).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            parser.error(f"invalid --spec-file: {exc}")
        if not isinstance(specification, dict):
            parser.error("--spec-file must contain a JSON object")

    job_name = safe_name(f"{args.client}-{args.date}-{args.package}")
    job_dir = Path(args.root).expanduser().resolve() / job_name
    job_dir.mkdir(parents=True, exist_ok=False)
    for folder in FOLDERS:
        (job_dir / folder).mkdir()

    manifest = {
        "schema_version": 1,
        "client": args.client,
        "subject": args.subject,
        "package": args.package,
        "production_mode": args.production_mode,
        "final_quantity": args.final_quantity,
        "proof_quantity": args.proof_quantity,
        "specification": specification,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "package-confirmed",
        "confirmations": [],
        "files": []
    }
    (job_dir / "job-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(job_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
