"""Configuration paths for Google Drive MCP."""

from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = SKILL_DIR / "data"
CREDENTIALS_FILE = DATA_DIR / "credentials.json"
TOKEN_FILE = DATA_DIR / "token.json"
AUTH_INFO_FILE = DATA_DIR / "auth_info.json"

# Full Drive access (read/write). Use drive.readonly for read-only.
SCOPES = ["https://www.googleapis.com/auth/drive"]

# Default project folder on Drive (under My Drive root)
DEFAULT_DRIVE_ROOT = "MADRLCitytleranflexresdr"
