from __future__ import annotations

from typing import Callable
from tkinter import messagebox

import customtkinter as ctk

from studyflow_lock.services.process_guard import RunningApp
from studyflow_lock.state import AppState


class AppWindow(ctk.CTk):
    def __init__(
        self,
        state: AppState,
        on_google_login: Callable[[], tuple[str, str]],
        on_fetch_running_apps: Callable[[], list[RunningApp]],
        on_allow_app: Callable[[str], None],
        on_block_app: Callable[[str], None],
        on_apply_preset: Callable[[str], int],
        on_get_rules_snapshot: Callable[[], tuple[list[str], list[str]]],
    ) -> None:
        super().__init__()
        self.app_state = state
        self.on_google_login = on_google_login
        self.on_fetch_running_apps = on_fetch_running_apps
        self.on_allow_app = on_allow_app
        self.on_block_app = on_block_app
        self.on_apply_preset = on_apply_preset
        self.on_get_rules_snapshot = on_get_rules_snapshot
        self._login_in_progress = False

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("StudyFlow Device Lock")
        self.geometry("960x660")
        self.configure(fg_color="#fafafa")

        self.container = ctk.CTkFrame(
            self,
            fg_color="#fafafa",
            corner_radius=10,
            border_width=1,
            border_color="#d4d4d8",
        )
        self.container.pack(fill="both", expand=True, padx=12, pady=12)

        self.tabs = ctk.CTkTabview(self.container, border_width=1, border_color="#d4d4d8")
        self.tabs.pack(fill="both", expand=True, padx=12, pady=12)
        self.tabs.add("メイン")
        self.tabs.add("詳細設定")

        self.main = self.tabs.tab("メイン")
        self.detail = self.tabs.tab("詳細設定")

        self._build_main_tab()
        self._build_detail_tab()

        self.overlay: ctk.CTkToplevel | None = None
        self.overlay_label: ctk.CTkLabel | None = None
        self._build_overlay()

        self.after(300, self._refresh)

    def _build_main_tab(self) -> None:
        hero = ctk.CTkFrame(
            self.main,
            fg_color="#ffffff",
            border_width=1,
            border_color="#d4d4d8",
            corner_radius=10,
        )
        hero.pack(fill="x", padx=16, pady=(16, 12))

        self.title_label = ctk.CTkLabel(
            hero,
            text="StudyFlow Auto Lock",
            text_color="#111827",
            font=("Segoe UI", 28, "bold"),
        )
        self.title_label.pack(anchor="w", padx=16, pady=(16, 4))

        self.subtitle_label = ctk.CTkLabel(
            hero,
            text="Googleでログインするだけで、Webタイマーと自動同期します",
            text_color="#374151",
            font=("Segoe UI", 14),
        )
        self.subtitle_label.pack(anchor="w", padx=16, pady=(0, 10))

        self.google_login_button = ctk.CTkButton(
            hero,
            text="Googleでログイン",
            width=220,
            height=40,
            border_width=1,
            border_color="#d4d4d8",
            command=self._handle_login_click,
        )
        self.google_login_button.pack(anchor="w", padx=16, pady=(0, 16))

        self.login_label = ctk.CTkLabel(
            self.main,
            text="ログイン状態: 未認証",
            text_color="#111827",
            font=("Segoe UI", 16, "bold"),
        )
        self.login_label.pack(anchor="w", padx=16, pady=(4, 8))

        status_wrap = ctk.CTkFrame(self.main, fg_color="transparent")
        status_wrap.pack(fill="x", padx=16, pady=8)

        self.status_card = ctk.CTkFrame(
            status_wrap,
            fg_color="#eff6ff",
            border_width=2,
            border_color="#93c5fd",
            corner_radius=12,
            width=320,
            height=120,
        )
        self.status_card.pack(side="left", padx=(0, 12))
        self.status_card.pack_propagate(False)

        self.status_icon = ctk.CTkLabel(
            self.status_card,
            text="○",
            text_color="#1d4ed8",
            font=("Segoe UI", 36, "bold"),
        )
        self.status_icon.pack(pady=(14, 0))

        self.status_label = ctk.CTkLabel(
            self.status_card,
            text="LOCK OFF",
            text_color="#1d4ed8",
            font=("Segoe UI", 24, "bold"),
        )
        self.status_label.pack(pady=(0, 8))

        info_card = ctk.CTkFrame(
            status_wrap,
            fg_color="#ffffff",
            border_width=1,
            border_color="#d4d4d8",
            corner_radius=12,
        )
        info_card.pack(side="left", fill="both", expand=True)

        self.remaining_label = ctk.CTkLabel(
            info_card,
            text="残り時間: --:--",
            text_color="#111827",
            font=("Segoe UI", 20, "bold"),
        )
        self.remaining_label.pack(anchor="w", padx=16, pady=(16, 8))

        self.active_app_label = ctk.CTkLabel(
            info_card,
            text="アクティブアプリ: -",
            text_color="#111827",
            font=("Segoe UI", 14),
        )
        self.active_app_label.pack(anchor="w", padx=16, pady=(0, 8))

        self.warning_label = ctk.CTkLabel(
            info_card,
            text="",
            text_color="#991b1b",
            wraplength=520,
            justify="left",
            font=("Segoe UI", 13, "bold"),
        )
        self.warning_label.pack(anchor="w", padx=16, pady=(0, 16))

    def _build_detail_tab(self) -> None:
        tip = ctk.CTkLabel(
            self.detail,
            text="詳細設定: 必要なときだけ使う画面です（通常はメイン画面だけでOK）",
            text_color="#111827",
            font=("Segoe UI", 14, "bold"),
        )
        tip.pack(anchor="w", padx=16, pady=(16, 8))

        preset_box = ctk.CTkFrame(
            self.detail,
            fg_color="#ffffff",
            border_width=1,
            border_color="#d4d4d8",
            corner_radius=10,
        )
        preset_box.pack(fill="x", padx=16, pady=(4, 10))

        preset_title = ctk.CTkLabel(
            preset_box,
            text="カテゴリ一括ブロック",
            text_color="#111827",
            font=("Segoe UI", 16, "bold"),
        )
        preset_title.pack(anchor="w", padx=12, pady=(10, 6))

        preset_buttons = ctk.CTkFrame(preset_box, fg_color="transparent")
        preset_buttons.pack(anchor="w", padx=12, pady=(0, 10))

        game_btn = ctk.CTkButton(
            preset_buttons,
            text="ゲームを一括ブロック",
            width=180,
            border_width=1,
            border_color="#d4d4d8",
            command=lambda: self._apply_preset("game"),
        )
        game_btn.pack(side="left", padx=(0, 8))

        sns_btn = ctk.CTkButton(
            preset_buttons,
            text="SNSを一括ブロック",
            width=180,
            border_width=1,
            border_color="#d4d4d8",
            command=lambda: self._apply_preset("sns"),
        )
        sns_btn.pack(side="left")

        picker_box = ctk.CTkFrame(
            self.detail,
            fg_color="#ffffff",
            border_width=1,
            border_color="#d4d4d8",
            corner_radius=10,
        )
        picker_box.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        picker_head = ctk.CTkFrame(picker_box, fg_color="transparent")
        picker_head.pack(fill="x", padx=12, pady=(10, 8))

        picker_title = ctk.CTkLabel(
            picker_head,
            text="アプリ選択（実行中アプリ）",
            text_color="#111827",
            font=("Segoe UI", 16, "bold"),
        )
        picker_title.pack(side="left")

        refresh_btn = ctk.CTkButton(
            picker_head,
            text="更新",
            width=90,
            border_width=1,
            border_color="#d4d4d8",
            command=self._refresh_app_picker,
        )
        refresh_btn.pack(side="right")

        self.app_picker_frame = ctk.CTkScrollableFrame(
            picker_box,
            fg_color="#ffffff",
            border_width=1,
            border_color="#e4e4e7",
        )
        self.app_picker_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        rules_box = ctk.CTkFrame(
            self.detail,
            fg_color="#ffffff",
            border_width=1,
            border_color="#d4d4d8",
            corner_radius=10,
        )
        rules_box.pack(fill="x", padx=16, pady=(0, 12))

        rules_title = ctk.CTkLabel(
            rules_box,
            text="現在の追加済みルール",
            text_color="#111827",
            font=("Segoe UI", 15, "bold"),
        )
        rules_title.pack(anchor="w", padx=12, pady=(10, 8))

        rules_grid = ctk.CTkFrame(rules_box, fg_color="transparent")
        rules_grid.pack(fill="x", padx=12, pady=(0, 12))

        self.allowed_box = ctk.CTkTextbox(
            rules_grid,
            width=430,
            height=110,
            border_width=1,
            border_color="#93c5fd",
            fg_color="#f8fbff",
            text_color="#0c4a6e",
        )
        self.allowed_box.pack(side="left", padx=(0, 8))

        self.blocked_box = ctk.CTkTextbox(
            rules_grid,
            width=430,
            height=110,
            border_width=1,
            border_color="#fca5a5",
            fg_color="#fff8f8",
            text_color="#7f1d1d",
        )
        self.blocked_box.pack(side="left")

        self._refresh_app_picker()
        self._refresh_rules_snapshot()

    def _build_overlay(self) -> None:
        overlay = ctk.CTkToplevel(self)
        overlay.withdraw()
        overlay.overrideredirect(True)
        overlay.attributes("-topmost", True)
        overlay.configure(fg_color="#fee2e2")

        frame = ctk.CTkFrame(
            overlay,
            fg_color="#fff1f2",
            border_width=3,
            border_color="#ef4444",
            corner_radius=0,
        )
        frame.pack(fill="both", expand=True)

        label = ctk.CTkLabel(
            frame,
            text="",
            text_color="#7f1d1d",
            justify="center",
            font=("Segoe UI", 30, "bold"),
        )
        label.place(relx=0.5, rely=0.5, anchor="center")

        self.overlay = overlay
        self.overlay_label = label

    def _show_overlay(self, message: str) -> None:
        if not self.overlay or not self.overlay_label:
            return
        width = self.winfo_screenwidth()
        height = self.winfo_screenheight()
        self.overlay.geometry(f"{width}x{height}+0+0")
        self.overlay_label.configure(text=message)
        self.overlay.deiconify()
        self.overlay.lift()

    def _hide_overlay(self) -> None:
        if self.overlay:
            self.overlay.withdraw()

    def _handle_login_click(self) -> None:
        if self._login_in_progress:
            return
        self._login_in_progress = True
        self.google_login_button.configure(state="disabled", text="ブラウザでログイン中...")
        self.update_idletasks()
        try:
            uid, email = self.on_google_login()
            self._on_login_success(uid, email)
        except Exception as exc:  # pylint: disable=broad-except
            self._on_login_failed(str(exc))

    def _on_login_success(self, uid: str, email: str) -> None:
        self._login_in_progress = False
        self.google_login_button.configure(state="normal", text="連携済み")
        self.login_label.configure(text=f"ログイン状態: {email} (uid: {uid})")

    def _on_login_failed(self, reason: str) -> None:
        self._login_in_progress = False
        self.google_login_button.configure(state="normal", text="Googleでログイン")
        self.login_label.configure(text="ログイン状態: 失敗")
        self.app_state.set_warning(f"ログイン失敗: {reason}")
        messagebox.showerror("Googleログイン失敗", reason)

    def _emoji_for_app(self, exe: str) -> str:
        value = exe.lower()
        if any(k in value for k in ["steam", "riot", "epic", "valorant", "league"]):
            return "🎮"
        if any(k in value for k in ["discord", "telegram", "line", "slack", "whatsapp"]):
            return "💬"
        if any(k in value for k in ["code", "notion"]):
            return "📘"
        return "🧩"

    def _refresh_rules_snapshot(self) -> None:
        allowed, blocked = self.on_get_rules_snapshot()
        self.allowed_box.delete("1.0", "end")
        self.blocked_box.delete("1.0", "end")

        allowed_text = "許可済み\n" + ("\n".join(allowed[:20]) if allowed else "(なし)")
        blocked_text = "ブロック済み\n" + ("\n".join(blocked[:20]) if blocked else "(なし)")
        self.allowed_box.insert("1.0", allowed_text)
        self.blocked_box.insert("1.0", blocked_text)

    def _refresh_app_picker(self) -> None:
        for child in self.app_picker_frame.winfo_children():
            child.destroy()

        apps = self.on_fetch_running_apps()
        if not apps:
            empty = ctk.CTkLabel(
                self.app_picker_frame,
                text="実行中アプリが見つかりません。",
                text_color="#374151",
                font=("Segoe UI", 13),
            )
            empty.pack(anchor="w", padx=10, pady=10)
            return

        for app in apps:
            row = ctk.CTkFrame(
                self.app_picker_frame,
                fg_color="#ffffff",
                border_width=1,
                border_color="#e4e4e7",
                corner_radius=8,
            )
            row.pack(fill="x", padx=8, pady=6)

            icon = self._emoji_for_app(app.executable)
            label = ctk.CTkLabel(
                row,
                text=f"{icon}  {app.display_name}   ({app.executable})",
                text_color="#111827",
                font=("Segoe UI", 13),
            )
            label.pack(side="left", padx=10, pady=8)

            allow_btn = ctk.CTkButton(
                row,
                text="許可",
                width=80,
                height=30,
                fg_color="#e0f2fe",
                text_color="#0c4a6e",
                border_width=1,
                border_color="#93c5fd",
                command=lambda exe=app.executable: self._allow_app(exe),
            )
            allow_btn.pack(side="right", padx=(6, 10), pady=8)

            block_btn = ctk.CTkButton(
                row,
                text="ブロック",
                width=90,
                height=30,
                fg_color="#fee2e2",
                text_color="#7f1d1d",
                border_width=1,
                border_color="#fca5a5",
                command=lambda exe=app.executable: self._block_app(exe),
            )
            block_btn.pack(side="right", padx=6, pady=8)

    def _allow_app(self, executable: str) -> None:
        self.on_allow_app(executable)
        self.app_state.set_warning(f"許可に追加: {executable}")
        self._refresh_rules_snapshot()

    def _block_app(self, executable: str) -> None:
        self.on_block_app(executable)
        self.app_state.set_warning(f"ブロックに追加: {executable}")
        self._refresh_rules_snapshot()

    def _apply_preset(self, category: str) -> None:
        count = self.on_apply_preset(category)
        self.app_state.set_warning(f"{category} プリセットを適用しました（{count}件）")
        self._refresh_rules_snapshot()

    def _refresh(self) -> None:
        snap = self.app_state.snapshot()

        if snap.is_locking:
            self.status_card.configure(fg_color="#fef2f2", border_color="#fca5a5")
            self.status_icon.configure(text="●", text_color="#b91c1c")
            self.status_label.configure(text="LOCK ON", text_color="#b91c1c")
        else:
            self.status_card.configure(fg_color="#eff6ff", border_color="#93c5fd")
            self.status_icon.configure(text="○", text_color="#1d4ed8")
            self.status_label.configure(text="LOCK OFF", text_color="#1d4ed8")

        remaining = snap.remaining_seconds
        if remaining is None or remaining < 0:
            remaining_text = "--:--"
        else:
            m, s = divmod(remaining, 60)
            remaining_text = f"{m:02d}:{s:02d}"

        self.remaining_label.configure(text=f"残り時間: {remaining_text}")
        app_text = snap.active_executable or "-"
        if snap.active_window_title:
            app_text = f"{app_text} | {snap.active_window_title[:42]}"
        self.active_app_label.configure(text=f"アクティブアプリ: {app_text}")
        self.warning_label.configure(text=snap.warning_message)

        if snap.overlay_active and snap.is_locking:
            self._show_overlay(snap.overlay_message or "STUDY LOCK ACTIVE")
        else:
            self._hide_overlay()

        self.after(300, self._refresh)
