from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class AppConfig:
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


    @staticmethod
    def load() -> "AppConfig":
        return AppConfig(
            firebase_service_account_path=os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "./service-account.json"),
            google_oauth_client_secret_path=os.getenv(
                "GOOGLE_OAUTH_CLIENT_SECRET_PATH", "./oauth-client-secret.json"
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
        )
