import base64
import datetime as dt
import json
from typing import Dict, Iterable, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class GmailClient:
    """Thin wrapper around the Gmail API for reading case-related messages."""

    def __init__(self, config: Dict):
        self.config = config
        self.scopes = config["google"]["scopes"]
        self.user = config["google"].get("user", "me")
        self.token_file = config["google"]["token_file"]
        self.client_secret_file = config["google"]["client_secret_file"]
        self._service = None

    def authenticate(self):
        if self._service:
            return self._service

        creds = None
        if self.token_file:
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
            except FileNotFoundError:
                creds = None

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_file, self.scopes)
            creds = flow.run_local_server(port=0)
            if self.token_file:
                with open(self.token_file, "w") as token:
                    token.write(creds.to_json())

        self._service = build("gmail", "v1", credentials=creds)
        return self._service

    def fetch_messages(
        self, query: Optional[str] = None, after: Optional[dt.datetime] = None
    ) -> List[Dict]:
        service = self.authenticate()
        query_string = query or self.config["gmail"].get("query")
        if after:
            query_string = f"{query_string} after:{after.strftime('%Y/%m/%d')}"

        results = (
            service.users()
            .messages()
            .list(userId=self.user, q=query_string, maxResults=100)
            .execute()
        )
        messages = results.get("messages", [])
        return [self._fetch_message_body(service, m["id"]) for m in messages]

    def _fetch_message_body(self, service, message_id: str) -> Dict:
        message = (
            service.users()
            .messages()
            .get(userId=self.user, id=message_id, format="full")
            .execute()
        )

        payload = message.get("payload", {})
        headers = payload.get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        date_header = next((h["value"] for h in headers if h["name"] == "Date"), "")
        date = self._parse_date(date_header) or dt.datetime.fromtimestamp(
            int(message.get("internalDate", "0")) / 1000
        )
        body_text = self._extract_body(payload)
        return {
            "id": message_id,
            "subject": subject,
            "date": date.isoformat(),
            "text": body_text,
            "source": "gmail",
            "raw": json.dumps(message),
        }

    def _extract_body(self, payload: Dict) -> str:
        if "parts" in payload:
            texts: List[str] = []
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")
                if mime_type == "text/plain":
                    data = part.get("body", {}).get("data")
                    if data:
                        texts.append(base64.urlsafe_b64decode(data).decode("utf-8"))
            joined = "\n".join(t.strip() for t in texts if t)
            if joined:
                return joined

        data = payload.get("body", {}).get("data")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8")
        return ""

    def _parse_date(self, value: str) -> Optional[dt.datetime]:
        try:
            return dt.datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %z")
        except Exception:
            return None
