import json
import os
import sys

def get_base_path():
    """実行ファイル（またはスクリプト）のあるディレクトリを返す"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def load_config(config_file):
    if not os.path.exists(config_file):
        return None
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

# ローカルモジュールのインポート
from history_manager import HistoryManager
from semantic_scholar_fetcher import SemanticScholarFetcher
from i18n import I18n

def main():
    base_path = get_base_path()
    config_path = os.path.join(base_path, 'config.json')

    config = load_config(config_path)
    if not config:
        print("設定ファイルが見つかりません。先に ronbun_checker または config_editor を実行して設定を行ってください。")
        return

    language = config.get('language', 'ja')
    i18n = I18n(language)

    print(i18n.t("prefetch.starting"))

    history_mgr = HistoryManager(
        db_file=os.path.join(base_path, 'history.db'),
        history_json=os.path.join(base_path, 'history.json'),
        pending_json=os.path.join(base_path, 'pending.json')
    )

    # 1. 保留中の記事を取得
    pending_entries = history_mgr.get_pending_entries()
    
    # Semantic Scholarのフェッチャー初期化
    ss_api_key       = config.get('semantic_scholar_api_key', '')
    ss_interval      = config.get('semantic_scholar_interval_sec', 1.5)
    ss_max_attempts  = config.get('semantic_scholar_max_attempts', 20)
    min_abstract_length = config.get('min_abstract_length', 50)

    semantic_fetcher = SemanticScholarFetcher(
        api_key=ss_api_key,
        request_interval_sec=ss_interval
    )

    # Abstractがまだない論文のみ抽出
    abstract_missing_entries = [e for e in pending_entries if not e.get('abstract') and e.get('title')]
    
    if not abstract_missing_entries:
        print(i18n.t("prefetch.no_pending"))
        return

    print(i18n.t("prefetch.start", count=len(abstract_missing_entries)))

    processed_count = 0
    for entry in abstract_missing_entries:
        if semantic_fetcher._call_count >= ss_max_attempts:
            print(i18n.t("prefetch.limit_reached", limit=ss_max_attempts))
            break
        
        abstract = semantic_fetcher.fetch_abstract(
            entry['title'],
            min_abstract_len=min_abstract_length
        )

        if abstract:
            print(i18n.t("prefetch.success", title=entry['title']))
            history_mgr.update_abstract(entry['link'], abstract)
            processed_count += 1
        else:
            print(i18n.t("prefetch.fallback", title=entry['title']))

    print(i18n.t("prefetch.done", count=processed_count))

if __name__ == "__main__":
    main()
    
    # EXEモードの場合、画面が自動で閉じないようにする（設定による）
    if getattr(sys, 'frozen', False):
        base_path = get_base_path()
        config_path = os.path.join(base_path, 'config.json')
        wait = True
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    wait = config.get('wait_on_exit', True)
            except Exception:
                pass

        if wait:
            input("\n終了するにはEnterキーを押してください...")
