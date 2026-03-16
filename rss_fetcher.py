import feedparser
import re
import unicodedata

class RSSFetcher:
    def __init__(self, urls):
        self.urls = urls

    def fetch_new_entries(self, history_manager):
        new_entries = []
        for url in self.urls:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if history_manager.is_known(entry.link):
                    continue
                
                # タイトルのクリーンアップ（HTMLタグ除去 + Unicode正規化）
                title = entry.title
                title = re.sub(r'<[^>]+>', '', title)
                title = unicodedata.normalize('NFKC', title)
                title = re.sub(r'\s+', ' ', title).strip()

                new_entries.append({
                        'title': title,
                        'link': entry.link,
                        'summary': getattr(entry, 'summary', ''),
                        'published': getattr(entry, 'published', 'N/A')
                    })
        return new_entries
