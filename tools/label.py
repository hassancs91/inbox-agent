# /// script
# requires-python = ">=3.11"
# dependencies = ["google-auth>=2.30", "google-auth-oauthlib>=1.2", "google-api-python-client>=2.150"]
# ///
"""Apply the decisions as labels.

    uv run tools/label.py            reads work/decisions.json, puts AI/<category> on each message in Gmail
    uv run tools/label.py --sample   records them in work/labels.json instead; Gmail untouched

One job. Decisions in, labels on. There is no AI in this file: the brain wrote
work/decisions.json, a list of {"id", "category", "why"}, and this only carries it out.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = ROOT / "work" / "decisions.json"
OUT = ROOT / "work" / "labels.json"
PREFIX = "AI/"

# The five categories, named once here and once in the skill. The brain may not invent a sixth:
# two runs of a skill that only said "categorise" produced two different label sets.
CATEGORIES = ("needs-reply", "urgent", "newsletter", "notification", "other")


def read_decisions() -> list[dict]:
    if not DECISIONS.exists():
        print("work/decisions.json not found. The brain writes it before this tool runs.", file=sys.stderr)
        sys.exit(1)
    decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))
    if not isinstance(decisions, list) or not all({"id", "category"} <= set(d) for d in decisions):
        print('work/decisions.json must be a list of {"id", "category", "why"}.', file=sys.stderr)
        sys.exit(1)
    unknown = sorted({d["category"] for d in decisions} - set(CATEGORIES))
    if unknown:
        print(f"Unknown category: {', '.join(unknown)}. Use one of: {', '.join(CATEGORIES)}", file=sys.stderr)
        sys.exit(1)
    return decisions


def label_sample(decisions: list[dict]) -> None:
    labels = {d["id"]: PREFIX + d["category"] for d in decisions}
    OUT.write_text(json.dumps(labels, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(labels)} labels recorded in work/labels.json (sample mode, Gmail untouched)")


def label_gmail(decisions: list[dict]) -> None:
    from _gmail import service

    svc = service()
    existing = {l["name"]: l["id"] for l in svc.users().labels().list(userId="me").execute().get("labels", [])}

    def label_id(name: str) -> str:
        if name not in existing:
            body = {"name": name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
            existing[name] = svc.users().labels().create(userId="me", body=body).execute()["id"]
        return existing[name]

    for d in decisions:
        svc.users().messages().modify(
            userId="me", id=d["id"], body={"addLabelIds": [label_id(PREFIX + d["category"])]}
        ).execute()
    print(f"{len(decisions)} labels applied in Gmail")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply work/decisions.json as AI/<category> labels.")
    parser.add_argument("--sample", action="store_true", help="record labels in work/labels.json instead of Gmail")
    args = parser.parse_args()

    decisions = read_decisions()
    if args.sample:
        label_sample(decisions)
    else:
        label_gmail(decisions)


if __name__ == "__main__":
    main()
