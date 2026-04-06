# StudyFlow Device Lock for Windows

StudyFlowのWebタイマー状態と同期して、許可外アプリを自動で最小化するWindows向けロックアプリです。

## 実装済みコア機能

- Googleログイン（ブラウザ起動）
- GoogleメールをFirebase Authに照合して同一ユーザーのUIDを解決
- Firestoreの `users/{uid}` ドキュメント内 `status.is_timer_running` を常時監視
- ロック中は許可外の最前面アプリを即時最小化
- `taskmgr.exe` など安全除外リストを標準搭載
- ローカルFastAPIで `/remote-unlock` エンドポイント待機
- ライトモード前提の高コントラストUI（枠線つき）
- メイン画面は「ログイン状態」「状態」「残り時間」「スタート/ストップ」のみに整理
- ホワイトリスト編集は「詳細設定」タブに隔離

## セットアップ

1. Python 3.11+ をインストール
2. 依存関係を導入

```powershell
pip install -r requirements.txt
```

3. 設定ファイルを作成

```powershell
Copy-Item .env.example .env
```

4. 次のファイルを配置
- `service-account.json` (Firebase Admin SDK)
- `oauth-client-secret.json` (Google OAuth Desktop)

5. 実行

```powershell
python main.py
```

## Firestoreフォーマット

既定では次のパスとフィールドを監視します。

- ドキュメント: `users/{uid}`
- 実行フラグ: `status.is_timer_running`
- 残り秒数: `status.remaining_seconds`

必要なら `.env` の以下を変更してください。

- `FIRESTORE_TIMER_DOC_PATH_TEMPLATE`
- `FIRESTORE_TIMER_FIELD_PATH`
- `FIRESTORE_TIMER_REMAINING_PATH`

## リモート解除API

- エンドポイント: `POST /remote-unlock`
- JSON: `{ "uid": "<firebase uid>", "secret": "<REMOTE_UNLOCK_SECRET>" }`
- 成功時: 一定時間ロック解除

## One-Click EXE化

```powershell
pip install pyinstaller
pyinstaller --onefile --name studyflow-lock main.py
```

生成物: `dist/studyflow-lock.exe`

## スタートアップ常駐（簡易）

Windowsスタートアップフォルダに `studyflow-lock.exe` のショートカットを置くと、PC起動時に自動起動できます。

`Win + R` → `shell:startup`
