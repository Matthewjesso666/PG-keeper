"""Google Drive client for pulling WCB-related files."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from google.oauth2.credentials import Credentials  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from googleapiclient.errors import HttpError  # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from google.auth.transport.requests import Request  # type: ignore

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


@dataclass
class DriveFile:
    id: str
    name: str
    mime_type: str
    path: Path


class DriveFetcher:
    def __init__(self, credentials_file: Path, token_file: Path | None = None):
        self.credentials_file = credentials_file
        self.token_file = token_file or credentials_file.parent / "drive_token.json"
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
        return build("drive", "v3", credentials=creds)

    def search_files(self, query: str, limit: int = 50) -> Iterable[DriveFile]:
        try:
            results = self.service.files().list(q=query, pageSize=limit, fields="files(id, name, mimeType)").execute()
        except HttpError as e:
            raise RuntimeError(f"Drive API error: {e}")

        for file in results.get("files", []):
            yield DriveFile(id=file["id"], name=file["name"], mime_type=file["mimeType"], path=Path(file["name"]))

    def download_file(self, drive_file: DriveFile, target_dir: Path) -> Path:
        from googleapiclient.http import MediaIoBaseDownload  # type: ignore
        import io

        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / drive_file.name
        request = self.service.files().get_media(fileId=drive_file.id)
        fh = io.FileIO(target_path, "wb")
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Download progress: {int(status.progress() * 100)}%")
        return target_path
