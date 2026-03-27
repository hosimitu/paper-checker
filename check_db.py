import sqlite3

def check():
    conn = sqlite3.connect('history.db')
    conn.row_factory = sqlite3.Row
    
    c = conn.execute("SELECT id, link, title FROM articles WHERE status='pending' AND (title IS NULL OR title='')")
    bad_rows = [dict(r) for r in c.fetchall()]
    print(f"Bad pending rows (null or empty title): {len(bad_rows)}")
    for r in bad_rows[:10]:
        print(r)
        
    c = conn.execute("SELECT count(*) FROM articles WHERE status='pending'")
    total_pending = c.fetchone()[0]
    print(f"Total pending rows: {total_pending}")

    # Check the first 10 pending rows sorted by added_date ascending (how get_pending_entries gets them)
    c = conn.execute("SELECT id, title FROM articles WHERE status='pending' ORDER BY added_date ASC LIMIT 10")
    print("First 10 pending rows:")
    for r in c.fetchall():
        print(dict(r))

if __name__ == '__main__':
    check()
