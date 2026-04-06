from __future__ import annotations

from dataclasses import dataclass
import json
import socket

import firebase_admin
from firebase_admin import auth, credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import requests

from studyflow_lock.config import AppConfig


@dataclass(frozen=True)
class LoginResult:
    uid: str
    email: str


def initialize_firebase_admin(service_account_path: str) -> None:
    if firebase_admin._apps:  # pylint: disable=protected-access
        return
    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred)


def run_google_login_and_resolve_uid(client_secret_path: str, scopes: list[str]) -> LoginResult:
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, scopes=scopes)
    credentials_data = flow.run_local_server(port=0, open_browser=True)

    # Use Google userinfo endpoint, then map to Firebase Auth user by email.
    response = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {credentials_data.token}"},
        timeout=10,
    )
    response.raise_for_status()
    profile = json.loads(response.text)
    email = profile.get("email")
    if not email:
        raise RuntimeError("Google login succeeded but email claim was missing")

    firebase_user = auth.get_user_by_email(email)
    return LoginResult(uid=firebase_user.uid, email=email)


def run_pairing_code_login(config: AppConfig, code: str) -> LoginResult:
    pairing_code = code.strip()
    if len(pairing_code) < config.pairing_code_min_length:
        raise ValueError(f"ペアリングコードは{config.pairing_code_min_length}文字以上で入力してください。")

    endpoint = f"{config.pairing_api_base_url.rstrip('/')}/{config.pairing_api_path.lstrip('/')}"
    payload = {
        "code": pairing_code,
        "deviceName": socket.gethostname(),
        "platform": "windows",
    }
    response = requests.post(endpoint, json=payload, timeout=20)
    if response.status_code >= 400:
        raise RuntimeError(f"ペアリング失敗: HTTP {response.status_code}")

    body = json.loads(response.text)
    uid = (
        body.get("uid")
        or (body.get("data") or {}).get("uid")
        or (body.get("result") or {}).get("uid")
    )
    email = (
        body.get("email")
        or (body.get("data") or {}).get("email")
        or (body.get("result") or {}).get("email")
        or "unknown@studyflow"
    )
    if not uid:
        raise RuntimeError("ペアリング応答に uid がありません。サーバー仕様を確認してください。")
    return LoginResult(uid=uid, email=email)
