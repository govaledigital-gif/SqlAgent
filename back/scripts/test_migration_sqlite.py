import sqlite3
import os

db = os.path.join(os.path.dirname(__file__), '..', 'test_migration.db')
db = os.path.normpath(db)
if os.path.exists(db):
    os.remove(db)
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute('CREATE TABLE companies(id TEXT PRIMARY KEY, name TEXT NOT NULL, code TEXT NOT NULL, owner_email TEXT NOT NULL, is_active INTEGER, created_at TEXT, updated_at TEXT)')
conn.commit()
print('Before:', cur.execute("PRAGMA table_info(companies)").fetchall())
try:
    cur.execute('ALTER TABLE companies ADD COLUMN ai_enabled INTEGER DEFAULT 0')
    conn.commit()
    print('ALTER OK')
except Exception as e:
    print('Alter error', e)
print('After:', cur.execute("PRAGMA table_info(companies)").fetchall())
conn.close()
