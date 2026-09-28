#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from pathlib import Path


STAGES = ["intent", "specification", "source", "quantity", "package", "proof-plan", "proof-selection", "final-render", "final-review", "packaging", "acceptance"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Record an explicit customer decision.")
    parser.add_argument("manifest")
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument("--decision", choices=["confirmed", "revise", "cancelled"], required=True)
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    path = Path(args.manifest).resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("confirmations", []).append({
        "stage": args.stage,
        "decision": args.decision,
        "note": args.note,
        "recorded_at": datetime.now().astimezone().isoformat(timespec="seconds")
    })
    data["status"] = f"{args.stage}-{args.decision}"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Recorded {args.stage}: {args.decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
