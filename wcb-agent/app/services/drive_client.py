"""Google Drive client for fetching case documents."""
from __future__ import annotations

from typing import List, Sequence

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES: Sequence[str] = [
    "https://www.googleapis.com/auth/drive.readonly",
]


class DriveClient:
    """Wrapper around the Drive API for file retrieval."""

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
        self.service = build("drive", "v3", credentials=self.credentials)

    def list_case_files(self, folder_id: str) -> List[dict]:
        """Return metadata for files within a Drive folder."""

        query = f"'{folder_id}' in parents and trashed = false"
        response = self.service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        return response.get("files", [])

    def download_file(self, file_id: str) -> bytes:
        """Download file content by ID."""

        request = self.service.files().get_media(fileId=file_id)
        file_bytes = request.execute()
        return file_bytes
