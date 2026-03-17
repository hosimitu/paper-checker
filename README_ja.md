# Paper Checker (論文チェッカー)
<table>
    <thead>
        <tr>
            <th style="text-align:center"><a href="README.md">English</a></th>
            <th style="text-align:center">日本語</th>
        </tr>
    </thead>
</table>

指定されたRSSフィードから最新の論文情報を取得し、Gemini APIを用いてユーザーの設定したキーワードとの関連性を自動判定するシステムです。
関連性が高いと判断された論文のみ、DiscordのWebhook経由で通知されます。

## 主な特徴

*   **遅延評価アーキテクチャ**: RSSで取得したばかりの最新論文は、Google Scholarにインデックスされるまで「保留」扱いとし、要旨(Abstract)が取得可能になったタイミングで高精度な判定を行います。
*   **Geminiによる高精度判定**: タイトルと要旨をセットでGeminiに渡し、キーワードの単純一致だけでなく文脈を解釈して関連性を判定します。また、同時に関連論文の日本語要旨も生成します。
*   **Discord Embedsによる通知**: Discordの「埋め込み」形式を利用したリッチな通知に対応。長い内容も分割して読みやすく表示します。
*   **重複防止**: 一度処理した（通知した、または関連なしと判定した）論文は記録され、二度と処理されません。
*   **フェイルセーフと自動介入**: Google ScholarのBot検知を回避するロジックを搭載。万が一ブロックされた場合でも、自動的にブラウザを表示してユーザーが手動でキャプチャを解除し、処理を続行することが可能です。
*   **セッションの永続化**: 一度キャプチャを解除した状態を保存・再利用するため、頻繁に介入を求められることなくスムーズに動作します。

## 必須要件

*   Python 3.x
*   (推奨) 仮想環境 (venv など)

## セットアップ手順

1.  **リポジトリのクローン・配置**
    任意のディレクトリにプロジェクトを配置します。

2.  **依存ライブラリのインストール**
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```

3.  **設定ファイルの準備**
    `config.json` を作成し、以下のように設定を記述します。（※ `.gitignore` に登録されているため、Gitにはコミットされません。もし存在しない場合はテンプレートから手動で作成してください）

    ```json
    {
        "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL",
        "gemini_api_key": "YOUR_GEMINI_API_KEY",
        "gemini_model": "gemini-3.1-flash-lite-preview",
        "keywords": ["membrane", "CO2 separation"],
        "rss_urls": ["RSS URL for the journal"],

        "max_analysis_success_count": 5,
        "max_scholar_access_attempts": 10,
        "scholar_search_timeout_sec": 30,
        "use_playwright": true,
        "manual_captcha_timeout_sec": 120,
        "playwright_user_data_dir": ".playwright_data",
        "interval_after_success_sec": 10,
        "interval_after_notfound_sec": 20,
        "pending_item_expire_days": 30,
        "min_abstract_length": 50,
        "scholar_search_year_range": 1
    }
    ```

    各項目の詳細は以下の通りです。

    | 項目名                        | 説明                                                                 | デフォルト値                    |
    | ----------------------------- | -------------------------------------------------------------------- | ------------------------------- |
    | `discord_webhook_url`         | 通知を送信する Discord Webhook URL                                   | -                               |
    | `gemini_api_key`              | Google Gemini API のキー                                             | -                               |
    | `gemini_model`                | 使用する Gemini モデル ID                                            | `gemini-3.1-flash-lite-preview` |
    | `keywords`                    | 関連性を判定するためのキーワードリスト                               | -                               |
    | `rss_urls`                    | 購読する RSS フィードの URL リスト                                   | -                               |
    | `max_analysis_success_count`  | 1回の実行で解析（通知）を成功させる最大件数                          | `5`                             |
    | `max_scholar_access_attempts` | 1回の実行で Google Scholar へアクセスを試みる最大件数                | `10`                            |
    | `scholar_search_timeout_sec`  | Google Scholar 検索の応答待ちタイムアウト（秒）                      | `30`                            |
    | `use_playwright`              | Playwright による高精度取得・キャプチャ対応を有効にするか            | `true`                          |
    | `manual_captcha_timeout_sec`  | キャプチャ解除を待機する最大時間（秒）                               | `120`                           |
    | `playwright_user_data_dir`    | ブラウザのセッション情報を保存するディレクトリ                       | `.playwright_data`              |
    | `interval_after_success_sec`  | 1件解析が成功した後の待機時間。Bot検知回避用                         | `10`                            |
    | `interval_after_notfound_sec` | Scholarに登録されていなかった場合の待機時間                          | `20`                            |
    | `pending_item_expire_days`    | 記事が保留されてから自動破棄（未処理として処理済みへ）するまでの日数 | `30`                            |
    | `min_abstract_length`         | 解析を試みる最低限の要旨(Abstract)文字数                             | `50`                            |
    | `scholar_search_year_range`   | Scholar検索で対象とする「現在から遡る年数」                          | `1`                             |

## 使い方

以下のコマンド、またはバッチファイルを実行してください。

```bash
python main.py
```
または
```cmd
run_checker.bat
```

**運用のおすすめ**
Windowsの「タスク スケジューラ」などを利用して、`run_checker.bat` を1日1回などの頻度で定期実行するように設定してください。

## ファイル構成

*   `main.py`: メイン処理プログラム
*   `rss_fetcher.py`: RSSから記事のタイトルとリンクを取得するモジュール
*   `abstract_fetcher.py`: Google Scholarから要旨(Abstract)を取得するモジュール
*   `gemini_analyzer.py`: Gemini APIを利用して関連性を判定・日本語訳を生成するモジュール
*   `history_manager.py`: 処理履歴や保留中のデータを管理するモジュール (SQLite)
*   `notifier.py`: Discordへリッチな通知を送信するモジュール
*   `run_checker.bat`: 実行用のバッチファイル
*   `config.json`: (ユーザー作成) APIキーやキーワードの設定ファイル
*   `history.db`: (自動生成) 処理済みデータや保留データを保存するSQLiteデータベース

## 注意事項
*   Gemini APIおよびGoogle Scholarのレート制限に配慮した設計になっています。もしGoogle Scholarでブロックされた場合は、自動でブラウザが立ち上がりますのでメッセージに従ってキャプチャを解除してください。
*   一度キャプチャを解除すれば、設定したディレクトリ（デフォルト `.playwright_data`）にセッション情報が保存され、次回以降のキャプチャ要求が抑制されます。
*   `config.json`, `history.db`, `.env` などの機密情報やローカルデータは自動的にGitの管理から除外 (`.gitignore` 参照) されます。
*   既存の `history.json` や `pending.json` がある場合、初回実行時に自動的に `history.db` への移行が行われ、元のファイルは `.bak` としてバックアップされます。
