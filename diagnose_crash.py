from app import app
import os

print("Testing app import and context...")
try:
    with app.app_context():
        print("App context active.")
        from models import User
        user = User.query.first()
        print(f"Database access successful. First user: {user.username if user else 'None'}")
except Exception as e:
    print(f"Error during app test: {e}")

print("Testing minimal server start...")
from waitress import serve
# Try running on a different port and only for a second
try:
    import threading
    import time
    
    def run_server():
        try:
            serve(app, host='127.0.0.1', port=5005)
        except Exception as e:
            print(f"Server thread error: {e}")

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(2)
    print("Server started for 2 seconds.")
except Exception as e:
    print(f"Server start error: {e}")
