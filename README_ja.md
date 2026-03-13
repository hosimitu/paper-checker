# Ronbun Checker (論文チェッカー)
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
*   **フェイルセーフ**: Google ScholarのBot検知やGeminiのレート制限を検知した場合、安全に処理を中断し、IPブロックの悪化を防ぎます。

## 必須要件

*   Python 3.x
*   (推奨) 仮想環境 (venv など)

## セットアップ手順

1.  **リポジトリのクローン・配置**
    任意のディレクトリにプロジェクトを配置します。

2.  **依存ライブラリのインストール**
    ```bash
    pip install -r requirements.txt
    ```

3.  **設定ファイルの準備**
    `config.json` を作成し、以下のように設定を記述します。（※ `.gitignore` に登録されているため、Gitにはコミットされません。もし存在しない場合はテンプレートから手動で作成してください）

    ```json
    {
        "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL",
        "gemini_api_key": "YOUR_GEMINI_API_KEY",
        "keywords": [
            "membrane",
            "CO2 separation"
        ],
        "rss_urls": [
            "RSS URL for the journal"
        ]
    }
    ```

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
*   `abstract_fetcher.py`: `scholarly` を利用してGoogle Scholarから要旨(Abstract)を取得するモジュール
*   `gemini_analyzer.py`: Gemini APIを利用して関連性を判定・日本語訳を生成するモジュール
*   `history_manager.py`: 処理済み(`history.json`)や保留中(`pending.json`)のデータを管理するモジュール
*   `notifier.py`: Discordへリッチな通知を送信するモジュール
*   `run_checker.bat`: 実行用のバッチファイル
*   `config.json`: (ユーザー作成) APIキーやキーワードの設定ファイル

## 注意事項
*   Gemini APIおよびGoogle Scholarのレート制限に配慮した設計になっています。もし短時間に大量の記事を処理してブロックされた場合は、メッセージに従い数時間空けてから再開してください。
*   `config.json`, `history.json`, `pending.json`, `.env` などの機密情報やローカルデータは自動的にGitの管理から除外 (`.gitignore` 参照) されます。
