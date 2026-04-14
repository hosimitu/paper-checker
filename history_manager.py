import json
import os
import sqlite3
from datetime import datetime, timedelta

class HistoryManager:
    def __init__(self, db_file='history.db', history_json='history.json', pending_json='pending.json'):
        self.db_file = db_file
        self.history_json = history_json
        self.pending_json = pending_json
        self._init_db()
        self._migrate_from_json()

    def _get_connection(self):
        return sqlite3.connect(self.db_file)

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    link TEXT UNIQUE,
                    title TEXT,
                    abstract TEXT,
                    is_relevant BOOLEAN,
                    reason TEXT,
                    jp_abstract TEXT,
                    status TEXT, -- 'pending' or 'completed'
                    added_date DATETIME,
                    processed_date DATETIME
                )
            """)
            conn.commit()

    def _migrate_from_json(self):
        """既存のJSONファイルがあればデータを移行する"""
        if not os.path.exists(self.history_json) and not os.path.exists(self.pending_json):
            return

        print("既存のJSONデータが見つかりました。SQLiteへ移行します...")
        with self._get_connection() as conn:
            # 1. 履歴 (history.json) の移行
            if os.path.exists(self.history_json):
                try:
                    with open(self.history_json, 'r', encoding='utf-8') as f:
                        links = json.load(f)
                        for link in links:
                            conn.execute(
                                "INSERT OR IGNORE INTO articles (link, status, added_date) VALUES (?, ?, ?)",
                                (link, 'completed', datetime.now().isoformat())
                            )
                    os.rename(self.history_json, self.history_json + '.bak')
                except Exception as e:
                    print(f"history.json の移行中にエラー: {e}")

            # 2. 保留中 (pending.json) の移行
            if os.path.exists(self.pending_json):
                try:
                    with open(self.pending_json, 'r', encoding='utf-8') as f:
                        entries = json.load(f)
                        for entry in entries:
                            conn.execute(
                                "INSERT OR IGNORE INTO articles (link, title, status, added_date) VALUES (?, ?, ?, ?)",
                                (entry['link'], entry.get('title', ''), 'pending', entry.get('added_date', datetime.now().isoformat()))
                            )
                    os.rename(self.pending_json, self.pending_json + '.bak')
                except Exception as e:
                    print(f"pending.json の移行中にエラー: {e}")
            conn.commit()
        print("移行が完了しました（バックアップとして .bak を作成しました）。")

    def is_known(self, entry_link):
        """履歴または保留中にあるか確認"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT 1 FROM articles WHERE link = ?", (entry_link,))
            return cursor.fetchone() is not None

    def add_to_pending(self, entry):
        """新規記事を保留キューに追加"""
        if not self.is_known(entry['link']):
            now_iso = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO articles (link, title, status, added_date) VALUES (?, ?, ?, ?)",
                    (entry['link'], entry['title'], 'pending', now_iso)
                )
                conn.commit()

    def get_pending_entries(self):
        """保留中の記事リストを古い順に取得"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM articles WHERE status = 'pending' ORDER BY added_date ASC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def mark_completed(self, entry_link, title=None, abstract=None, is_relevant=None, reason=None, jp_abstract=None):
        """処理完了。詳細情報を保存しステータスを更新"""
        now_iso = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE articles SET 
                    status = 'completed',
                    title = COALESCE(?, title),
                    abstract = ?,
                    is_relevant = ?,
                    reason = ?,
                    jp_abstract = ?,
                    processed_date = ?
                WHERE link = ?
            """, (title, abstract, is_relevant, reason, jp_abstract, now_iso, entry_link))
            conn.commit()

    def move_to_end(self, entry_link, abstract=None):
        """キューの最後に回す。要旨が提供された場合は保存する。"""
        now_iso = datetime.now().isoformat()
        with self._get_connection() as conn:
            if abstract:
                conn.execute(
                    "UPDATE articles SET added_date = ?, abstract = ? WHERE link = ?",
                    (now_iso, abstract, entry_link)
                )
            else:
                conn.execute(
                    "UPDATE articles SET added_date = ? WHERE link = ?",
                    (now_iso, entry_link)
                )
            conn.commit()

    def cleanup_expired(self, days=30):
        """期限切れの保留記事を完了（破棄）扱いにする"""
        threshold = (datetime.now() - timedelta(days=days)).isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT title FROM articles WHERE status = 'pending' AND added_date < ?",
                (threshold,)
            )
            expired = cursor.fetchall()
            for row in expired:
                print(f"期限切れのため保持を終了します: {row[0]}")
            
            conn.execute(
                "UPDATE articles SET status = 'completed' WHERE status = 'pending' AND added_date < ?",
                (threshold,)
            )
            conn.commit()

    def save(self):
        """SQLite版では個別のセーブは不要（各メソッドでcommit済み）"""
        pass
