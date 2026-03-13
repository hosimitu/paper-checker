import json
import os
from datetime import datetime, timedelta

class HistoryManager:
    def __init__(self, history_file='history_manager.json', pending_file='pending.json'):
        # 既存のファイル名と整合性を保つため修正 (history.json に統一)
        self.history_file = 'history.json'
        self.pending_file = pending_file
        self.history = self._load_json(self.history_file, set)
        self.pending = self._load_json(self.pending_file, list)

    def _load_json(self, file_path, type_func):
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return type_func(data)
            except Exception:
                return type_func()
        return type_func()

    def is_known(self, entry_link):
        """履歴または保留中にあるか確認"""
        if entry_link in self.history:
            return True
        return any(p['link'] == entry_link for p in self.pending)

    def add_to_pending(self, entry):
        """新規記事を保留キューに追加"""
        if not self.is_known(entry['link']):
            entry['added_date'] = datetime.now().isoformat()
            self.pending.append(entry)

    def get_pending_entries(self):
        """保留中の記事リストを取得"""
        return self.pending

    def mark_completed(self, entry_link):
        """処理完了。保留から削除し履歴に追加"""
        self.history.add(entry_link)
        self.pending = [p for p in self.pending if p['link'] != entry_link]

    def cleanup_expired(self, days=30):
        """期限切れ（30日以上）の保留記事を削除して履歴へ（二度と拾わない）"""
        now = datetime.now()
        new_pending = []
        for p in self.pending:
            added_date = datetime.fromisoformat(p.get('added_date'))
            if now - added_date < timedelta(days=days):
                new_pending.append(p)
            else:
                print(f"期限切れのため破棄します: {p['title']}")
                self.history.add(p['link'])
        self.pending = new_pending

    def save(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.history), f, ensure_ascii=False, indent=4)
        with open(self.pending_file, 'w', encoding='utf-8') as f:
            json.dump(self.pending, f, ensure_ascii=False, indent=4)
