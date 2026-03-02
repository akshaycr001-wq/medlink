import sqlite3
import glob
print("Starting search for admin1")
for dbf in glob.glob('instance/*.db'):
    try:
        db = sqlite3.connect(dbf)
        users = db.execute('SELECT username, name, role FROM user WHERE role="sub_admin" OR name LIKE "%admin1%" OR username LIKE "%admin1%"').fetchall()
        print(f"[{dbf}] matches:")
        for u in users:
            print(f"  {u}")
    except Exception as e:
        print(f"Error on {dbf}: {e}")
