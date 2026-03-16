import re
import datetime
import unicodedata
import time
import threading
import os
import queue as queue_module
from scholarly import scholarly
from playwright_stealth import Stealth

class BotDetectedError(Exception):
    """Google ScholarのBot検知（ブロック）を検知した際の例外"""
    pass

class ManualInterventionRequired(Exception):
    """手動でのキャプチャ解除が必要な際の例外"""
    pass

def _run_playwright_headless(url, data_dir, result_queue):
    """
    別スレッドでPlaywright Sync APIを実行する。
    launch_persistent_context を使用してセッションを維持する。
    """
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # 永続的なコンテキストを起動（ブラウザの起動も兼ねる）
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            context = p.chromium.launch_persistent_context(
                data_dir,
                headless=True,
                user_agent=user_agent
            )
            page = context.pages[0] if context.pages else context.new_page()
            Stealth().apply_stealth_sync(page)

            try:
                page.goto(url, timeout=30000)

                # ブロック検知 (CAPTCHAなど)
                content = page.content()
                if "gs_captcha_cb" in content or "recaptcha" in content.lower() or page.locator("#gs_captcha_ccl").is_visible():
                    print("\n[!] Google Scholar Bot Detection (CAPTCHA) detected via Playwright.")
                    result_queue.put(('captcha', url))
                    return

                # 最初の検索結果を待機
                try:
                    page.wait_for_selector(".gs_ri", timeout=5000)
                except:
                    result_queue.put(('ok', None))
                    return

                render_results = page.locator(".gs_ri")
                if render_results.count() > 0:
                    first_result = render_results.first
                    title_elem = first_result.locator(".gs_rt a")

                    if title_elem.count() > 0:
                        res_title = title_elem.inner_text()
                        res_url = title_elem.get_attribute("href")
                        snippet_elem = first_result.locator(".gs_rs")
                        res_abstract = snippet_elem.inner_text() if snippet_elem.count() > 0 else ""
                        result_queue.put(('ok', {
                            'bib': {'title': res_title, 'abstract': res_abstract},
                            'pub_url': res_url or ""
                        }))
                    else:
                        result_queue.put(('ok', None))
                else:
                    result_queue.put(('ok', None))

            except Exception as e:
                result_queue.put(('error', str(e)))
            finally:
                context.close()

    except Exception as e:
        result_queue.put(('error', str(e)))


def _run_playwright_headful(url, data_dir, result_queue, timeout_sec):
    """
    別スレッドでPlaywright Sync APIをヘッドフルで実行する。
    launch_persistent_context を使用してセッションを維持する。
    """
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                data_dir,
                headless=False
            )
            page = context.pages[0] if context.pages else context.new_page()
            Stealth().apply_stealth_sync(page)
            page.goto(url)

            start_time = time.time()
            result_found = None

            while time.time() - start_time < timeout_sec:
                try:
                    if page.locator(".gs_ri").count() > 0:
                        print("\n[+] ブロックが解除されたことを確認しました。")
                        first_result = page.locator(".gs_ri").first
                        title_elem = first_result.locator(".gs_rt a")
                        if title_elem.count() > 0:
                            res_title = title_elem.inner_text()
                            res_url = title_elem.get_attribute("href")
                            snippet_elem = first_result.locator(".gs_rs")
                            res_abstract = snippet_elem.inner_text() if snippet_elem.count() > 0 else ""
                            result_found = {
                                'bib': {'title': res_title, 'abstract': res_abstract},
                                'pub_url': res_url or ""
                            }
                        break
                except:
                    pass
                time.sleep(2)

            context.close()

            if result_found:
                result_queue.put(('ok', result_found))
            else:
                result_queue.put(('timeout', None))

    except Exception as e:
        result_queue.put(('error', str(e)))


class AbstractFetcher:
    def __init__(self, config=None):
        self.config = config or {}
        self.use_playwright = self.config.get('use_playwright', False)
        self.manual_timeout = self.config.get('manual_captcha_timeout_sec', 120)
        # ユーザーデータディレクトリの絶対パスを取得
        data_dir_name = self.config.get('playwright_user_data_dir', '.playwright_data')
        self.data_dir = os.path.abspath(data_dir_name)

    def _clean_title(self, title):
        """タイトルから HTMLタグを除去し、Unicode正規化を行う"""
        if not title:
            return ""
        # BeautifulSoup等を使わず、簡易的な正規表現でタグ（<...状況...>）を除去
        title = re.sub(r'<[^>]+>', '', title)
        # Unicode正規化 (NFKC: 特殊記号や全角半角を統合)
        title = unicodedata.normalize('NFKC', title)
        # 連続する空白を1つにまとめ、前後の空白を消去
        title = re.sub(r'\s+', ' ', title).strip()
        return title

    def _simplify_for_comparison(self, title):
        """比較のためにタイトルを簡略化する（記号、空白を除去）"""
        return re.sub(r'[^a-zA-Z0-9]', '', title).lower()

    def _fetch_abstract_with_playwright(self, query, year_low):
        """別スレッドでPlaywrightを起動してGoogle Scholarから情報を取得する"""
        url = f"https://scholar.google.co.jp/scholar?as_ylo={year_low}&q={query}&hl=ja&as_sdt=0,5"
        result_queue = queue_module.Queue()

        t = threading.Thread(target=_run_playwright_headless, args=(url, self.data_dir, result_queue))
        t.start()
        t.join(timeout=40)

        if t.is_alive():
            print("\n[!] Playwright headless timed out. Trying headful mode.")
            return self._handle_manual_captcha(url)

        status, data = result_queue.get()

        if status == 'captcha':
            return self._handle_manual_captcha(data)
        elif status == 'ok':
            return data
        else:
            print(f"Playwright Error: {data}")
            if "timeout" in str(data).lower():
                return self._handle_manual_captcha(url)
            return None

    def _handle_manual_captcha(self, url):
        """ヘッドフルブラウザを別スレッドで起動し、ユーザーにキャプチャ解除を依頼する"""
        print("\n" + "="*60)
        print("【重要】Google Scholarのブロックを検知しました。")
        print("ブラウザウィンドウを起動しますので、キャプチャを解除してください。")
        print(f"制限時間: {self.manual_timeout}秒")
        print("="*60 + "\n")

        result_queue = queue_module.Queue()
        t = threading.Thread(target=_run_playwright_headful, args=(url, self.data_dir, result_queue, self.manual_timeout))
        t.start()
        t.join(timeout=self.manual_timeout + 10)

        if t.is_alive():
            print(f"\n[!] {self.manual_timeout}秒以内に解除が確認できませんでした。（スレッドタイムアウト）")
            raise BotDetectedError("CAPTCHA timeout: Manual intervention timed out (thread).")

        status, data = result_queue.get()

        if status == 'ok':
            return data
        elif status == 'timeout':
            print(f"\n[!] {self.manual_timeout}秒以内に解除が確認できませんでした。")
            raise BotDetectedError("CAPTCHA timeout: Manual intervention failed or timed out.")
        else:
            print(f"\n[!] ヘッドフルモードでエラーが発生しました: {data}")
            raise BotDetectedError(f"Headful browser error: {data}")

    def fetch_abstract(self, title, source_url=None, year_range=1, min_abstract_len=50):
        """
        Google Scholarでタイトルを検索し、Abstract取得を試みる。
        """
        clean_title = self._clean_title(title)
        current_year = datetime.datetime.now().year
        year_low = current_year - year_range
        query = clean_title

        try:
            if self.use_playwright:
                print(f"Searching Scholar via Playwright: {query}")
                result = self._fetch_abstract_with_playwright(query, year_low)
            else:
                # 従来のscholarlyを使用
                print(f"Searching Scholar via Scholarly: {query}")
                search_query = scholarly.search_pubs(
                    query,
                    year_low=year_low,
                    patents=False
                )
                result = next(search_query, None)

            if result:
                bib = result.get('bib', {})
                res_title = self._clean_title(bib.get('title', '')).lower()
                res_url = result.get('pub_url', '').lower()

                # タイトルの類似性チェック
                sim_clean_title = self._simplify_for_comparison(clean_title)
                sim_res_title = self._simplify_for_comparison(res_title)
                if sim_clean_title not in sim_res_title and sim_res_title not in sim_clean_title:
                    print(f"タイトルが一致しません: {res_title}")
                    return None

                abstract = bib.get('abstract')
                if abstract and len(abstract) > min_abstract_len:
                    return abstract
            return None

        except BotDetectedError as e:
            raise e
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "MaxTries" in error_msg or "Too Many Requests" in error_msg:
                print(f"CRITICAL: Google Scholar Bot Detection detected! ({error_msg})")
                if self.use_playwright:
                    url = f"https://scholar.google.co.jp/scholar?as_ylo={year_low}&q={query}"
                    return self._handle_manual_captcha(url)
                raise BotDetectedError(f"Google Scholar block detected: {error_msg}")

            print(f"Fetch Error: {e}")
            return None
