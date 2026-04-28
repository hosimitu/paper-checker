"""
SemanticScholarFetcher
======================
Semantic Scholar Academic Graph API を使って論文のAbstractを取得するモジュール。

API仕様:
    エンドポイント: GET /graph/v1/paper/search
    URL: https://api.semanticscholar.org/graph/v1/paper/search
    レート制限 (APIキーあり): 1 req/sec
    フィールド指定: fields=title,abstract,year

過負荷防止のための設計ポイント:
    - リクエスト間隔を最低 1.0 秒に強制 (APIの制限が 1 req/sec のため)
    - 1実行あたりの最大呼び出し回数を設定可能
    - タイムアウト 10 秒でHTTPリクエストを切り捨て
    - HTTP 429 受信時は即座にフォールバック扱いとして None を返す（アプリを止めない）
"""

import time
import requests
from abstract_fetcher import clean_title, simplify_for_comparison

# Semantic Scholar API のベースURL
_API_BASE = "https://api.semanticscholar.org/graph/v1"
# HTTPリクエストのタイムアウト（秒）
_REQUEST_TIMEOUT = 10


class SemanticScholarFetcher:
    """Semantic Scholar APIを用いてAbstractを取得するクラス。"""

    def __init__(self, api_key: str = "", request_interval_sec: float = 1.5):
        """
        Parameters
        ----------
        api_key : str
            Semantic Scholar API キー。空文字の場合はキーなし（共有レート制限）で動作。
        request_interval_sec : float
            リクエスト間の待機秒数。APIの制限 (1 req/sec) を下回らないよう
            最低 1.0 秒に強制する。
        """
        self.api_key = api_key.strip() if api_key else ""
        # 1秒未満への設定は許可しない（APIレート制限遵守）
        self.request_interval_sec = max(1.0, request_interval_sec)
        self._call_count = 0  # 今回の実行での累計呼び出し回数

    def reset_call_count(self):
        """呼び出し回数カウンターをリセットする（テスト等で使用）。"""
        self._call_count = 0

    def fetch_abstract(
        self,
        title: str,
        min_abstract_len: int = 50,
    ) -> str | None:
        """
        タイトルで Semantic Scholar を検索し、一致する論文のAbstractを返す。

        Parameters
        ----------
        title : str
            検索するタイトル文字列。
        min_abstract_len : int
            Abstractの最小文字数。これ未満の場合は None を返す。

        Returns
        -------
        str | None
            取得できたAbstract文字列、取得できなかった場合は None。
        """
        query = clean_title(title)
        if not query:
            return None

        # ヘッダー設定（APIキーがある場合のみ付与）
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        params = {
            "query": query,
            "fields": "title,abstract,year",
            "limit": 3,  # 上位3件のみ取得（最小限のデータ）
        }

        try:
            response = requests.get(
                f"{_API_BASE}/paper/search",
                headers=headers,
                params=params,
                timeout=_REQUEST_TIMEOUT,
            )
            self._call_count += 1

            if response.status_code == 429:
                # レート制限超過 → Googleフォールバックに任せる
                print("[Semantic Scholar] レート制限 (429) 受信。Google Scholarへフォールバックします。")
                return None

            if response.status_code != 200:
                print(f"[Semantic Scholar] APIエラー (HTTP {response.status_code})。Google Scholarへフォールバックします。")
                return None

            data = response.json()
            candidates = data.get("data", [])

            if not candidates:
                return None

            # タイトル類似チェック
            sim_query = simplify_for_comparison(query)
            for paper in candidates:
                paper_title = paper.get("title", "")
                abstract = paper.get("abstract") or ""

                sim_paper = simplify_for_comparison(paper_title)
                # 片方がもう片方の部分文字列として含まれているか確認
                if sim_query in sim_paper or sim_paper in sim_query:
                    if len(abstract) >= min_abstract_len:
                        return abstract

            # 一致する論文が見つからなかった
            return None

        except requests.exceptions.Timeout:
            print("[Semantic Scholar] タイムアウト。Google Scholarへフォールバックします。")
            return None
        except Exception as e:
            print(f"[Semantic Scholar] 予期しないエラー: {e}。Google Scholarへフォールバックします。")
            return None
        finally:
            # レート制限遵守のためのインターバル（成功・失敗に関わらず待機）
            time.sleep(self.request_interval_sec)
