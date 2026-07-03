"""OAuth2 authentication for Google Drive API."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from config import AUTH_INFO_FILE, CREDENTIALS_FILE, DATA_DIR, SCOPES, TOKEN_FILE


class AuthManager:
    """Manages Google OAuth2 credentials for Drive API."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def is_authenticated(self) -> bool:
        return TOKEN_FILE.exists() and self._load_credentials() is not None

    def get_auth_info(self) -> dict:
        if not TOKEN_FILE.exists():
            return {"authenticated": False}

        info: dict = {"authenticated": True}
        if AUTH_INFO_FILE.exists():
            try:
                info.update(json.loads(AUTH_INFO_FILE.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                pass

        if TOKEN_FILE.exists():
            age_hours = (
                datetime.now(timezone.utc).timestamp() - TOKEN_FILE.stat().st_mtime
            ) / 3600
            info["token_age_hours"] = round(age_hours, 2)

        return info

    def validate_auth(self) -> bool:
        creds = self._load_credentials()
        if creds is None:
            return False
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_credentials(creds)
                return True
            except Exception:
                return False
        return creds.valid

    def setup_auth(self, port: int = 0) -> bool:
        if not CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                f"Falta {CREDENTIALS_FILE}. "
                "Descarga credentials.json desde Google Cloud Console "
                "(OAuth 2.0 Client ID tipo Desktop) y colócalo en data/."
            )

        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
        creds = flow.run_local_server(port=port, open_browser=True)
        self._save_credentials(creds)
        self._save_auth_info()
        return True

    def re_auth(self, port: int = 0) -> bool:
        for path in (TOKEN_FILE, AUTH_INFO_FILE):
            if path.exists():
                path.unlink()
        return self.setup_auth(port=port)

    def get_credentials(self) -> Credentials:
        creds = self._load_credentials()
        if creds is None:
            raise RuntimeError(
                "No autenticado. Ejecuta setup_auth primero "
                "(requiere data/credentials.json de Google Cloud)."
            )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self._save_credentials(creds)

        return creds

    def _load_credentials(self) -> Credentials | None:
        if not TOKEN_FILE.exists():
            return None

        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_credentials(creds)
            except Exception:
                return None
        return creds if creds and creds.valid else None

    def _save_credentials(self, creds: Credentials) -> None:
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    def _save_auth_info(self) -> None:
        AUTH_INFO_FILE.write_text(
            json.dumps(
                {
                    "authenticated_at_iso": datetime.now(timezone.utc).isoformat(),
                    "scopes": SCOPES,
                },
                indent=2,
            ),
            encoding="utf-8",
        )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Google Drive MCP auth")
    parser.add_argument("action", choices=["setup", "check", "reauth"])
    args = parser.parse_args()

    auth = AuthManager()
    if args.action == "setup":
        ok = auth.setup_auth()
        print("OK" if ok else "FAIL")
        return 0 if ok else 1
    if args.action == "check":
        print("authenticated" if auth.validate_auth() else "not_authenticated")
        return 0
    if args.action == "reauth":
        ok = auth.re_auth()
        print("OK" if ok else "FAIL")
        return 0 if ok else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
