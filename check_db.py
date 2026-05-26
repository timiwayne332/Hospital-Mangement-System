import sqlite3
import os
path = 'hospital_mgmt.db'
print('exists', os.path.exists(path))
try:
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print('tables', cur.fetchall())
    conn.close()
except Exception as e:
    print('ERR', repr(e))
