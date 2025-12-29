import io
from typing import Dict, Iterable, List, Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


class DriveClient:
    """Google Drive wrapper to pull documents relevant to the case."""

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

        self._service = build("drive", "v3", credentials=creds)
        return self._service

    def fetch_files(self, folder_ids: Optional[Iterable[str]] = None) -> List[Dict]:
        service = self.authenticate()
        folders = folder_ids or self.config["drive"].get("folder_ids", [])
        collected: List[Dict] = []
        for folder_id in folders:
            query = f"'{folder_id}' in parents"
            response = service.files().list(q=query, fields="files(id, name, mimeType, modifiedTime)").execute()
            for file_meta in response.get("files", []):
                text, raw_bytes = self._download_file(service, file_meta["id"], file_meta["mimeType"])
                collected.append(
                    {
                        "id": file_meta["id"],
                        "name": file_meta["name"],
                        "mimeType": file_meta["mimeType"],
                        "modifiedTime": file_meta["modifiedTime"],
                        "text": text,
                        "bytes": raw_bytes,
                        "source": "drive",
                    }
                )
        return collected

    def _download_file(
        self, service, file_id: str, mime_type: str, export_as: Optional[str] = None
    ) -> Tuple[str, bytes]:
        export_type = export_as
        if not export_type and mime_type.startswith("application/vnd.google-apps"):
            export_type = "text/plain"

        buffer = io.BytesIO()
        if export_type:
            request = service.files().export_media(fileId=file_id, mimeType=export_type)
        else:
            request = service.files().get_media(fileId=file_id)

        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        raw_bytes = buffer.getvalue()
        text = raw_bytes.decode("utf-8", errors="ignore") if export_type else ""
        return text, raw_bytes
