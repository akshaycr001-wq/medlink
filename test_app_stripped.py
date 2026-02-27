from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
# from flask_wtf.csrf import CSRFProtect
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
# from flask_talisman import Talisman
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Pharmacy, Medicine, Review, Hospital, SOS, SystemAlert, MedicineAlternative, Ambulance
from config import config
from datetime import datetime, timedelta
import os
import re
import math
import json
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Load configuration based on environment
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Initialize security extensions (DISABLED FOR TEST)
# csrf = CSRFProtect(app)
# limiter = Limiter(...)

if not os.environ.get('FLASK_TESTING'):
    db.init_app(app)
    
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@app.route("/")
def hello():
    return "App loaded correctly without security extensions."

if __name__ == "__main__":
    print("Starting test app...")
    app.run(port=5010, use_reloader=False)
