from __future__ import annotations

from pathlib import Path

from studyflow_lock.auth import initialize_firebase_admin, run_google_login_and_resolve_uid
from studyflow_lock.config import AppConfig
from studyflow_lock.preflight import require_runtime_files
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
    process_guard = ProcessGuard(config, state, Path("./whitelist.json"))
    remote_api = RemoteUnlockServer(config, state)

    timer_watcher.start()
    process_guard.start()
    remote_api.start()

    app = AppWindow(state)
    app.set_login(login.uid, login.email)
    app.mainloop()


if __name__ == "__main__":
    run()
