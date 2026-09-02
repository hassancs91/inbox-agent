# /// script
# requires-python = ">=3.11"
# dependencies = ["google-auth>=2.30", "google-auth-oauthlib>=1.2", "google-api-python-client>=2.150"]
# ///
"""Put the twelve sample emails into the connected Gmail account.

    uv run tools/seed_sample.py --dry-run     show what would be inserted
    uv run tools/seed_sample.py               insert them (INBOX, unread)

For a demo or test account, so the agent can be watched working on real Gmail without
anyone's private mail on screen. Do not run it on an inbox you care about: it adds
twelve emails you did not receive. It never sends anything; messages.insert places a
message in the mailbox the way an import does, with no recipient delivery.

There is no AI in this file.
"""

import argparse
import base64
import json
from email.message import EmailMessage
from email.utils import format_datetime
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "sample-inbox.json"


def to_mime(email: dict) -> str:
    msg = EmailMessage()
    msg["From"] = f'{email["from"]["name"]} <{email["from"]["email"]}>'
    msg["To"] = email["to"]
    msg["Subject"] = email["subject"]
    msg["Date"] = format_datetime(datetime.fromisoformat(email["date"].replace("Z", "+00:00")))
    msg["X-Inbox-Agent-Fixture"] = email["id"]
    msg.set_content(email["body"])
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")


def main() -> None:
    parser = argparse.ArgumentParser(description="Insert the sample inbox into the connected Gmail account.")
    parser.add_argument("--dry-run", action="store_true", help="print what would be inserted, insert nothing")
    args = parser.parse_args()

    emails = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if args.dry_run:
        for e in emails:
            print(f'{e["id"]}  {e["from"]["email"]:42}  {e["subject"]}')
        print(f"{len(emails)} emails would be inserted. Nothing was.")
        return

    from _gmail import service

    svc = service()
    stamp = lambda e: str(int(datetime.fromisoformat(e["date"].replace("Z", "+00:00")).timestamp() * 1000))
    for e in emails:
        body = {"raw": to_mime(e), "labelIds": ["INBOX", "UNREAD"], "internalDate": stamp(e)}
        svc.users().messages().insert(userId="me", body=body, internalDateSource="dateHeader").execute()
        print(f'inserted {e["id"]}  {e["subject"]}')
    print(f"{len(emails)} emails inserted. Run uv run tools/fetch.py to see them.")


if __name__ == "__main__":
    main()
