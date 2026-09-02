# /// script
# requires-python = ">=3.11"
# dependencies = ["google-auth>=2.30", "google-auth-oauthlib>=1.2", "google-api-python-client>=2.150"]
# ///
"""Fetch the inbox into work/inbox.json.

The first tool of the inbox agent. One job: get the emails and save them to a file.
There is no AI in this file. Nothing here decides what an email means.

    uv run tools/fetch.py              read your Gmail inbox (after /connect-gmail)
    uv run tools/fetch.py --sample     read fixtures/sample-inbox.json, no Gmail needed
    uv run tools/fetch.py --max 50     how many of the newest inbox messages to read (default 20)

Every email comes out in the same shape, whichever source it came from:
    id, threadId, date, from {name, email}, to, subject, body, labels
"""

import argparse
import base64
import html
import json
import re
from datetime import datetime, timezone
from email.utils import parseaddr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "sample-inbox.json"
OUT = ROOT / "work" / "inbox.json"
BODY_LIMIT = 4000  # characters; enough to understand an email, not enough to drown the brain


def fetch_sample() -> list[dict]:
    """The twelve emails that ship with this folder."""
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def fetch_gmail(limit: int) -> list[dict]:
    """The newest messages in the INBOX, each fetched in full and reshaped."""
    from _gmail import service

    svc = service()
    listing = svc.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=limit).execute()
    emails = []
    for ref in listing.get("messages", []):
        msg = svc.users().messages().get(userId="me", id=ref["id"], format="full").execute()
        emails.append(shape(msg))
    return emails


def shape(msg: dict) -> dict:
    """A Gmail API message -> the one shape every tool in this folder understands."""
    headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
    name, addr = parseaddr(headers.get("from", ""))
    stamp = int(msg.get("internalDate", 0)) / 1000
    return {
        "id": msg["id"],
        "threadId": msg["threadId"],
        "date": datetime.fromtimestamp(stamp, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
        "from": {"name": name or addr, "email": addr},
        "to": headers.get("to", ""),
        "subject": headers.get("subject", "(no subject)"),
        "body": body_text(msg["payload"]) or msg.get("snippet", ""),
        "labels": msg.get("labelIds", []),
    }


def body_text(payload: dict) -> str:
    """The plain-text body. Walks multipart messages; strips HTML only when there is no plain part."""
    plain: list[str] = []
    rich: list[str] = []

    def walk(part: dict) -> None:
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data")
        if mime == "text/plain" and data:
            plain.append(decode(data))
        elif mime == "text/html" and data:
            rich.append(decode(data))
        for sub in part.get("parts", []):
            walk(sub)

    walk(payload)
    text = "\n".join(plain) if plain else strip_html("\n".join(rich))
    return text.strip()[:BODY_LIMIT]


def decode(data: str) -> str:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")


def strip_html(markup: str) -> str:
    text = re.sub(r"<(script|style).*?</\1>", " ", markup, flags=re.S | re.I)
    text = re.sub(r"<br\s*/?>|</p>|</div>|</tr>|</li>|</h[1-6]>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\r]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n\n", text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch the inbox into work/inbox.json.")
    parser.add_argument("--sample", action="store_true", help="read the sample inbox instead of Gmail")
    parser.add_argument("--max", type=int, default=20, help="newest inbox messages to read from Gmail (default 20)")
    args = parser.parse_args()

    emails = fetch_sample() if args.sample else fetch_gmail(args.max)

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(emails, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(emails)} emails written to {OUT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
