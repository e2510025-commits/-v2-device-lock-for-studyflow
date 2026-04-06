from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile
import threading
import time
from typing import Any

import requests

from studyflow_lock.config import AppConfig
from studyflow_lock.state import AppState


class AutoUpdater:
    def __init__(self, config: AppConfig, state: AppState) -> None:
        self.config = config
        self.state = state
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if not self.config.auto_update_enabled:
            self.state.set_warning("Auto update disabled")
            return
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="auto-updater", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._check_and_apply_update()
            except Exception as exc:  # pylint: disable=broad-except
                self.state.set_warning(f"Auto update error: {exc}")

            interval_seconds = max(1, self.config.auto_update_check_interval_hours) * 3600
            if self._stop_event.wait(timeout=interval_seconds):
                return

    def _parse_version(self, value: str) -> tuple[int, int, int]:
        # Accept formats like v1.2.3 or 1.2.3
        raw = value.strip().lower().lstrip("v")
        m = re.match(r"^(\d+)\.(\d+)\.(\d+)", raw)
        if not m:
            return (0, 0, 0)
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))

    def _select_asset(self, release: dict[str, Any]) -> tuple[str, str] | None:
        assets = release.get("assets", [])
        for asset in assets:
            name = str(asset.get("name", ""))
            url = str(asset.get("browser_download_url", ""))
            if name.lower().endswith(".exe") and "setup" in name.lower() and url:
                return (name, url)
        for asset in assets:
            name = str(asset.get("name", ""))
            url = str(asset.get("browser_download_url", ""))
            if name.lower().endswith(".exe") and url:
                return (name, url)
        return None

    def _check_and_apply_update(self) -> None:
        latest_url = f"https://api.github.com/repos/{self.config.github_repo}/releases/latest"
        response = requests.get(latest_url, timeout=20)
        if response.status_code != 200:
            self.state.set_warning("Auto update: latest release not available")
            return

        release = response.json()
        latest_tag = str(release.get("tag_name", ""))
        latest_version = self._parse_version(latest_tag)
        current_version = self._parse_version(self.config.app_version)

        if latest_version <= current_version:
            self.state.set_warning("Auto update: already on latest version")
            return

        selected = self._select_asset(release)
        if not selected:
            self.state.set_warning("Auto update: release asset not found")
            return

        name, download_url = selected
        self.state.set_warning(f"Auto update: downloading {name}")

        temp_dir = Path(tempfile.gettempdir()) / "studyflow-lock-updater"
        temp_dir.mkdir(parents=True, exist_ok=True)
        dest = temp_dir / name

        with requests.get(download_url, stream=True, timeout=60) as dl:
            dl.raise_for_status()
            with dest.open("wb") as fw:
                for chunk in dl.iter_content(chunk_size=1024 * 512):
                    if chunk:
                        fw.write(chunk)

        if "setup" in name.lower():
            # Inno Setup silent install flags
            subprocess.Popen(
                [str(dest), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
                close_fds=True,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
        else:
            subprocess.Popen(
                [str(dest)],
                close_fds=True,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )

        self.state.set_warning("Auto update started. App will exit now.")
        os._exit(0)
