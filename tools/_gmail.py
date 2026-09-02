"""Shared: how the tools talk to Gmail. Not a tool; nothing runs this file directly.

One permission for the whole agent, chosen once:

    https://www.googleapis.com/auth/gmail.modify

Google's own wording for it on the consent screen: "Read, compose, and send emails from
your Gmail account". Yes, send is in there. Google has no scope for "draft but never
send". What keeps this agent from sending is that no tool in this folder sends. What the
scope cannot do, for anyone holding the token, is permanently delete mail: that needs the
full https://mail.google.com/ scope, which we never ask for.

There is no AI in this file.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CREDENTIALS = ROOT / "credentials.json"
TOKEN = ROOT / "token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

NOT_CONNECTED = (
    "Gmail is not connected yet.",
    "Run /connect-gmail first (lecture 3), or use --sample to work on the sample inbox.",
)


def load_credentials():
    """token.json -> Credentials, refreshed if needed. None if this folder is not connected."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    if not TOKEN.exists():
        return None
    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return creds if creds.valid else None


def service():
    """A Gmail API client, or a plain two-line refusal and exit 1."""
    creds = load_credentials()
    if creds is None:
        for line in NOT_CONNECTED:
            print(line, file=sys.stderr)
        sys.exit(1)
    from googleapiclient.discovery import build

    return build("gmail", "v1", credentials=creds, cache_discovery=False)
