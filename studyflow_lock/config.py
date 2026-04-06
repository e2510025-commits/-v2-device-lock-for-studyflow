from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    app_root: Path
    firebase_service_account_path: str
    google_oauth_client_secret_path: str
    google_oauth_scopes: list[str]
    firestore_timer_doc_path_template: str
    firestore_timer_field_path: str
    firestore_timer_remaining_path: str
    remote_unlock_host: str
    remote_unlock_port: int
    remote_unlock_secret: str
    remote_unlock_duration_seconds: int
    process_watch_interval_seconds: float
    lock_enforcement_mode: str
    github_repo: str
    app_version: str
    auto_update_enabled: bool
    auto_update_check_interval_hours: int
    whitelist_path: Path


    @staticmethod
    def load() -> "AppConfig":
        if getattr(sys, "frozen", False):
            app_root = Path(sys.executable).resolve().parent
        else:
            app_root = Path(__file__).resolve().parents[1]

        def _resolve_path(raw: str) -> str:
            candidate = Path(raw)
            if candidate.is_absolute():
                return str(candidate)
            return str((app_root / candidate).resolve())

        whitelist_raw = os.getenv("WHITELIST_PATH", "./whitelist.json")
        whitelist_candidate = Path(_resolve_path(whitelist_raw))
        default_whitelist = (app_root / "whitelist.json").resolve()
        if not whitelist_candidate.exists() and default_whitelist.exists():
            whitelist_candidate = default_whitelist

        return AppConfig(
            app_root=app_root,
            firebase_service_account_path=_resolve_path(
                os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "./service-account.json")
            ),
            google_oauth_client_secret_path=_resolve_path(
                os.getenv("GOOGLE_OAUTH_CLIENT_SECRET_PATH", "./oauth-client-secret.json")
            ),
            google_oauth_scopes=[
                scope.strip()
                for scope in os.getenv("GOOGLE_OAUTH_SCOPES", "openid,email,profile").split(",")
                if scope.strip()
            ],
            firestore_timer_doc_path_template=os.getenv(
                "FIRESTORE_TIMER_DOC_PATH_TEMPLATE", "users/{uid}"
            ),
            firestore_timer_field_path=os.getenv(
                "FIRESTORE_TIMER_FIELD_PATH", "status.is_timer_running"
            ),
            firestore_timer_remaining_path=os.getenv(
                "FIRESTORE_TIMER_REMAINING_PATH", "status.remaining_seconds"
            ),
            remote_unlock_host=os.getenv("REMOTE_UNLOCK_HOST", "127.0.0.1"),
            remote_unlock_port=int(os.getenv("REMOTE_UNLOCK_PORT", "8765")),
            remote_unlock_secret=os.getenv("REMOTE_UNLOCK_SECRET", "change-me"),
            remote_unlock_duration_seconds=int(
                os.getenv("REMOTE_UNLOCK_DURATION_SECONDS", "300")
            ),
            process_watch_interval_seconds=float(
                os.getenv("PROCESS_WATCH_INTERVAL_SECONDS", "0.5")
            ),
            lock_enforcement_mode=os.getenv("LOCK_ENFORCEMENT_MODE", "both").lower(),
            github_repo=os.getenv("GITHUB_REPO", "e2510025-commits/-v2-device-lock-for-studyflow"),
            app_version=os.getenv("APP_VERSION", "0.2.1"),
            auto_update_enabled=os.getenv("AUTO_UPDATE_ENABLED", "true").lower()
            in {"1", "true", "yes", "on"},
            auto_update_check_interval_hours=int(
                os.getenv("AUTO_UPDATE_CHECK_INTERVAL_HOURS", "6")
            ),
            whitelist_path=whitelist_candidate,
        )
