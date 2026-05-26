import os
import shutil
from datetime import datetime

base = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base, 'hospital_mgmt.db')
backup_path = os.path.join(base, f'hospital_mgmt.db.bak.{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}')

if not os.path.exists(db_path):
    print('No database file found to repair.')
    raise SystemExit(1)

print(f'Backing up corrupted database to: {backup_path}')
shutil.copy2(db_path, backup_path)
print('Backup complete.')

print('Removing corrupted database file...')
os.remove(db_path)
print('Corrupted database removed.')

print('Seeding new database...')
os.system('python seed_database.py')
print('Database repair complete.')
