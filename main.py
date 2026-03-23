import json
import time
import os
import sys
import subprocess

def get_base_path():
    """実行ファイル（またはスクリプト）のあるディレクトリを返す"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------
# Playwrightのインポート前にブラウザパスを環境変数として設定する
# （インポート後に設定するとPlaywright内部でパスが確定してしまい見失うため）
# ---------------------------------------------------------
_pw_browsers_path = os.path.join(get_base_path(), 'playwright_browsers')
if os.path.exists(_pw_browsers_path):
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = _pw_browsers_path

from history_manager import HistoryManager
from rss_fetcher import RSSFetcher
from abstract_fetcher import AbstractFetcher, BotDetectedError
from gemini_analyzer import GeminiAnalyzer, GeminiRateLimitError
from notifier import Notifier

def load_config(config_file):
    if not os.path.exists(config_file):
        return None
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    base_path = get_base_path()
    config_path = os.path.join(base_path, 'config.json')
    
    config = load_config(config_path)
    if config is None:
        print(f"Error: configuration file not found at {config_path}")
        print("Starting config_editor for initial setup...")
        
        if getattr(sys, 'frozen', False):
            editor_path = os.path.join(base_path, 'config_editor.exe')
            cmd = [editor_path, '--initial-setup']
        else:
            editor_path = os.path.join(base_path, 'config_editor.py')
            cmd = [sys.executable, editor_path, '--initial-setup']
            
        if os.path.exists(editor_path):
            subprocess.run(cmd)
            config = load_config(config_path)
            if config is None:
                print("Configuration not completed. Exiting.")
                return
        else:
            print("config_editor not found. Please create config.json manually.")
            return

    language = config.get('language', 'ja')


    # メッセージの定義
    msgs = {
        'ja': {
            'starting': "Ronbun Checker (Delayed Evaluation Mode) 起動中...",
            'rss_check': "Step 1: RSSフィードから新着記事をチェック中...",
            'no_pending': "現在、保留中（Abstract待ち）の記事はありません。",
            'pending_count': "Step 2: 保留中の {} 件についてAbstractの取得を試みます...",
            'limit_reached': "解析成功上限({}件)に達しました。残りは次回に回します。",
            'tried_limit': "試行上限({}件)に達しました。Google Scholar保護のため本日のアクセスを終了します。",
            'processing': "-- 処理中の進捗 (試行:{}/{}, 成功:{}/{}): {} --",
            'scholar_no_resp': "\nCRITICAL: Google Scholar 応答なし（CAPTCHA待ちの可能性が高い）\n安全のため本日の処理を中断します。",
            'abs_success': "Abstract取得成功: {}",
            'gemini_limit': "\n!!!! {} !!!!\nGeminiのクォータ上限に達しました。本日の処理を中断します。",
            'relevant': "関連あり！通知します。",
            'not_relevant': "関連なし。",
            'not_registered': "まだGoogle Scholarに未登録のようです: {}",
            'done': "すべての処理が完了しました。"
        },
        'en': {
            'starting': "Ronbun Checker (Delayed Evaluation Mode) Starting...",
            'rss_check': "Step 1: Checking for new articles from RSS feeds...",
            'no_pending': "No pending articles (waiting for abstract) at the moment.",
            'pending_count': "Step 2: Attempting to fetch abstracts for {} pending articles...",
            'limit_reached': "Analysis success limit ({} articles) reached. Remaining will be processed next time.",
            'tried_limit': "Attempt limit ({} articles) reached. Ending access for today to protect Google Scholar.",
            'processing': "-- Processing Progress (Attempt:{}/{}, Success:{}/{}): {} --",
            'scholar_no_resp': "\nCRITICAL: No response from Google Scholar (likely waiting for CAPTCHA)\nInterrupting process for today for safety.",
            'abs_success': "Abstract fetch success: {}",
            'gemini_limit': "\n!!!! {} !!!!\nGemini quota limit reached. Interrupting process for today.",
            'relevant': "Relevant! Notifying.",
            'not_relevant': "Not relevant.",
            'not_registered': "Not yet registered in Google Scholar: {}",
            'done': "All processes completed."
        }
    }
    m = msgs.get(language, msgs['ja'])

    print(m['starting'])
    
    history_mgr = HistoryManager(
        db_file=os.path.join(base_path, 'history.db'),
        history_json=os.path.join(base_path, 'history.json'),
        pending_json=os.path.join(base_path, 'pending.json')
    )
    rss_fetcher = RSSFetcher(config['rss_urls'])
    abstract_fetcher = AbstractFetcher(config=config)
    analyzer = GeminiAnalyzer(
        config['gemini_api_key'], 
        config['keywords'],
        model_id=config.get('gemini_model', 'gemini-3.1-flash-lite-preview'),
        language=language
    )
    notifier = Notifier(config['discord_webhook_url'], language=language)

    # 1. RSSから新しい記事を収穫し、pendingに追加
    print(m['rss_check'])
    latest_rss_entries = rss_fetcher.fetch_new_entries(history_mgr)
    for entry in latest_rss_entries:
        history_mgr.add_to_pending(entry)
    
    # 期限切れの整理
    pending_item_expire_days = config.get('pending_item_expire_days', 30)
    history_mgr.cleanup_expired(days=pending_item_expire_days)
    history_mgr.save()

    # 2. 保留中の記事に対してAbstract取得とGemini評価を行う
    pending_entries = history_mgr.get_pending_entries()
    
    if not pending_entries:
        print(m['no_pending'])
    else:
        print(m['pending_count'].format(len(pending_entries)))
        
        # 1回の実行での制限
        max_analysis_success_count = config.get('max_analysis_success_count', 5)
        max_scholar_access_attempts = config.get('max_scholar_access_attempts', 10)
        scholar_search_timeout_sec = config.get('scholar_search_timeout_sec', 30)
        interval_after_success_sec = config.get('interval_after_success_sec', 10)
        interval_after_notfound_sec = config.get('interval_after_notfound_sec', 20)
        min_abstract_length = config.get('min_abstract_length', 50)
        scholar_search_year_range = config.get('scholar_search_year_range', 1)
        
        processed_count = 0
        tried_count = 0
        
        import threading
        
        for entry in pending_entries:
            if processed_count >= max_analysis_success_count:
                print(m['limit_reached'].format(max_analysis_success_count))
                break
            if tried_count >= max_scholar_access_attempts:
                print(m['tried_limit'].format(max_scholar_access_attempts))
                break
                
            tried_count += 1
            print(m['processing'].format(tried_count, max_scholar_access_attempts, processed_count, max_analysis_success_count, entry['title']))
            
            # Google Scholar検索（タイムアウト付き）
            abstract = None
            def fetch_with_timeout():
                nonlocal abstract
                try:
                    abstract = abstract_fetcher.fetch_abstract(
                        entry['title'], 
                        source_url=entry['link'],
                        year_range=scholar_search_year_range,
                        min_abstract_len=min_abstract_length
                    )
                except BotDetectedError as be:
                    print(f"\n!!!! {be} !!!!")
                    entry['bot_error'] = be

            fetch_thread = threading.Thread(target=fetch_with_timeout)
            fetch_thread.start()
            fetch_thread.join(timeout=scholar_search_timeout_sec)
            
            if fetch_thread.is_alive():
                print(m['scholar_no_resp'])
                break
            
            if 'bot_error' in entry:
                break
            
            if abstract:
                print(m['abs_success'].format(entry['title']))
                processed_count += 1
                
                # Geminiで解析
                entry['summary'] = abstract
                try:
                    is_relevant, reason, summarized_abstract = analyzer.analyze_entry(entry)
                except GeminiRateLimitError as ge:
                    print(m['gemini_limit'].format(ge))
                    break
                
                if is_relevant:
                    print(m['relevant'])
                    notifier.notify(entry, reason, summarized_abstract)
                else:
                    print(m['not_relevant'])
                
                # 関連性に関わらず、解析済みの詳細情報を保存して完了とする
                history_mgr.mark_completed(
                    entry['link'],
                    title=entry['title'],
                    abstract=abstract,
                    is_relevant=is_relevant,
                    reason=reason,
                    jp_abstract=summarized_abstract
                )
                time.sleep(interval_after_success_sec)
            else:
                print(m['not_registered'].format(entry['title']))
                history_mgr.move_to_end(entry['link'])
                time.sleep(interval_after_notfound_sec)

        # SQLite版では個別のsave()は不要だが、インターフェース維持のため呼び出しは残す（中身はpass）
        history_mgr.save()
    
    print(m['done'])

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
