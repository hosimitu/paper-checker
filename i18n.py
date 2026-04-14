import json
import os
import sys

# 翻訳ファイルが見つからない場合のフォールバック言語
FALLBACK_LANGUAGE = "en"


def _get_locales_dir() -> str:
    """ロケールファイルのディレクトリを返す（EXE化対応）"""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'locales')


class I18n:
    """
    JSONファイルベースの国際化（i18n）クラス。

    locales/{lang}.json から翻訳文字列を読み込み、
    ドット記法でキーを指定して取得する。

    例:
        i18n = I18n("ja")
        i18n.t("main.starting")
        i18n.t("main.pending_count", count=5)

    指定した言語のキーが見つからない場合は FALLBACK_LANGUAGE (en) を使用する。
    """

    def __init__(self, language: str = FALLBACK_LANGUAGE):
        self._language = language
        self._strings: dict = {}
        self._fallback: dict = {}
        self._load()

    def _load_file(self, lang: str) -> dict:
        """指定言語のJSONファイルを読み込む。ファイルが存在しない場合は空の辞書を返す。"""
        path = os.path.join(_get_locales_dir(), f"{lang}.json")
        if not os.path.exists(path):
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[i18n] ロケールファイルの読み込みに失敗しました '{path}': {e}")
            return {}

    def _load(self):
        """現在の言語とフォールバック言語を読み込む。"""
        self._strings = self._load_file(self._language)
        if self._language != FALLBACK_LANGUAGE:
            self._fallback = self._load_file(FALLBACK_LANGUAGE)
        else:
            self._fallback = {}

    def set_language(self, language: str):
        """言語を動的に切り替える（config_editor のUI切り替えに使用）。"""
        self._language = language
        self._load()

    def t(self, key: str, **kwargs) -> str:
        """
        ドット記法でキーを指定して翻訳文字列を取得する。

        キーが見つからない場合はフォールバック言語 (en) を使用し、
        それも見つからない場合はキー自体を返す。

        Args:
            key: ドット区切りのキー (例: "main.starting")
            **kwargs: 文字列内の名前付きプレースホルダーに渡す値

        Returns:
            翻訳済み文字列。フォーマット引数がある場合は適用済みのものを返す。
        """
        value = self._get_nested(self._strings, key)
        if value is None:
            value = self._get_nested(self._fallback, key)
        if value is None:
            return key  # どの言語にも見つからない場合はキー自体を返す
        if kwargs:
            try:
                return value.format(**kwargs)
            except KeyError:
                return value
        return value

    def _get_nested(self, data: dict, key: str):
        """ドット区切りのキーでネストされた辞書から値を取得する。"""
        keys = key.split('.')
        current = data
        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return None
            current = current[k]
        return current

    @staticmethod
    def available_languages() -> list:
        """
        利用可能な言語コード一覧を返す。
        locales/ ディレクトリ内の .json ファイルを自動検出する。
        """
        locales_dir = _get_locales_dir()
        if not os.path.exists(locales_dir):
            return [FALLBACK_LANGUAGE]
        return sorted(
            os.path.splitext(f)[0]
            for f in os.listdir(locales_dir)
            if f.endswith('.json')
        )
