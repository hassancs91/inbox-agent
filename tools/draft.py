# /// script
# requires-python = ">=3.11"
# dependencies = ["google-auth>=2.30", "google-auth-oauthlib>=1.2", "google-api-python-client>=2.150"]
# ///
"""Create a Gmail draft for each reply the brain wrote.

    uv run tools/draft.py            reads work/drafts.json, creates one draft per reply in Gmail,
                                     inside the thread of the email it answers
    uv run tools/draft.py --sample   records them in work/drafts-created.json instead; Gmail untouched

One job. Replies in, drafts out. There is no AI in this file: the brain wrote
work/drafts.json, a list of {"id", "body", "fill_in"}, and this only carries it out.

Each draft lands in the thread under the email it answers, addressed to whoever wrote
that email, waiting for you. Who it goes to, the subject and the thread all come from the
original message, never from the brain. This file creates drafts and does nothing else
with mail: there is no call in it that moves a message out of Drafts.

A thread that already holds a draft is left alone, yours or last run's. This tool adds;
it never replaces.
"""

import argparse
import base64
import json
import re
import sys
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ROOT / "work" / "drafts.json"
INBOX = ROOT / "work" / "inbox.json"
OUT = ROOT / "work" / "drafts-created.json"

# A draft with a hole in it is not a draft. The brain checks for these before it saves;
# this is the second look, with no judgement in it: brackets, braces, blanks, the usual marks.
PLACEHOLDER = re.compile(r"\[[^\]\n]*\]|\{\{|\bTODO\b|\bTBD\b|\bXXX\b|_{3,}|<insert\b", re.I)


def fail(*lines: str) -> None:
    for line in lines:
        print(line, file=sys.stderr)
    sys.exit(1)


def read_drafts() -> list[dict]:
    if not DRAFTS.exists():
        fail("work/drafts.json not found. The brain writes it before this tool runs.")
    drafts = json.loads(DRAFTS.read_text(encoding="utf-8"))
    if not isinstance(drafts, list) or not all({"id", "body"} <= set(d) for d in drafts):
        fail('work/drafts.json must be a list of {"id", "body", "fill_in"}.')
    for d in drafts:
        if not isinstance(d["body"], str) or not d["body"].strip():
            fail(f'Draft for {d["id"]} has an empty body. Every draft is a whole reply.')
        hole = PLACEHOLDER.search(d["body"])
        if hole:
            fail(f'Draft for {d["id"]} still has placeholder text: {hole.group(0)!r}. Fix the draft, then run again.')
    return drafts


def reply_subject(subject: str) -> str:
    return subject if re.match(r"^\s*re\s*:", subject, re.I) else f"Re: {subject}"


def reply_raw(original: dict, body: str) -> str:
    """The reply as one RFC 2822 message, base64url as the Gmail API wants it."""
    msg = EmailMessage()
    msg["To"] = original["to"]
    msg["Subject"] = original["subject"]
    if original.get("message_id"):
        # These two headers are what makes every mail client, Gmail included, show the
        # draft under the message it answers instead of as a fresh email.
        msg["In-Reply-To"] = original["message_id"]
        msg["References"] = " ".join(filter(None, [original.get("references"), original["message_id"]]))
    msg.set_content(body, charset="utf-8", cte="quoted-printable")
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")


def originals_sample(ids: set[str]) -> dict[str, dict]:
    """What each reply answers, read from work/inbox.json."""
    if not INBOX.exists():
        fail("work/inbox.json not found. Run uv run tools/fetch.py --sample first.")
    emails = {e["id"]: e for e in json.loads(INBOX.read_text(encoding="utf-8"))}
    missing = sorted(ids - set(emails))
    if missing:
        fail(f"Not in work/inbox.json: {', '.join(missing)}. A draft answers an email that was fetched.")
    return {
        i: {
            "threadId": emails[i]["threadId"],
            "to": formataddr((emails[i]["from"]["name"], emails[i]["from"]["email"])),
            "subject": reply_subject(emails[i]["subject"]),
        }
        for i in ids
    }


def originals_gmail(svc, ids: set[str]) -> dict[str, dict]:
    """What each reply answers, read from Gmail: one metadata call per message, no body."""
    from googleapiclient.errors import HttpError

    wanted = ["Subject", "From", "Reply-To", "Message-ID", "References"]
    out = {}
    for i in ids:
        try:
            msg = svc.users().messages().get(userId="me", id=i, format="metadata", metadataHeaders=wanted).execute()
        except HttpError as err:
            if err.resp.status == 404:
                fail(f"Message {i} is not in Gmail any more. Run uv run tools/fetch.py again.")
            raise
        headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
        out[i] = {
            "threadId": msg["threadId"],
            "to": headers.get("reply-to") or headers.get("from", ""),
            "subject": reply_subject(headers.get("subject", "(no subject)")),
            "message_id": headers.get("message-id", ""),
            "references": headers.get("references", ""),
        }
    return out


def threads_with_a_draft(svc) -> set[str]:
    """Every thread that already holds a draft, so this run does not add a second one."""
    threads, token = set(), None
    while True:
        page = svc.users().drafts().list(userId="me", maxResults=500, pageToken=token).execute()
        threads |= {d["message"]["threadId"] for d in page.get("drafts", [])}
        token = page.get("nextPageToken")
        if not token:
            return threads


def draft_sample(drafts: list[dict]) -> None:
    originals = originals_sample({d["id"] for d in drafts})
    # Keyed by message id: one draft per email, so a rewritten draft replaces the old record.
    created = {d["id"]: {**originals[d["id"]], "body": d["body"]} for d in drafts}
    OUT.write_text(json.dumps(created, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(created)} drafts recorded in work/drafts-created.json (sample mode, Gmail untouched)")


def draft_gmail(drafts: list[dict]) -> None:
    from _gmail import service

    svc = service()
    originals = originals_gmail(svc, {d["id"] for d in drafts})
    taken = threads_with_a_draft(svc)
    created = skipped = 0
    for d in drafts:
        original = originals[d["id"]]
        if original["threadId"] in taken:
            skipped += 1
            continue
        body = {"message": {"threadId": original["threadId"], "raw": reply_raw(original, d["body"])}}
        svc.users().drafts().create(userId="me", body=body).execute()
        taken.add(original["threadId"])
        created += 1
    print(f"{created} drafts created in Gmail")
    if skipped:
        print(f"{skipped} left alone: the thread already has a draft")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Gmail draft, in its thread, for each reply in work/drafts.json.")
    parser.add_argument("--sample", action="store_true", help="record drafts in work/drafts-created.json instead of Gmail")
    args = parser.parse_args()

    drafts = read_drafts()
    if args.sample:
        draft_sample(drafts)
    else:
        draft_gmail(drafts)


if __name__ == "__main__":
    main()
