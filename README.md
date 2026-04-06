# StudyFlow Device Lock for Windows

StudyFlowのWebタイマー状態と同期して、許可外アプリを自動で最小化するWindows向けロックアプリです。

## 実装済みコア機能

- サイト側で発行した一時ペアリングコードによるアカウント連携
- Firestoreの `users/{uid}` ドキュメント内 `status.is_timer_running` を常時監視
- ロック中は許可外の最前面アプリを即時最小化
- `taskmgr.exe` など安全除外リストを標準搭載
- ローカルFastAPIで `/remote-unlock` エンドポイント待機
- ライトモード前提の高コントラストUI（枠線つき）
- 起動直後は「ペアリングコード入力」中心のシンプルUI
- Webタイマー開始/停止をDB経由で自動同期（ローカルStart操作不要）
- 詳細設定タブにアプリ選択Picker（実行中アプリをワンクリックで許可/ブロック）
- 「ゲーム」「SNS」カテゴリの一括ブロックプリセット

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

5. 事前チェック

```powershell
./scripts/preflight_check.ps1
```

6. 実行

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
- `LOCK_ENFORCEMENT_MODE` (`minimize` / `overlay` / `both`)
- `PAIRING_API_BASE_URL`
- `PAIRING_API_PATH`

## リモート解除API

- エンドポイント: `POST /remote-unlock`
- JSON: `{ "uid": "<firebase uid>", "secret": "<REMOTE_UNLOCK_SECRET>" }`
- 成功時: 一定時間ロック解除

## 実機確認手順（1）

1. StudyFlow Webでタイマーを開始する
2. アプリのステータスが `LOCKING` に変わることを確認
3. ホワイトリスト外アプリを前面に出す
4. `.env` の `LOCK_ENFORCEMENT_MODE=overlay` または `both` のとき、全画面警告オーバーレイが表示されることを確認
5. 同時に `minimize` が有効なら対象アプリが最小化されることを確認

## UI / UX

- メイン画面:
	- 「ペアリングコード入力」
	- LOCK ON / OFF の大きな状態表示（色とアイコン）
	- 残り時間 / アクティブアプリ表示
- 詳細設定:
	- 実行中アプリPicker（許可 / ブロック）
	- カテゴリプリセット（ゲーム / SNS）

## One-Click EXE化

```powershell
pip install pyinstaller
pyinstaller --onefile --windowed --name studyflow-lock main.py
```

生成物: `dist/studyflow-lock.exe`

## インストーラー作成（ローカル）

```powershell
./scripts/build_release_installer.ps1 -Version 0.2.0
```

生成物: `dist/StudyFlow-Lock-Setup.exe`

補足:

- EXEは `--windowed` でビルドされるため、起動時にコマンドプロンプトは表示されません。
- 起動失敗時はエラーダイアログを表示し、詳細ログを `%LOCALAPPDATA%\StudyFlowDeviceLock\startup-error.log` に出力します。
- 既にインストール済みの場合、同じ `AppId` を使ってアップデートとして実行されます（`.env` と `whitelist.json` は保持）。

## GitHub Releaseへ自動掲載

- ワークフロー: `.github/workflows/release-installer.yml`
- `v0.2.0` のようなタグをpushすると、以下を自動でReleaseへ添付します。
	- `studyflow-lock.exe`
	- `StudyFlow-Lock-Setup.exe`

例:

```powershell
git tag v0.2.0
git push origin v0.2.0
```

## 自動アップデート

- 起動中に GitHub Releases の最新バージョンを確認します。
- 最新版があればインストーラーを自動ダウンロードしてサイレント実行します。
- 既定設定は `.env` の以下で調整できます。
	- `APP_VERSION`
	- `GITHUB_REPO`
	- `AUTO_UPDATE_ENABLED`
	- `AUTO_UPDATE_CHECK_INTERVAL_HOURS`

## スタートアップ常駐（簡易）

Windowsスタートアップフォルダに `studyflow-lock.exe` のショートカットを置くと、PC起動時に自動起動できます。

`Win + R` → `shell:startup`
