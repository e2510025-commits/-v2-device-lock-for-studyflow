from __future__ import annotations

from dataclasses import asdict
import threading

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from studyflow_lock.config import AppConfig
from studyflow_lock.state import AppState


class RemoteUnlockRequest(BaseModel):
    uid: str
    secret: str


class RemoteUnlockServer:
    def __init__(self, config: AppConfig, state: AppState) -> None:
        self.config = config
        self.state = state
        self.app = FastAPI(title="StudyFlow Remote Unlock API")
        self._thread: threading.Thread | None = None
        self._build_routes()

    def _build_routes(self) -> None:
        @self.app.get("/health")
        def health() -> dict[str, str]:
            return {"status": "ok"}

        @self.app.get("/status")
        def status() -> dict:
            return asdict(self.state.snapshot())

        @self.app.post("/remote-unlock")
        def remote_unlock(req: RemoteUnlockRequest) -> dict[str, str]:
            snapshot = self.state.snapshot()
            if req.secret != self.config.remote_unlock_secret:
                raise HTTPException(status_code=403, detail="invalid secret")
            if not snapshot.uid or req.uid != snapshot.uid:
                raise HTTPException(status_code=403, detail="uid mismatch")

            self.state.arm_remote_unlock(self.config.remote_unlock_duration_seconds)
            self.state.set_warning("Remote unlock accepted from API")
            return {"result": "unlocked"}

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _run() -> None:
            uvicorn.run(
                self.app,
                host=self.config.remote_unlock_host,
                port=self.config.remote_unlock_port,
                log_level="warning",
            )

        self._thread = threading.Thread(target=_run, name="remote-unlock-api", daemon=True)
        self._thread.start()
