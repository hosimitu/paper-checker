import feedparser

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
                new_entries.append({
                        'title': entry.title,
                        'link': entry.link,
                        'summary': getattr(entry, 'summary', ''),
                        'published': getattr(entry, 'published', 'N/A')
                    })
        return new_entries
