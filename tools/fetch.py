# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Fetch the inbox into work/inbox.json.

The first tool of the inbox agent. One job: get the emails and save them to a file.
There is no AI in this file. Nothing here decides what an email means.

    uv run tools/fetch.py --sample     read fixtures/sample-inbox.json, no Gmail needed
    uv run tools/fetch.py              read your Gmail (lecture 3 connects it)
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "sample-inbox.json"
OUT = ROOT / "work" / "inbox.json"


def fetch_sample() -> list[dict]:
    """The twelve emails that ship with this folder."""
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def fetch_gmail() -> list[dict]:
    """Not connected yet. Lecture 3 replaces this."""
    print("Gmail is not connected yet.", file=sys.stderr)
    print("Run /connect-gmail first (lecture 3), or use --sample to work on the sample inbox.", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch the inbox into work/inbox.json.")
    parser.add_argument("--sample", action="store_true", help="read the sample inbox instead of Gmail")
    args = parser.parse_args()

    emails = fetch_sample() if args.sample else fetch_gmail()

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(emails, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(emails)} emails written to {OUT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
