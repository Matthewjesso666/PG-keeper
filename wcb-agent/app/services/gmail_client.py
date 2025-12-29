"""Gmail client for retrieving case-related correspondence."""
from __future__ import annotations

from typing import List, Sequence

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES: Sequence[str] = [
    "https://www.googleapis.com/auth/gmail.readonly",
]


class GmailClient:
    """Wrapper around the Gmail API for message retrieval."""

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ) -> None:
        self.credentials = Credentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )
        self.service = build("gmail", "v1", credentials=self.credentials)

    def fetch_recent_messages(self, query: str = "", max_results: int = 25) -> List[dict]:
        """Return a list of Gmail messages matching the search query."""

        results = (
            self.service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        message_ids = [m["id"] for m in results.get("messages", [])]
        messages = []
        for message_id in message_ids:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
            messages.append(message)
        return messages
