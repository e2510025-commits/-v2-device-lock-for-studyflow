from __future__ import annotations

import ctypes
from pathlib import Path
from traceback import format_exc
import threading

from studyflow_lock.auth import initialize_firebase_admin, run_google_login_and_resolve_uid
from studyflow_lock.config import AppConfig
from studyflow_lock.preflight import require_runtime_files
from studyflow_lock.services.auto_updater import AutoUpdater
from studyflow_lock.services.firebase_watcher import FirebaseTimerWatcher
from studyflow_lock.services.process_guard import ProcessGuard
from studyflow_lock.services.remote_unlock_api import RemoteUnlockServer
from studyflow_lock.state import AppState
from studyflow_lock.ui.app_window import AppWindow


def run() -> None:
    config = AppConfig.load()
    state = AppState()
    service_lock = threading.RLock()
    services_started = False
    timer_watcher: FirebaseTimerWatcher | None = None

    initialize_firebase_admin(config.firebase_service_account_path)
    process_guard = ProcessGuard(config, state, Path(config.whitelist_path))
    remote_api = RemoteUnlockServer(config, state)
    auto_updater = AutoUpdater(config, state)

    def on_google_login() -> tuple[str, str]:
        nonlocal services_started, timer_watcher
        require_runtime_files(config)
        login = run_google_login_and_resolve_uid(
            config.google_oauth_client_secret_path,
            config.google_oauth_scopes,
        )
        state.set_identity(login.uid, login.email)

        with service_lock:
            if not services_started:
                timer_watcher = FirebaseTimerWatcher(config, state, login.uid)
                timer_watcher.start()
                process_guard.start()
                remote_api.start()
                auto_updater.start()
                services_started = True

        state.set_warning("StudyFlowと連携しました。Webタイマーに自動同期します。")
        return login.uid, login.email

    def on_fetch_running_apps():
        return process_guard.list_running_apps()

    def on_allow_app(executable: str) -> None:
        process_guard.add_allowed(executable)

    def on_block_app(executable: str) -> None:
        process_guard.add_blocked(executable)

    def on_apply_preset(category: str) -> int:
        return process_guard.apply_preset(category)

    app = AppWindow(
        state=state,
        on_google_login=on_google_login,
        on_fetch_running_apps=on_fetch_running_apps,
        on_allow_app=on_allow_app,
        on_block_app=on_block_app,
        on_apply_preset=on_apply_preset,
    )
    app.mainloop()


def run_safe() -> None:
    try:
        run()
    except Exception as exc:  # pylint: disable=broad-except
        message = (
            "StudyFlow Device Lock failed to start.\n\n"
            f"{exc}\n\n"
            "The app will still open without credentials; add service-account.json and "
            "oauth-client-secret.json in the install folder before pressing Google login."
        )
        log_dir = Path.home() / "AppData" / "Local" / "StudyFlowDeviceLock"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "startup-error.log").write_text(format_exc(), encoding="utf-8")
        ctypes.windll.user32.MessageBoxW(0, message, "StudyFlow Device Lock", 0x10)


if __name__ == "__main__":
    run_safe()
