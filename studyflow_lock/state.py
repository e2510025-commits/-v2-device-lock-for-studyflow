from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import threading


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


@dataclass
class Snapshot:
    uid: str | None
    email: str | None
    is_locking: bool
    timer_running: bool
    remaining_seconds: int | None
    active_executable: str
    active_window_title: str
    warning_message: str
    overlay_active: bool
    overlay_message: str
    remote_unlock_until_iso: str | None


class AppState:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.uid: str | None = None
        self.email: str | None = None
        self.timer_running: bool = False
        self.local_lock_override: bool | None = None
        self.remaining_seconds: int | None = None
        self.active_executable: str = ""
        self.active_window_title: str = ""
        self.warning_message: str = ""
        self.overlay_active: bool = False
        self.overlay_message: str = ""
        self.remote_unlock_until: datetime | None = None

    def set_identity(self, uid: str, email: str) -> None:
        with self._lock:
            self.uid = uid
            self.email = email

    def set_timer_status(self, running: bool, remaining_seconds: int | None) -> None:
        with self._lock:
            self.timer_running = running
            self.remaining_seconds = remaining_seconds

    def set_local_override(self, lock_on: bool | None) -> None:
        with self._lock:
            self.local_lock_override = lock_on

    def set_active_window(self, executable: str, title: str) -> None:
        with self._lock:
            self.active_executable = executable
            self.active_window_title = title

    def set_warning(self, message: str) -> None:
        with self._lock:
            self.warning_message = message

    def set_overlay(self, active: bool, message: str = "") -> None:
        with self._lock:
            self.overlay_active = active
            self.overlay_message = message

    def arm_remote_unlock(self, duration_seconds: int) -> None:
        with self._lock:
            self.remote_unlock_until = _utcnow() + timedelta(seconds=duration_seconds)

    def is_remote_unlock_active(self) -> bool:
        with self._lock:
            if self.remote_unlock_until is None:
                return False
            if _utcnow() > self.remote_unlock_until:
                self.remote_unlock_until = None
                return False
            return True

    def is_locking(self) -> bool:
        with self._lock:
            if self.is_remote_unlock_active():
                return False
            if self.local_lock_override is None:
                return self.timer_running
            return self.local_lock_override

    def snapshot(self) -> Snapshot:
        with self._lock:
            return Snapshot(
                uid=self.uid,
                email=self.email,
                is_locking=self.is_locking(),
                timer_running=self.timer_running,
                remaining_seconds=self.remaining_seconds,
                active_executable=self.active_executable,
                active_window_title=self.active_window_title,
                warning_message=self.warning_message,
                overlay_active=self.overlay_active,
                overlay_message=self.overlay_message,
                remote_unlock_until_iso=self.remote_unlock_until.isoformat()
                if self.remote_unlock_until
                else None,
            )
