import json
import time
import os
import sys
import subprocess
import random

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
from abstract_fetcher import AbstractFetcher, BotDetectedError, CaptchaDetectedError
from gemini_analyzer import GeminiAnalyzer, GeminiRateLimitError, GeminiUnavailableError, GeminiNotFoundError, GeminiAnalysisError
from notifier import Notifier
from i18n import I18n

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
    i18n = I18n(language)

    print(i18n.t("main.starting"))

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
    print(i18n.t("main.rss_check"))
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
        print(i18n.t("main.no_pending"))
    else:
        print(i18n.t("main.pending_count", count=len(pending_entries)))

        # 1回の実行での制限
        max_analysis_success_count  = config.get('max_analysis_success_count', 5)
        max_scholar_access_attempts = config.get('max_scholar_access_attempts', 10)
        scholar_search_timeout_sec  = config.get('scholar_search_timeout_sec', 30)
        interval_after_success_sec  = config.get('interval_after_success_sec', 10)
        interval_after_notfound_sec = config.get('interval_after_notfound_sec', 20)
        interval_random_max_sec     = config.get('interval_random_max_sec', 9)
        min_abstract_length         = config.get('min_abstract_length', 50)
        scholar_search_year_range   = config.get('scholar_search_year_range', 1)

        processed_count = 0
        tried_count = 0
        consecutive_unavailable_count = 0

        import threading

        for entry in pending_entries:
            if processed_count >= max_analysis_success_count:
                print(i18n.t("main.limit_reached", limit=max_analysis_success_count))
                break
            if tried_count >= max_scholar_access_attempts:
                print(i18n.t("main.tried_limit", limit=max_scholar_access_attempts))
                break

            tried_count += 1
            print(i18n.t(
                "main.processing",
                tried=tried_count,
                max_tried=max_scholar_access_attempts,
                processed=processed_count,
                max_processed=max_analysis_success_count,
                title=entry['title']
            ))

            # ガード: タイトルがない場合は Scholar 検索を行わず整理してスキップ
            if not entry.get('title'):
                print(i18n.t("main.invalid_title_warning"))
                history_mgr.mark_completed(entry['link'], title="[Invalid Title]", is_relevant=False, reason="Title missing")
                continue

            # 既にDBに要旨があるかチェック
            abstract = entry.get('abstract')

            if not abstract:
                # Google Scholar検索（タイムアウト付き）
                def fetch_with_timeout():
                    nonlocal abstract
                    try:
                        abstract = abstract_fetcher.fetch_abstract(
                            entry['title'],
                            source_url=entry['link'],
                            year_range=scholar_search_year_range,
                            min_abstract_len=min_abstract_length
                        )
                    except CaptchaDetectedError as ce:
                        entry['captcha_url'] = ce.url
                    except BotDetectedError as be:
                        print(i18n.t("main.bot_error", error=be))
                        entry['bot_error'] = be

                fetch_thread = threading.Thread(target=fetch_with_timeout)
                fetch_thread.start()
                fetch_thread.join(timeout=scholar_search_timeout_sec)

                if fetch_thread.is_alive():
                    print(i18n.t("main.scholar_no_resp"))
                    break

                if 'captcha_url' in entry:
                    print(i18n.t("main.captcha_detected"))
                    try:
                        abstract = abstract_fetcher.resolve_captcha_and_fetch(
                            entry['captcha_url'],
                            entry['title'],
                            min_abstract_len=min_abstract_length
                        )
                    except BotDetectedError as be:
                        print(i18n.t("main.bot_error", error=be))
                        break
            else:
                print(i18n.t("main.db_abstract_reuse", title=entry['title']))

            if 'bot_error' in entry:
                break

            if abstract:
                print(i18n.t("main.abs_success", title=entry['title']))
                # Geminiで解析
                entry['summary'] = abstract
                try:
                    is_relevant, reason, summarized_abstract = analyzer.analyze_entry(entry)
                    consecutive_unavailable_count = 0  # 成功したらリセット
                except GeminiRateLimitError as ge:
                    print(i18n.t("main.gemini_limit", error=ge))
                    # 既に要旨がある場合は保存してから終了
                    history_mgr.move_to_end(entry['link'], abstract=abstract)
                    break
                except GeminiUnavailableError as ue:
                    print(f"\n!!!! {ue} !!!!")
                    consecutive_unavailable_count += 1
                    if consecutive_unavailable_count >= 3:
                        print(i18n.t("main.gemini_unavailable_stop"))
                        # 3回目も要旨を保存してから終了
                        history_mgr.move_to_end(entry['link'], abstract=abstract)
                        break
                    print(i18n.t("main.gemini_unavailable_continue"))
                    history_mgr.move_to_end(entry['link'], abstract=abstract)
                    continue
                except GeminiNotFoundError as ne:
                    print(i18n.t("main.gemini_not_found", error=ne))
                    # モデルが見つからない場合は、以降の論文もすべて失敗する可能性が高いため中断する
                    # pending状態（move_to_end）にして次回回しにする
                    history_mgr.move_to_end(entry['link'], abstract=abstract)
                    break
                except GeminiAnalysisError as ae:
                    print(f"Gemini analysis error (retrying later): {ae}")
                    history_mgr.move_to_end(entry['link'], abstract=abstract)
                    continue
                except Exception as e:
                    print(f"Unexpected error during Gemini analysis (retrying later): {e}")
                    history_mgr.move_to_end(entry['link'], abstract=abstract)
                    continue

                processed_count += 1

                if is_relevant:
                    print(i18n.t("main.relevant"))
                    notifier.notify(entry, reason, summarized_abstract)
                else:
                    print(i18n.t("main.not_relevant"))

                # 関連性に関わらず、解析済みの詳細情報を保存して完了とする
                history_mgr.mark_completed(
                    entry['link'],
                    title=entry['title'],
                    abstract=abstract,
                    is_relevant=is_relevant,
                    reason=reason,
                    jp_abstract=summarized_abstract
                )
                time.sleep(interval_after_success_sec + random.randint(0, interval_random_max_sec))
            else:
                print(i18n.t("main.not_registered", title=entry['title']))
                history_mgr.move_to_end(entry['link'])
                time.sleep(interval_after_notfound_sec + random.randint(0, interval_random_max_sec))

        # SQLite版では個別のsave()は不要だが、インターフェース維持のため呼び出しは残す（中身はpass）
        history_mgr.save()

    print(i18n.t("main.done"))

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
