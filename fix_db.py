import sqlite3

def fix():
    conn = sqlite3.connect('history.db')
    c = conn.execute("DELETE FROM articles WHERE status='pending' AND (title IS NULL OR title='')")
    deleted = c.rowcount
    conn.commit()
    print(f"Deleted {deleted} pending rows with null or empty title.")

if __name__ == '__main__':
    fix()
