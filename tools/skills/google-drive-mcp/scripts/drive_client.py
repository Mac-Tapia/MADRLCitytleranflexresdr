"""Google Drive API client wrapper."""

from __future__ import annotations

import io
import mimetypes
from pathlib import Path
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from auth_manager import AuthManager
from config import DEFAULT_DRIVE_ROOT

FOLDER_MIME = "application/vnd.google-apps.folder"
EXPORT_MIME = {
    "application/vnd.google-apps.document": "text/plain",
    "application/vnd.google-apps.spreadsheet": "text/csv",
    "application/vnd.google-apps.presentation": "text/plain",
}


class DriveClient:
    """Thin wrapper around Drive API v3."""

    def __init__(self, auth: AuthManager | None = None) -> None:
        self._auth = auth or AuthManager()
        creds = self._auth.get_credentials()
        self._service = build("drive", "v3", credentials=creds, cache_discovery=False)

    def list_files(
        self,
        folder_id: str | None = None,
        folder_path: str | None = None,
        page_size: int = 50,
        include_trashed: bool = False,
    ) -> list[dict[str, Any]]:
        parent_id = folder_id or self._resolve_folder_path(folder_path)
        query_parts = [f"'{parent_id}' in parents"]
        if not include_trashed:
            query_parts.append("trashed = false")
        query = " and ".join(query_parts)

        results = (
            self._service.files()
            .list(
                q=query,
                pageSize=min(page_size, 100),
                fields=(
                    "files(id, name, mimeType, size, modifiedTime, "
                    "webViewLink, parents)"
                ),
                orderBy="folder,name",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        return [self._format_file(f) for f in results.get("files", [])]

    def search_files(
        self,
        query: str,
        folder_id: str | None = None,
        folder_path: str | None = None,
        page_size: int = 25,
    ) -> list[dict[str, Any]]:
        q_parts = [f"name contains '{self._escape_query(query)}'", "trashed = false"]
        if folder_id or folder_path:
            parent_id = folder_id or self._resolve_folder_path(folder_path)
            q_parts.append(f"'{parent_id}' in parents")

        results = (
            self._service.files()
            .list(
                q=" and ".join(q_parts),
                pageSize=min(page_size, 100),
                fields="files(id, name, mimeType, size, modifiedTime, webViewLink, parents)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        return [self._format_file(f) for f in results.get("files", [])]

    def get_file_info(self, file_id: str) -> dict[str, Any]:
        meta = (
            self._service.files()
            .get(
                fileId=file_id,
                fields="id, name, mimeType, size, modifiedTime, webViewLink, parents",
                supportsAllDrives=True,
            )
            .execute()
        )
        return self._format_file(meta)

    def resolve_path(self, folder_path: str) -> dict[str, Any]:
        folder_id = self._resolve_folder_path(folder_path)
        return self.get_file_info(folder_id)

    def download_file(self, file_id: str, local_path: str) -> dict[str, Any]:
        meta = self.get_file_info(file_id)
        dest = Path(local_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if meta["mimeType"] in EXPORT_MIME:
            content = (
                self._service.files()
                .export(fileId=file_id, mimeType=EXPORT_MIME[meta["mimeType"]])
                .execute()
            )
            dest.write_bytes(content if isinstance(content, bytes) else content.encode())
        else:
            request = self._service.files().get_media(fileId=file_id)
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            dest.write_bytes(buffer.getvalue())

        return {
            "file_id": file_id,
            "name": meta["name"],
            "local_path": str(dest.resolve()),
            "size_bytes": dest.stat().st_size,
        }

    def read_file_content(self, file_id: str, max_bytes: int = 512_000) -> dict[str, Any]:
        meta = self.get_file_info(file_id)
        if meta.get("size") and int(meta["size"]) > max_bytes:
            return {
                "error": (
                    f"Archivo demasiado grande ({meta['size']} bytes). "
                    f"Usa download_file (máx inline: {max_bytes} bytes)."
                ),
                "file_id": file_id,
                "name": meta["name"],
            }

        if meta["mimeType"] in EXPORT_MIME:
            content = (
                self._service.files()
                .export(fileId=file_id, mimeType=EXPORT_MIME[meta["mimeType"]])
                .execute()
            )
            text = content.decode("utf-8") if isinstance(content, bytes) else content
        else:
            request = self._service.files().get_media(fileId=file_id)
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            raw = buffer.getvalue()
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                return {
                    "error": "Archivo binario; usa download_file.",
                    "file_id": file_id,
                    "name": meta["name"],
                    "size_bytes": len(raw),
                }

        return {
            "file_id": file_id,
            "name": meta["name"],
            "mimeType": meta["mimeType"],
            "content": text,
            "truncated": len(text) >= max_bytes,
        }

    def upload_file(
        self,
        local_path: str,
        folder_id: str | None = None,
        folder_path: str | None = None,
        drive_name: str | None = None,
    ) -> dict[str, Any]:
        src = Path(local_path)
        if not src.is_file():
            raise FileNotFoundError(f"No existe: {local_path}")

        parent_id = folder_id or self._resolve_folder_path(
            folder_path or DEFAULT_DRIVE_ROOT
        )
        name = drive_name or src.name
        mime, _ = mimetypes.guess_type(str(src))
        media = MediaFileUpload(str(src), mimetype=mime or "application/octet-stream")

        created = (
            self._service.files()
            .create(
                body={"name": name, "parents": [parent_id]},
                media_body=media,
                fields="id, name, mimeType, size, webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )
        return self._format_file(created)

    def create_folder(
        self,
        name: str,
        parent_folder_id: str | None = None,
        parent_folder_path: str | None = None,
    ) -> dict[str, Any]:
        parents = []
        if parent_folder_id:
            parents = [parent_folder_id]
        elif parent_folder_path:
            parents = [self._resolve_folder_path(parent_folder_path)]

        body: dict[str, Any] = {"name": name, "mimeType": FOLDER_MIME}
        if parents:
            body["parents"] = parents

        created = (
            self._service.files()
            .create(body=body, fields="id, name, mimeType, webViewLink", supportsAllDrives=True)
            .execute()
        )
        return self._format_file(created)

    def _resolve_folder_path(self, folder_path: str | None) -> str:
        if not folder_path or folder_path in ("root", "/"):
            return "root"

        parts = [p for p in folder_path.replace("\\", "/").split("/") if p]
        parent_id = "root"
        for part in parts:
            parent_id = self._find_child_folder(parent_id, part)
        return parent_id

    def _find_child_folder(self, parent_id: str, name: str) -> str:
        q = (
            f"'{parent_id}' in parents and "
            f"name = '{self._escape_query(name)}' and "
            f"mimeType = '{FOLDER_MIME}' and trashed = false"
        )
        results = (
            self._service.files()
            .list(
                q=q,
                pageSize=1,
                fields="files(id)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        files = results.get("files", [])
        if not files:
            raise FileNotFoundError(
                f"Carpeta no encontrada: '{name}' bajo parent {parent_id}"
            )
        return files[0]["id"]

    @staticmethod
    def _escape_query(value: str) -> str:
        return value.replace("'", "\\'")

    @staticmethod
    def _format_file(meta: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": meta.get("id"),
            "name": meta.get("name"),
            "mimeType": meta.get("mimeType"),
            "size": meta.get("size"),
            "modifiedTime": meta.get("modifiedTime"),
            "webViewLink": meta.get("webViewLink"),
            "parents": meta.get("parents", []),
            "is_folder": meta.get("mimeType") == FOLDER_MIME,
        }
