from __future__ import annotations

import ctypes
from pathlib import Path
from traceback import format_exc

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
    require_runtime_files(config)
    state = AppState()

    initialize_firebase_admin(config.firebase_service_account_path)
    login = run_google_login_and_resolve_uid(
        config.google_oauth_client_secret_path,
        config.google_oauth_scopes,
    )
    state.set_identity(login.uid, login.email)

    timer_watcher = FirebaseTimerWatcher(config, state, login.uid)
    process_guard = ProcessGuard(config, state, Path(config.whitelist_path))
    remote_api = RemoteUnlockServer(config, state)
    auto_updater = AutoUpdater(config, state)

    timer_watcher.start()
    process_guard.start()
    remote_api.start()
    auto_updater.start()

    app = AppWindow(state)
    app.set_login(login.uid, login.email)
    app.mainloop()


def run_safe() -> None:
    try:
        run()
    except Exception as exc:  # pylint: disable=broad-except
        message = (
            "StudyFlow Device Lock failed to start.\n\n"
            f"{exc}\n\n"
            "Please verify .env, service-account.json, oauth-client-secret.json, and whitelist.json."
        )
        log_dir = Path.home() / "AppData" / "Local" / "StudyFlowDeviceLock"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "startup-error.log").write_text(format_exc(), encoding="utf-8")
        ctypes.windll.user32.MessageBoxW(0, message, "StudyFlow Device Lock", 0x10)


if __name__ == "__main__":
    run_safe()
