from __future__ import annotations

import customtkinter as ctk

from studyflow_lock.state import AppState


class AppWindow(ctk.CTk):
    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("StudyFlow Device Lock")
        self.geometry("860x560")
        self.configure(fg_color="#fafafa")

        self.container = ctk.CTkFrame(
            self,
            fg_color="#fafafa",
            corner_radius=8,
            border_width=1,
            border_color="#d4d4d8",
        )
        self.container.pack(fill="both", expand=True, padx=14, pady=14)

        self.tabs = ctk.CTkTabview(self.container, border_width=1, border_color="#d4d4d8")
        self.tabs.pack(fill="both", expand=True, padx=12, pady=12)
        self.tabs.add("メイン")
        self.tabs.add("詳細設定")

        main = self.tabs.tab("メイン")
        detail = self.tabs.tab("詳細設定")

        self.login_label = ctk.CTkLabel(
            main,
            text="ログイン: 未認証",
            text_color="#18181b",
            font=("Segoe UI", 18, "bold"),
        )
        self.login_label.pack(anchor="w", padx=16, pady=(16, 8))

        self.status_label = ctk.CTkLabel(
            main,
            text="IDLE",
            text_color="#18181b",
            fg_color="#ffffff",
            corner_radius=8,
            width=280,
            height=70,
            border_width=2,
            border_color="#d4d4d8",
            font=("Segoe UI", 36, "bold"),
        )
        self.status_label.pack(anchor="w", padx=16, pady=8)

        self.remaining_label = ctk.CTkLabel(
            main,
            text="残り時間: --:--",
            text_color="#18181b",
            font=("Segoe UI", 20, "bold"),
        )
        self.remaining_label.pack(anchor="w", padx=16, pady=8)

        self.active_app_label = ctk.CTkLabel(
            main,
            text="アクティブアプリ: -",
            text_color="#18181b",
            font=("Segoe UI", 15),
        )
        self.active_app_label.pack(anchor="w", padx=16, pady=(8, 4))

        self.warning_label = ctk.CTkLabel(
            main,
            text="",
            text_color="#991b1b",
            wraplength=780,
            justify="left",
            font=("Segoe UI", 14, "bold"),
        )
        self.warning_label.pack(anchor="w", padx=16, pady=(6, 16))

        buttons = ctk.CTkFrame(main, fg_color="transparent")
        buttons.pack(anchor="w", padx=16, pady=8)

        self.start_button = ctk.CTkButton(
            buttons,
            text="スタート(ローカル強制)",
            width=220,
            border_width=1,
            border_color="#d4d4d8",
            command=self._force_start,
        )
        self.start_button.pack(side="left", padx=(0, 8))

        self.stop_button = ctk.CTkButton(
            buttons,
            text="ストップ(ローカル解除)",
            width=220,
            fg_color="#ffffff",
            text_color="#18181b",
            border_width=1,
            border_color="#d4d4d8",
            command=self._force_stop,
        )
        self.stop_button.pack(side="left")

        self.whitelist_hint = ctk.CTkLabel(
            detail,
            text="ホワイトリストは whitelist.json を編集してください。\n通常運用ではこのタブを開く必要はありません。",
            text_color="#18181b",
            justify="left",
            font=("Segoe UI", 14),
        )
        self.whitelist_hint.pack(anchor="w", padx=16, pady=16)

        self.after(300, self._refresh)

    def set_login(self, uid: str, email: str) -> None:
        self.login_label.configure(text=f"ログイン: {email} (uid: {uid})")

    def _force_start(self) -> None:
        self.state.set_local_override(True)

    def _force_stop(self) -> None:
        self.state.set_local_override(False)

    def _refresh(self) -> None:
        snap = self.state.snapshot()

        if snap.is_locking:
            self.status_label.configure(text="LOCKING", text_color="#991b1b")
        else:
            self.status_label.configure(text="IDLE", text_color="#166534")

        remaining = snap.remaining_seconds
        if remaining is None or remaining < 0:
            remaining_text = "--:--"
        else:
            m, s = divmod(remaining, 60)
            remaining_text = f"{m:02d}:{s:02d}"

        self.remaining_label.configure(text=f"残り時間: {remaining_text}")
        app_text = snap.active_executable or "-"
        if snap.active_window_title:
            app_text = f"{app_text} | {snap.active_window_title[:48]}"
        self.active_app_label.configure(text=f"アクティブアプリ: {app_text}")
        self.warning_label.configure(text=snap.warning_message)

        self.after(300, self._refresh)
