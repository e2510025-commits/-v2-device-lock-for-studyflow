from __future__ import annotations

import json
from pathlib import Path
import threading
import time

import psutil
import win32con
import win32gui
import win32process

from studyflow_lock.config import AppConfig
from studyflow_lock.state import AppState


class ProcessGuard:
    def __init__(self, config: AppConfig, state: AppState, whitelist_path: Path) -> None:
        self.config = config
        self.state = state
        self.whitelist_path = whitelist_path
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.allowed_executables: set[str] = set()
        self.safety_exempt_executables: set[str] = set()
        self._load_whitelist()

    def _load_whitelist(self) -> None:
        data = json.loads(self.whitelist_path.read_text(encoding="utf-8"))
        self.allowed_executables = {
            item.strip().lower() for item in data.get("allowed_executables", []) if item.strip()
        }
        self.safety_exempt_executables = {
            item.strip().lower()
            for item in data.get("safety_exempt_executables", [])
            if item.strip()
        }

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="process-guard", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3)

    def _foreground_process(self) -> tuple[int, str, str]:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return 0, "", ""
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        title = win32gui.GetWindowText(hwnd)
        try:
            proc = psutil.Process(pid)
            exe = proc.name().lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            exe = ""
        return hwnd, exe, title

    def _minimize(self, hwnd: int) -> None:
        if hwnd and win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                hwnd, exe, title = self._foreground_process()
                self.state.set_active_window(exe, title)

                if not self.state.is_locking():
                    time.sleep(self.config.process_watch_interval_seconds)
                    continue

                if not exe:
                    time.sleep(self.config.process_watch_interval_seconds)
                    continue

                if exe in self.safety_exempt_executables:
                    time.sleep(self.config.process_watch_interval_seconds)
                    continue

                if exe not in self.allowed_executables:
                    self._minimize(hwnd)
                    self.state.set_warning(
                        f"Blocked app minimized: {exe} ({title[:40]})"
                    )
                else:
                    self.state.set_warning("LOCK ON: allowed app in focus")
            except Exception as exc:  # pylint: disable=broad-except
                self.state.set_warning(f"Process guard error: {exc}")

            time.sleep(self.config.process_watch_interval_seconds)
