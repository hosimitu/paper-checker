import re
import datetime
from scholarly import scholarly

class BotDetectedError(Exception):
    """Google ScholarのBot検知（ブロック）を検知した際の例外"""
    pass

class AbstractFetcher:
    def __init__(self):
        pass

    def _clean_title(self, title):
        """タイトルから <sub> などのHTMLタグを除去する"""
        return re.sub(r'<[^>]+>', '', title)

    def fetch_abstract(self, title, source_url=None):
        """
        Google Scholarでタイトルを検索し、Abstract取得を試みる。
        """
        try:
            # 0. タイトルのクリーンアップ (HTMLタグ除去)
            clean_title = self._clean_title(title)
            
            # 1. 普通の検索（あいまい検索）に変更（Bot検知を緩和）
            # 直近1年に絞り込み、特許を除外
            current_year = datetime.datetime.now().year
            query = clean_title
            print(f"Searching Scholar (Year >= {current_year-1}, No Patents): {query}")
            search_query = scholarly.search_pubs(
                query, 
                year_low=current_year - 1, 
                patents=False
            )
            first_result = next(search_query, None)
            
            if first_result:
                bib = first_result.get('bib', {})
                res_title = bib.get('title', '').lower()
                res_venue = bib.get('venue', '').lower()
                res_url = first_result.get('pub_url', '').lower()
                
                # 2. タイトルの類似性チェック
                if clean_title.lower() not in res_title and res_title not in clean_title.lower():
                    print(f"タイトルが一致しません: {res_title}")
                    return None

                # 3. 掲載誌またはURLドメインのチェック
                if source_url:
                    from urllib.parse import urlparse
                    source_domain = urlparse(source_url).netloc.lower().replace('www.', '')
                    if source_domain not in res_url and source_domain not in res_venue:
                        print(f"掲載元/ドメインが一致しません: {res_venue} / {res_url} (Expected: {source_domain})")
                        return None

                abstract = bib.get('abstract')
                if abstract and len(abstract) > 50:
                    return abstract
            return None
        except Exception as e:
            error_msg = str(e)
            # Bot検知（429 Too Many Requests や MaxTriesExceeded）をチェック
            if "429" in error_msg or "MaxTries" in error_msg or "Too Many Requests" in error_msg:
                print(f"CRITICAL: Google Scholar Bot Detection detected! ({error_msg})")
                raise BotDetectedError(f"Google Scholar block detected: {error_msg}")
            
            print(f"Scholarly Fetch Error: {e}")
            return None
