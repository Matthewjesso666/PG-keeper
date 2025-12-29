"""Google Drive fetching helpers."""
from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from typing import List

from pg_keeper.config import GoogleAuthConfig
from pg_keeper.models import Document, SourceType


@dataclass
class DriveClient:
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
                f"Missing Google client libraries ({joined}). Install google-api-python-client "
                "and google-auth-httplib2 to enable Drive sync."
            )

    def fetch_recent_files(self, limit: int = 25) -> List[Document]:
        self._ensure_google_dependencies()

        from google.oauth2.credentials import Credentials  # type: ignore
        from googleapiclient.discovery import build  # type: ignore

        credentials = Credentials.from_authorized_user_file(
            str(self.config.token_file or self.config.credentials_file),
            scopes=self.config.scopes,
        )
        service = build("drive", "v3", credentials=credentials)
        results = (
            service.files()
            .list(pageSize=limit, fields="files(id, name, mimeType, modifiedTime)")
            .execute()
        )
        files = results.get("files", [])

        documents: List[Document] = []
        for file in files:
            documents.append(
                Document(
                    identifier=file.get("id", ""),
                    title=file.get("name", "Unnamed file"),
                    source=SourceType.DRIVE,
                    content=file.get("mimeType", ""),
                    metadata={"mimeType": file.get("mimeType", "")},
                )
            )
        return documents
