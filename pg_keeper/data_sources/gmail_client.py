"""Gmail fetching helpers.

This module keeps external imports optional so tests can run without the
Google client libraries installed.
"""
from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from datetime import datetime
from typing import List

from pg_keeper.config import GoogleAuthConfig
from pg_keeper.models import Document, SourceType


@dataclass
class GmailClient:
    """Minimal Gmail fetcher using the Gmail API.

    The implementation intentionally avoids importing the Google client
    libraries until runtime so environments without them can still load the
    module.
    """

    config: GoogleAuthConfig

    def _ensure_google_dependencies(self) -> None:
        missing = []
        for module_name in [
            "google.oauth2.credentials",
            "googleapiclient.discovery",
        ]:
            if importlib.util.find_spec(module_name) is None:
                missing.append(module_name)
        if missing:
            joined = ", ".join(missing)
            raise ImportError(
                f"Missing Google client libraries ({joined}). Install "
                "google-api-python-client and google-auth-httplib2 to enable Gmail sync."
            )

    def fetch_recent_messages(self, limit: int = 25) -> List[Document]:
        """Fetch recent messages and normalize them as Documents.

        Notes
        -----
        The method will raise an ImportError if the required Google libraries
        are not available. When `dry_run` is desired, call this with a mocked
        service or avoid invoking it.
        """

        self._ensure_google_dependencies()

        from google.oauth2.credentials import Credentials  # type: ignore
        from googleapiclient.discovery import build  # type: ignore

        credentials = Credentials.from_authorized_user_file(
            str(self.config.token_file or self.config.credentials_file),
            scopes=self.config.scopes,
        )
        service = build("gmail", "v1", credentials=credentials)
        response = (
            service.users()
            .messages()
            .list(userId="me", maxResults=limit, q="in:inbox")
            .execute()
        )
        messages = response.get("messages", [])

        documents: List[Document] = []
        for message in messages:
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=message["id"], format="metadata")
                .execute()
            )
            headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
            subject = headers.get("subject", "No Subject")
            date = headers.get("date")
            created_at = datetime.fromtimestamp(0)
            if date:
                try:
                    created_at = datetime.strptime(date[:25], "%a, %d %b %Y %H:%M:%S")
                except ValueError:
                    created_at = datetime.fromtimestamp(0)
            snippet = msg.get("snippet", "")
            documents.append(
                Document(
                    identifier=message["id"],
                    title=subject,
                    source=SourceType.GMAIL,
                    content=snippet,
                    created_at=created_at,
                    metadata={"from": headers.get("from", ""), "threadId": msg.get("threadId", "")},
                )
            )
        return documents
