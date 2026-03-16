import json
import time
from history_manager import HistoryManager
from rss_fetcher import RSSFetcher
from abstract_fetcher import AbstractFetcher, BotDetectedError
from gemini_analyzer import GeminiAnalyzer, GeminiRateLimitError
from notifier import Notifier

def load_config(config_file='config.json'):
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    print("Ronbun Checker (Delayed Evaluation Mode) 起動中...")
    config = load_config()
    
    history_mgr = HistoryManager()
    rss_fetcher = RSSFetcher(config['rss_urls'])
    abstract_fetcher = AbstractFetcher(config=config)
    analyzer = GeminiAnalyzer(
        config['gemini_api_key'], 
        config['keywords'],
        model_id=config.get('gemini_model', 'gemini-3.1-flash-lite-preview')
    )
    notifier = Notifier(config['discord_webhook_url'])

    # 1. RSSから新しい記事を収穫し、pendingに追加
    print("Step 1: RSSフィードから新着記事をチェック中...")
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
        print("現在、保留中（Abstract待ち）の記事はありません。")
    else:
        print(f"Step 2: 保留中の {len(pending_entries)} 件についてAbstractの取得を試みます...")
        
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
                print(f"解析成功上限({max_analysis_success_count}件)に達しました。残りは次回に回します。")
                break
            if tried_count >= max_scholar_access_attempts:
                print(f"試行上限({max_scholar_access_attempts}件)に達しました。Google Scholar保護のため本日のアクセスを終了します。")
                break
                
            tried_count += 1
            print(f"-- 処理中 (試行:{tried_count}/{max_scholar_access_attempts}, 成功:{processed_count}/{max_analysis_success_count}): {entry['title']} --")
            
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
                print("\nCRITICAL: Google Scholar 応答なし（CAPTCHA待ちの可能性が高い）")
                print("安全のため本日の処理を中断します。")
                break
            
            if 'bot_error' in entry:
                break
            
            if abstract:
                print(f"Abstract取得成功: {entry['title']}")
                processed_count += 1
                
                # Geminiで解析
                entry['summary'] = abstract
                try:
                    is_relevant, reason, jp_abstract = analyzer.analyze_entry(entry)
                except GeminiRateLimitError as ge:
                    print(f"\n!!!! {ge} !!!!")
                    print("Geminiのクォータ上限に達しました。本日の処理を中断します。")
                    break
                
                if is_relevant:
                    print("関連あり！通知します。")
                    notifier.notify(entry, reason, jp_abstract)
                else:
                    print("関連なし。")
                
                history_mgr.mark_completed(entry['link'])
                time.sleep(interval_after_success_sec)
            else:
                print(f"まだGoogle Scholarに未登録のようです: {entry['title']}")
                history_mgr.move_to_end(entry['link'])
                time.sleep(interval_after_notfound_sec)

        history_mgr.save()
    
    print("すべての処理が完了しました。")

if __name__ == "__main__":
    main()
