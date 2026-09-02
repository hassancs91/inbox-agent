# /// script
# requires-python = ">=3.11"
# dependencies = ["google-auth>=2.30", "google-auth-oauthlib>=1.2", "google-api-python-client>=2.150"]
# ///
"""Connect this folder to your Gmail account, once.

    uv run tools/connect.py

Needs credentials.json in this folder: an OAuth client of type Desktop app, downloaded
from Google Cloud. Opens the browser on Google's consent screen, saves token.json, then
makes ONE harmless call (your address and message count) to prove the connection works.

No email is read here. There is no AI in this file.
"""

import json
import sys

from _gmail import CREDENTIALS, SCOPES, TOKEN, load_credentials


def fail(*lines: str, code: int = 2) -> None:
    for line in lines:
        print(line, file=sys.stderr)
    sys.exit(code)


def main() -> None:
    if not CREDENTIALS.exists():
        fail(
            "credentials.json not found in this folder.",
            "Create an OAuth client of type Desktop app in Google Cloud, download its JSON,",
            "and save it here as credentials.json. The four steps are in README.md under Connect Gmail.",
        )
    try:
        client = json.loads(CREDENTIALS.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        fail("credentials.json is not valid JSON. Download it again from Google Cloud.")
    if "installed" not in client:
        kind = "Web application" if "web" in client else "unknown"
        fail(
            f"credentials.json is a {kind} client. The agent needs an OAuth client of type Desktop app.",
            "Create one under Credentials in Google Cloud and download that JSON instead.",
        )

    creds = load_credentials()
    if creds is None:
        from google_auth_oauthlib.flow import InstalledAppFlow

        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS), SCOPES)
        creds = flow.run_local_server(port=0)  # the browser opens on Google's consent screen
        TOKEN.write_text(creds.to_json(), encoding="utf-8")
        print(f"token.json written to {TOKEN.name}")
    else:
        print("Already connected. Checking that it still works.")

    from googleapiclient.discovery import build

    svc = build("gmail", "v1", credentials=creds, cache_discovery=False)
    profile = svc.users().getProfile(userId="me").execute()
    print(f"Connected as {profile['emailAddress']} · {profile.get('messagesTotal', '?')} messages in the mailbox")
    print("Permission granted: gmail.modify. This agent uses it to read, label and draft. It cannot permanently delete.")


if __name__ == "__main__":
    main()
