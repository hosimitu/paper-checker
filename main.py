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
    abstract_fetcher = AbstractFetcher()
    analyzer = GeminiAnalyzer(config['gemini_api_key'], config['keywords'])
    notifier = Notifier(config['discord_webhook_url'])

    # 1. RSSから新しい記事を収穫し、pendingに追加
    print("Step 1: RSSフィードから新着記事をチェック中...")
    latest_rss_entries = rss_fetcher.fetch_new_entries(history_mgr)
    for entry in latest_rss_entries:
        history_mgr.add_to_pending(entry)
    
    # 期限切れ(30日)の整理
    history_mgr.cleanup_expired(days=30)
    history_mgr.save()

    # 2. 保留中の記事に対してAbstract取得とGemini評価を行う
    pending_entries = history_mgr.get_pending_entries()
    
    if not pending_entries:
        print("現在、保留中（Abstract待ち）の記事はありません。")
    else:
        print(f"Step 2: 保留中の {len(pending_entries)} 件についてAbstractの取得を試みます...")
        
        # 1回の実行での解析制限 (RPDを考慮)
        limit = 5
        processed_count = 0
        
        import threading
        
        for entry in pending_entries:
            if processed_count >= limit:
                print(f"1回あたりの解析上限({limit}件)に達しました。残りは次回に回します。")
                break
                
            print(f"-- 処理中 ({processed_count + 1}/{limit}): {entry['title']} --")
            
            # Google Scholar検索（タイムアウト付き）
            abstract = None
            def fetch_with_timeout():
                nonlocal abstract
                try:
                    abstract = abstract_fetcher.fetch_abstract(entry['title'], source_url=entry['link'])
                except BotDetectedError as be:
                    print(f"\n!!!! {be} !!!!")
                    # 例外を外に伝えるためにグローバル（またはnonlocal）で保持
                    entry['bot_error'] = be

            fetch_thread = threading.Thread(target=fetch_with_timeout)
            fetch_thread.start()
            fetch_thread.join(timeout=30) # 30秒待っても終わらなければCAPTCHA待ちと判断
            
            if fetch_thread.is_alive():
                print("\nCRITICAL: Google Scholar 応答なし（CAPTCHA待ちの可能性が高い）")
                print("安全のため本日の処理を中断します。")
                break
            
            if 'bot_error' in entry:
                break # Bot検知例外が出た場合も中断
            
            if abstract:
                print(f"Abstract取得成功: {entry['title']}")
                processed_count += 1
                
                # Geminiで解析
                entry['summary'] = abstract # RSSのメタデータではなく取得したAbstractをセット
                try:
                    is_relevant, reason, jp_abstract = analyzer.analyze_entry(entry)
                except GeminiRateLimitError as ge:
                    print(f"\n!!!! {ge} !!!!")
                    print("Geminiのクォータ上限に達しました。本日の処理を中断します。")
                    break # ループを中断
                
                if is_relevant:
                    print("関連あり！通知します。")
                    notifier.notify(entry, reason, jp_abstract)
                else:
                    print("関連なし。")
                
                # 処理完了（履歴へ移動）
                history_mgr.mark_completed(entry['link'])
                time.sleep(10) # APIレート制限用
            else:
                print(f"まだGoogle Scholarに未登録のようです: {entry['title']}")
                time.sleep(20)

        history_mgr.save()
    
    print("すべての処理が完了しました。")

if __name__ == "__main__":
    main()
