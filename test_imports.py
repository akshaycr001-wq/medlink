import sys

modules = [
    "flask",
    "flask_sqlalchemy",
    "flask_login",
    "flask_migrate",
    "flask_wtf",
    "flask_limiter",
    "flask_talisman",
    "werkzeug.security",
    "psycopg2",
    "dotenv"
]

for mod in modules:
    print(f"Importing {mod}...")
    try:
        __import__(mod)
        print(f"Success: {mod}")
    except Exception as e:
        print(f"Failed to import {mod}: {e}")
    sys.stdout.flush()

print("All imports tested.")
