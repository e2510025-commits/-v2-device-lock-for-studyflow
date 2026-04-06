from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class RunningApp:
    executable: str
    display_name: str


class ProcessGuard:
    def __init__(self, config: AppConfig, state: AppState, whitelist_path: Path) -> None:
        self.config = config
        self.state = state
        self.whitelist_path = whitelist_path
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.allowed_executables: set[str] = set()
        self.blocked_executables: set[str] = set()
        self.safety_exempt_executables: set[str] = set()
        self.presets: dict[str, list[str]] = {}
        self._rules_lock = threading.RLock()
        self._load_whitelist()

    def _is_minimize_enabled(self) -> bool:
        return self.config.lock_enforcement_mode in {"minimize", "both"}

    def _is_overlay_enabled(self) -> bool:
        return self.config.lock_enforcement_mode in {"overlay", "both"}

    def _load_whitelist(self) -> None:
        with self._rules_lock:
            data = json.loads(self.whitelist_path.read_text(encoding="utf-8"))
            self.allowed_executables = {
                item.strip().lower() for item in data.get("allowed_executables", []) if item.strip()
            }
            self.blocked_executables = {
                item.strip().lower() for item in data.get("blocked_executables", []) if item.strip()
            }
            self.safety_exempt_executables = {
                item.strip().lower()
                for item in data.get("safety_exempt_executables", [])
                if item.strip()
            }
            self.presets = {
                key: [item.strip().lower() for item in values if item.strip()]
                for key, values in data.get("presets", {}).items()
                if isinstance(values, list)
            }

    def _save_whitelist(self) -> None:
        with self._rules_lock:
            payload = {
                "allowed_executables": sorted(self.allowed_executables),
                "blocked_executables": sorted(self.blocked_executables),
                "safety_exempt_executables": sorted(self.safety_exempt_executables),
                "presets": self.presets,
            }
            self.whitelist_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    def list_running_apps(self) -> list[RunningApp]:
        seen: set[str] = set()
        apps: list[RunningApp] = []
        for proc in psutil.process_iter(["name"]):
            try:
                name = str(proc.info.get("name") or "").strip().lower()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            if not name or not name.endswith(".exe"):
                continue
            if name in seen:
                continue
            if name in self.safety_exempt_executables:
                continue
            seen.add(name)
            apps.append(RunningApp(executable=name, display_name=name.replace(".exe", "").title()))

        apps.sort(key=lambda item: item.executable)
        return apps

    def add_allowed(self, executable: str) -> None:
        exe = executable.strip().lower()
        if not exe:
            return
        with self._rules_lock:
            self.allowed_executables.add(exe)
            self.blocked_executables.discard(exe)
        self._save_whitelist()

    def add_blocked(self, executable: str) -> None:
        exe = executable.strip().lower()
        if not exe:
            return
        with self._rules_lock:
            self.blocked_executables.add(exe)
            self.allowed_executables.discard(exe)
        self._save_whitelist()

    def apply_preset(self, category: str) -> int:
        key = category.strip().lower()
        with self._rules_lock:
            values = self.presets.get(key, [])
            for exe in values:
                self.blocked_executables.add(exe)
                self.allowed_executables.discard(exe)
        self._save_whitelist()
        return len(values)

    def get_rules_snapshot(self) -> tuple[list[str], list[str]]:
        with self._rules_lock:
            return (sorted(self.allowed_executables), sorted(self.blocked_executables))

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
                    self.state.set_overlay(False, "")
                    time.sleep(self.config.process_watch_interval_seconds)
                    continue

                if not exe:
                    self.state.set_overlay(False, "")
                    time.sleep(self.config.process_watch_interval_seconds)
                    continue

                if exe in self.safety_exempt_executables:
                    self.state.set_overlay(False, "")
                    time.sleep(self.config.process_watch_interval_seconds)
                    continue

                is_blocked = exe in self.blocked_executables
                is_not_allowed = bool(self.allowed_executables) and exe not in self.allowed_executables

                if is_blocked or is_not_allowed:
                    overlay_message = (
                        "STUDY LOCK ACTIVE\n\n"
                        "許可されていないアプリが検出されました。\n"
                        f"対象: {exe}\n"
                        "StudyFlowのタイマーを停止するか、許可アプリへ戻ってください。"
                    )
                    if self._is_minimize_enabled():
                        self._minimize(hwnd)
                    if self._is_overlay_enabled():
                        self.state.set_overlay(True, overlay_message)
                    self.state.set_warning(f"Blocked app detected: {exe} ({title[:40]})")
                else:
                    self.state.set_overlay(False, "")
                    self.state.set_warning("LOCK ON: allowed app in focus")
            except Exception as exc:  # pylint: disable=broad-except
                self.state.set_overlay(False, "")
                self.state.set_warning(f"Process guard error: {exc}")

            time.sleep(self.config.process_watch_interval_seconds)
