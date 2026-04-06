from __future__ import annotations

import threading
import time
from typing import Any

from firebase_admin import firestore

from studyflow_lock.config import AppConfig
from studyflow_lock.state import AppState


class FirebaseTimerWatcher:
    def __init__(self, config: AppConfig, state: AppState, uid: str) -> None:
        self.config = config
        self.state = state
        self.uid = uid
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="firebase-timer-watcher", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3)

    def _read_value_by_path(self, document: dict[str, Any], field_path: str) -> Any:
        current: Any = document
        for key in field_path.split("."):
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current

    def _run(self) -> None:
        db = firestore.client()
        doc_path = self.config.firestore_timer_doc_path_template.format(uid=self.uid)
        doc_ref = db.document(doc_path)

        last_running: bool | None = None
        while not self._stop_event.is_set():
            try:
                doc = doc_ref.get()
                payload = doc.to_dict() or {}
                running_raw = self._read_value_by_path(payload, self.config.firestore_timer_field_path)
                remaining_raw = self._read_value_by_path(
                    payload, self.config.firestore_timer_remaining_path
                )

                running = bool(running_raw)
                remaining = int(remaining_raw) if isinstance(remaining_raw, (int, float)) else None

                if running != last_running:
                    self.state.set_warning(
                        "LOCK ON: Web timer is running"
                        if running
                        else "IDLE: Web timer stopped"
                    )
                self.state.set_timer_status(running, remaining)
                last_running = running
            except Exception as exc:  # pylint: disable=broad-except
                self.state.set_warning(f"Firebase sync error: {exc}")

            time.sleep(1.0)
