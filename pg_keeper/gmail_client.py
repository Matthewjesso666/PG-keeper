"""Gmail client utilities for fetching WCB correspondence."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Iterable, List

# Google API imports are optional and will be loaded at runtime
from google.oauth2.credentials import Credentials  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from googleapiclient.errors import HttpError  # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from google.auth.transport.requests import Request  # type: ignore

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


@dataclass
class GmailMessage:
    id: str
    subject: str | None
    received_at: datetime
    body_text: str
    attachments: List[Path]


class GmailFetcher:
    def __init__(self, credentials_file: Path, token_file: Path | None = None):
        self.credentials_file = credentials_file
        self.token_file = token_file or credentials_file.parent / "gmail_token.json"
        self.service = self._build_service()

    def _build_service(self):
        creds: Credentials | None = None
        if self.token_file.exists():
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.token_file, "w", encoding="utf-8") as token:
                token.write(creds.to_json())
        return build("gmail", "v1", credentials=creds)

    def fetch_messages(self, query: str, limit: int = 25) -> Iterable[GmailMessage]:
        try:
            results = self.service.users().messages().list(userId="me", q=query, maxResults=limit).execute()
        except HttpError as e:
            raise RuntimeError(f"Gmail API error: {e}")

        messages = results.get("messages", [])
        for message in messages:
            msg = self.service.users().messages().get(userId="me", id=message["id"], format="raw").execute()
            payload = BytesParser(policy=policy.default).parsebytes(msg["raw"].encode("UTF-8"))
            subject = payload["subject"]
            received = payload["date"]
            received_at = datetime.strptime(received, "%a, %d %b %Y %H:%M:%S %z") if received else datetime.utcnow()
            body_text = payload.get_body(preferencelist=("plain", "html"))
            text = body_text.get_content() if body_text else ""

            attachments: List[Path] = []
            for part in payload.iter_attachments():
                filename = part.get_filename() or "attachment"
                data = part.get_payload(decode=True)
                target = Path(filename)
                target.write_bytes(data)
                attachments.append(target)

            yield GmailMessage(
                id=message["id"],
                subject=subject,
                received_at=received_at,
                body_text=text,
                attachments=attachments,
            )
