from __future__ import annotations

from pathlib import Path

from studyflow_lock.config import AppConfig


def require_runtime_files(config: AppConfig) -> None:
    service_account = Path(config.firebase_service_account_path)
    oauth_secret = Path(config.google_oauth_client_secret_path)

    missing = [str(path) for path in (service_account, oauth_secret) if not path.exists()]
    if missing:
        missing_text = ", ".join(missing)
        raise FileNotFoundError(
            "Required credential files are missing: "
            f"{missing_text}. Please copy files and retry."
        )
