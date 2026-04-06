from __future__ import annotations

from dataclasses import dataclass
import json

import firebase_admin
from firebase_admin import auth, credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import requests


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
