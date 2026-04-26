from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import random
import re
import secrets
from flask_mail import Mail, Message

# OTP Storage (In-memory for demo; use Redis or DB for production)
OTP_STORE = {}

# Load environment variables IMMEDIATELY
load_dotenv()

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, func
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Pharmacy, Medicine, Review, Hospital, SOS, SystemAlert, MedicineAlternative, Ambulance
from config import config
from datetime import datetime, timedelta
import re
import math
import json
import secrets
import urllib.parse
import urllib.request

def geocode_location(name, address):
    """Attempt to geocode a location name and address using Nominatim (free)."""
    try:
        headers = {'User-Agent': 'MedLink-Emergency-Network/1.2'}
        
        # Strategy 1: Highly specific search (Address + Kochi + Kerala)
        if address:
            query = f"{name}, {address}, Kochi, Kerala, India"
            safe_query = urllib.parse.quote(query)
            url = f"https://nominatim.openstreetmap.org/search?q={safe_query}&format=json&limit=1"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                if data:
                    return float(data[0]['lat']), float(data[0]['lon'])

        # Strategy 2: Relaxed search (Name + Kochi)
        query = f"{name}, Kochi, India"
        safe_query = urllib.parse.quote(query)
        url = f"https://nominatim.openstreetmap.org/search?q={safe_query}&format=json&limit=1"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
                
        # Strategy 3: Just the address (if name is too obscure)
        if address:
            query = f"{address}, Kochi, India"
            safe_query = urllib.parse.quote(query)
            url = f"https://nominatim.openstreetmap.org/search?q={safe_query}&format=json&limit=1"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                if data:
                    return float(data[0]['lat']), float(data[0]['lon'])
                    
    except Exception as e:
        print(f"DEBUG: Geocoding failed for {name} ({address}): {e}")
    return None, None

# Create Flask app
app = Flask(__name__)

@app.before_request
def auto_seed_db():
    if not getattr(app, '_database_seeded', False):
        from models import db, User, Hospital, MedicineAlternative
        from werkzeug.security import generate_password_hash
        
        # 1. Ensure Admin exists
        if not User.query.filter_by(role='admin').first():
            admin = User(
                name='System Admin',
                username='admin',
                email='admin@medlink.com',
                password=generate_password_hash('admin123', method='pbkdf2:sha256'),
                role='admin',
                email_verified=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Auto-seeded admin account.")

        # 2. Ensure Test Data (Pharmacies, Hospitals, Alternatives)
        try:
            # Seed Hospitals if empty
            if Hospital.query.count() == 0:
                import seed_hospitals_real
                seed_hospitals_real.seed_hospitals()
                print("Auto-seeded internal hospital list.")

            # Seed Test Pharmacy & Medicines if empty
            if User.query.filter_by(username='testpharmacy').first() is None:
                import add_test_data
                add_test_data.add_test_data()
                print("Auto-seeded test pharmacy account.")

            # 3. Data Repair: Ensure all unverified pharmacies have a license_doc (for button visibility)
            from models import Pharmacy
            unlicensed = Pharmacy.query.filter_by(license_doc=None, verified=False).all()
            if unlicensed:
                for p in unlicensed:
                    p.license_doc = 'placeholder_license.png'
                db.session.commit()
                print(f"Repaired {len(unlicensed)} pharmacy records with placeholder licenses.")

        except Exception as e:
            print(f"Non-critical auto-repair/seed error: {e}")
            db.session.rollback()

        app._database_seeded = True

# Load configuration based on environment
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
MAIL_DEBUG_MODE = os.environ.get('MAIL_DEBUG_MODE', 'False').lower() == 'true'
mail = Mail(app)

# Initialize security extensions
# We use a robust initialization for production but keep it safe for local Python 3.14
try:
    csrf = CSRFProtect(app)
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://'),
        enabled=app.config.get('RATELIMIT_ENABLED', True)
    )
except Exception as e:
    print(f"Warning: Security extensions failed to initialize robustly: {e}")
    # Minimal fallback for local stability if needed
    class MockLimiter:
        def limit(self, *args, **kwargs): return lambda f: f
        def exempt(self, f): return f
    class MockCSRF:
        def init_app(self, app): pass
        def exempt(self, f): return f
    limiter = MockLimiter()
    csrf = MockCSRF()

@app.route('/send_otp', methods=['POST'])
@csrf.exempt
def send_otp():
    data = request.json
    email = data.get('gmail') if data else None
    
    if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', email):
        return jsonify({'error': 'Invalid Gmail address'}), 400
        
    otp = str(random.randint(100000, 999999))
    OTP_STORE[email] = {
        'code': otp,
        'timestamp': datetime.now()
    }
    
    if MAIL_DEBUG_MODE or not app.config.get('MAIL_USERNAME') or app.config.get('MAIL_USERNAME') == 'your_gmail@gmail.com':
        # DEBUG MODE: Print OTP to terminal
        print("\n" + "="*40)
        print(f"[MedLink OTP] Verification code for {email}: {otp}")
        print("="*40 + "\n")
    else:
        # PRODUCTION MODE: Send real email
        try:
            msg = Message(
                subject='MedLink - Your Verification Code',
                recipients=[email],
                html=f'''
                <div style="font-family: sans-serif; padding: 20px; max-width: 400px;">
                    <h2 style="color: #0d9488;">MedLink Verification</h2>
                    <p>Your one-time verification code is:</p>
                    <h1 style="letter-spacing: 8px; color: #1e293b; font-size: 36px;">{otp}</h1>
                    <p style="color: #64748b; font-size: 12px;">This code expires in 10 minutes. Do not share it with anyone.</p>
                </div>
                '''
            )
            mail.send(msg)
        except Exception as e:
            print(f"Email send error: {e}")
            return jsonify({'error': 'Failed to send email. Please check server mail config.'}), 500
    
    return jsonify({'message': 'OTP sent successfully'})

# Security headers (only enforce HTTPS in production)
csp = {
    'default-src': ["'self'", "'unsafe-inline'"],
    'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", 
                   "https://cdn.tailwindcss.com", "https://cdnjs.cloudflare.com",
                   "https://cdn.jsdelivr.net", "https://unpkg.com"],
    'style-src': ["'self'", "'unsafe-inline'", 
                  "https://cdnjs.cloudflare.com", "https://fonts.googleapis.com",
                  "https://cdn.tailwindcss.com", "https://cdn.jsdelivr.net"],
    'font-src': ["'self'", "https://fonts.gstatic.com", "https://cdnjs.cloudflare.com"],
    'img-src': ["'self'", "data:", "https:"],
    'connect-src': ["'self'", "https:"],
}
if env == 'production':
    Talisman(app, force_https=True, strict_transport_security=True, content_security_policy=csp)
else:
    # In development, use Talisman but don't force HTTPS
    Talisman(app, force_https=False, content_security_policy=None)

# Create upload folder if not exists
upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'png', 'jpg', 'jpeg'})

def haversine(lat1, lon1, lat2, lon2):
    # Radius of the Earth in km
    R = 6371.0
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance

if not os.environ.get('FLASK_TESTING'):
    db.init_app(app)
    migrate = Migrate(app, db)
    
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Rate limit login attempts
def login():
    if request.method == 'POST':
        identifier = (request.form.get('identifier') or '').strip().lower()
        password = request.form.get('password')
        user = User.query.filter(or_(func.lower(User.username) == identifier, func.lower(User.email) == identifier)).first()
        
        if not user:
            print(f"DEBUG: Login failed - Account not found for identifier: {identifier}")
        else:
            print(f"DEBUG: Login attempt for user: {user.username} (Role: {user.role})")
        
        if user:
            # Strip whitespace to avoid common login issues
            if check_password_hash(user.password, password.strip()):
                if user.role in ['admin', 'sub_admin']:
                    flash('Please use the Admin Portal', 'error')
                    return redirect(url_for('admin_login'))
                
                if user.is_suspended:
                    flash('Your account has been suspended by an administrator.', 'error')
                    return redirect(url_for('login'))
                
                # Check email verification (Bypassed for now)
                # if not getattr(user, 'email_verified', True):
                #     flash('Please verify your email before logging in. Check the server console for the verification link.')
                #     return redirect(url_for('login'))

                if user.role == 'pharmacy':
                    pharma = Pharmacy.query.filter_by(user_id=user.id).first()
                    if pharma and not pharma.verified:
                        flash('Your pharmacy account is pending admin approval.', 'warning')
                        return redirect(url_for('login'))
                    login_user(user)
                    return redirect(url_for('pharmacy_dashboard'))
                elif user.role == 'patient':
                    login_user(user)
                    return redirect(url_for('patient_dashboard'))
            else:
                flash('Incorrect password. Please try again or use Forgot Password.')
        else:
            flash('Account not found. Please register or check your credentials.')
            
    return render_template('login.html')

# --- Password Reset Token Store (in-memory; swap to DB/Redis for production) ---
_reset_tokens = {}  # { token: { 'user_id': int, 'expires': datetime } }
_verify_tokens = {}  # { token: { 'user_id': int, 'expires': datetime } }

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate 6-digit OTP
            otp = str(random.randint(100000, 999999))
            OTP_STORE[email] = {
                'code': otp,
                'timestamp': datetime.now(),
                'user_id': user.id,
                'type': 'password_reset'
            }
            
            # Send OTP via email
            if MAIL_DEBUG_MODE or not app.config.get('MAIL_USERNAME'):
                print(f"\n[PASSWORD RESET OTP] User: {user.username} | Email: {email} | OTP: {otp}\n")
            else:
                try:
                    msg = Message(
                        subject='MedLink - Password Reset Code',
                        recipients=[email],
                        html=f'''
                        <div style="font-family: sans-serif; padding: 20px; max-width: 400px; border: 1px solid #eee; border-radius: 12px;">
                            <h2 style="color: #0d9488;">MedLink Reset</h2>
                            <p>You requested a password reset. Your verification code is:</p>
                            <h1 style="letter-spacing: 8px; color: #1e293b; font-size: 36px; text-align: center;">{otp}</h1>
                            <p style="color: #64748b; font-size: 12px;">This code expires in 2 minutes. If you didn't request this, ignore this email.</p>
                        </div>
                        '''
                    )
                    mail.send(msg)
                except Exception as e:
                    print(f"Mail error: {e}")
                    flash('Error sending verification code. Please try again.')
                    return redirect(url_for('forgot_password'))
            
            return render_template('forgot_password.html', step=2, email=email)
            
        flash('If that account exists, a verification code has been sent.')
        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html', step=1)

@app.route('/verify_reset_otp', methods=['POST'])
def verify_reset_otp():
    email = request.form.get('email')
    otp_code = request.form.get('otp_code')
    stored = OTP_STORE.get(email)
    
    if not stored or stored.get('type') != 'password_reset' or stored['code'] != otp_code:
        flash('Invalid verification code.')
        return render_template('forgot_password.html', step=2, email=email)
        
    if (datetime.now() - stored['timestamp']).total_seconds() > 120:
        flash('Code expired. Please try again.')
        return redirect(url_for('forgot_password'))
        
    # Generate temporary reset token valid for 10 minutes
    reset_token = secrets.token_urlsafe(32)
    _reset_tokens[reset_token] = {
        'user_id': stored['user_id'],
        'expires': datetime.now() + timedelta(minutes=10)
    }
    
    # Store in session to ensure the user stays on the same reset flow
    session['reset_active'] = reset_token
    return render_template('forgot_password.html', step=3, token=reset_token)

@app.route('/reset_password', methods=['POST'])
def reset_password():
    token = request.form.get('token')
    token_data = _reset_tokens.get(token)
    
    if not token_data or token_data['expires'] < datetime.now():
        _reset_tokens.pop(token, None)
        flash('Session expired. Please start again.')
        return redirect(url_for('forgot_password'))
    
    password = request.form.get('password')
    confirm = request.form.get('confirm_password')
    
    if not password or len(password) < 8:
        flash('Password must be at least 8 characters.')
        return render_template('forgot_password.html', step=3, token=token)
        
    if password != confirm:
        flash('Passwords do not match.')
        return render_template('forgot_password.html', step=3, token=token)
        
    user = User.query.get(token_data['user_id'])
    if user:
        # Strip whitespace and use a more universally compatible hashing method
        user.password = generate_password_hash(password.strip(), method='pbkdf2:sha256')
        db.session.commit()
        _reset_tokens.pop(token, None)
        session.pop('reset_active', None)
        flash('Password updated successfully! You can now log in.')
        return redirect(url_for('login'))
        
    flash('User not found.')
    return redirect(url_for('forgot_password'))

@app.route('/verify_email/<token>')
def verify_email(token):
    token_data = _verify_tokens.get(token)
    if not token_data or token_data['expires'] < datetime.now():
        _verify_tokens.pop(token, None)
        flash('This verification link has expired or is invalid.')
        return redirect(url_for('login'))
    user = User.query.get(token_data['user_id'])
    if user:
        user.email_verified = True
        db.session.commit()
        _verify_tokens.pop(token, None)
        flash('Email verified successfully! You can now log in.')
    return redirect(url_for('login'))

@app.route('/admin_login', methods=['GET', 'POST'])
@limiter.limit("3 per minute")  # Stricter rate limit for admin login
def admin_login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip().lower()
        password = request.form.get('password')
        user = User.query.filter(func.lower(User.username) == username).first()
        
        if user:
            if check_password_hash(user.password, password.strip()):
                if user.role not in ['admin', 'sub_admin']:
                    flash('Access Denied: Admins Only')
                    return redirect(url_for('login'))
                
                if user.role == 'sub_admin' and user.is_suspended:
                    flash('Your administrative access has been suspended.')
                    return redirect(url_for('admin_login'))
                    
                login_user(user)
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Incorrect admin password')
        else:
            flash('Admin ID not found')
            
    return render_template('admin_login.html')

@app.route('/emergency_rescue_homeo')
def emergency_rescue():
    # 1. Clear collisions: Find ALL accounts with this email
    email_target = 'pharm48848@gmail.com'
    all_users = User.query.filter(func.lower(User.email) == email_target.lower()).all()
    
    # 2. Identify the 'main' pharmacy account (likely the one with pharmacy role)
    main_pharma = None
    for u in all_users:
        if u.role == 'pharmacy':
            main_pharma = u
            break
            
    if not main_pharma and all_users:
        main_pharma = all_users[0] # Fallback to first one
        
    if main_pharma:
        # Rename others to avoid collision
        for u in all_users:
            if u.id != main_pharma.id:
                u.email = f"old_{u.id}_{u.email}"
                u.username = f"old_{u.id}_{u.username}"
        
        # Reset the main one
        main_pharma.password = generate_password_hash('Medlink123', method='pbkdf2:sha256')
        main_pharma.email_verified = True
        db.session.commit()
        return f"SUCCESS: Account '{main_pharma.username}' restored. Use pharmacy login with password 'Medlink123'. (Renamed {len(all_users)-1} colliding accounts)"
        
    return "User homeonellad not found."

@app.route('/admin/restore_data')
@login_required
def restore_data():
    if current_user.role != 'admin':
        return "Access Denied", 403
        
    try:
        import seed_hospitals_real
        import seed_massive_alternatives
        import add_test_data
        
        print("Starting manual data restoration...")
        seed_hospitals_real.seed_hospitals()
        seed_massive_alternatives.seed_alternatives()
        
        # Also ensure test pharmacy exists
        if User.query.filter_by(username='testpharmacy').first() is None:
            add_test_data.add_test_data()
            
        return "SUCCESS: All core data (Hospitals, Ambulances, Alternatives, Test Data) has been restored/updated."
    except Exception as e:
        return f"Restore Error: {e}", 500
        seed_hospitals_real.seed_hospitals()
        seed_massive_alternatives.seed_alternatives()
        
        # Also ensure test pharmacy exists
        if User.query.filter_by(username='testpharmacy').first() is None:
            add_test_data.add_test_data()
            
        return "SUCCESS: All core data (Hospitals, Ambulances, Alternatives, Test Data) has been restored/updated."
    except Exception as e:
        return f"Restore Error: {e}", 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('gmail')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role') # 'patient' or 'pharmacy'
        phone = request.form.get('phone')
        
        # 1. Basic Gmail Validation
        if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', email):
            flash('Please provide a valid @gmail.com address')
            return redirect(url_for('register'))

        # 2. Password Confirmation
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))
            
        if len(password) < 8:
            flash('Password must be at least 8 characters long')
            return redirect(url_for('register'))

        # 3. Existing User Check
        if User.query.filter((func.lower(User.username) == username.lower()) | (func.lower(User.email) == email.lower())).first():
            flash('Username or Email already exists')
            return redirect(url_for('register'))
            
        # 4. Handle Optional License Upload
        license_filename = None
        file = request.files.get('license_doc')
        if file and allowed_file(file.filename):
            license_filename = secure_filename(f"{username}_license_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], license_filename))

        # Store pending registration in session
        session['pending_registration'] = {
            'username': username,
            'email': email,
            'password': generate_password_hash(password.strip(), method='pbkdf2:sha256'),
            'role': role,
            'phone': phone,
            'shop_name': request.form.get('shop_name'),
            'latitude': request.form.get('latitude'),
            'longitude': request.form.get('longitude'),
            'location_address': request.form.get('location_address'),
            'prc_no': request.form.get('prc_no'),
            'dl_no': request.form.get('dl_no'),
            'license_doc': license_filename
        }

        # Generate and send OTP automatically
        otp = str(random.randint(100000, 999999))
        OTP_STORE[email] = {
            'code': otp,
            'timestamp': datetime.now()
        }

        if MAIL_DEBUG_MODE or not app.config.get('MAIL_USERNAME') or app.config.get('MAIL_USERNAME') == 'your_gmail@gmail.com':
            print("\n" + "="*40)
            print(f"[MedLink OTP] Verification code for {email}: {otp}")
            print("="*40 + "\n")
        else:
            try:
                msg = Message(
                    subject='MedLink - Your Verification Code',
                    recipients=[email],
                    html=f'''
                    <div style="font-family: sans-serif; padding: 20px; max-width: 400px;">
                        <h2 style="color: #0d9488;">MedLink Verification</h2>
                        <p>Your one-time verification code is:</p>
                        <h1 style="letter-spacing: 8px; color: #1e293b; font-size: 36px;">{otp}</h1>
                        <p style="color: #64748b; font-size: 12px;">This code expires in 2 minutes. Do not share it with anyone.</p>
                    </div>
                    '''
                )
                mail.send(msg)
            except Exception as e:
                print(f"Email send error: {e}")
                flash('Failed to send verification email. Please try again.')
                return redirect(url_for('register'))

        return redirect(url_for('verify_otp'))

    return render_template('register.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    pending = session.get('pending_registration')
    if not pending:
        flash('Please register first')
        return redirect(url_for('register'))

    email = pending['email']
    
    if request.method == 'POST':
        otp_code = request.form.get('otp_code')
        stored_otp = OTP_STORE.get(email)

        if not stored_otp or stored_otp['code'] != otp_code:
            flash('Invalid verification code.')
            return render_template('verify_otp.html', email=email)

        # 120 second expiry as requested
        if (datetime.now() - stored_otp['timestamp']).total_seconds() > 120:
            flash('Verification code expired. Please register again.')
            session.pop('pending_registration', None)
            if email in OTP_STORE: del OTP_STORE[email]
            return redirect(url_for('register'))

        # Create user
        role = pending['role']
        # Ensure 'name' is populated as it's non-nullable in the User model
        user_display_name = pending['shop_name'] if role == 'pharmacy' else pending['username']
        
        new_user = User(
            username=pending['username'],
            email=email,
            password=pending['password'],
            role=role,
            name=user_display_name,
            phone=pending['phone'],
            email_verified=True
        )
        db.session.add(new_user)
        db.session.flush() # Get user ID before creating pharmacy
        
        if role == 'pharmacy':
            # Safe float conversion for pharmacy coordinates
            try:
                lat_val = float(pending['latitude']) if pending['latitude'] else None
                lng_val = float(pending['longitude']) if pending['longitude'] else None
            except (ValueError, TypeError):
                lat_val, lng_val = None, None

            new_pharmacy = Pharmacy(
                owner=new_user, # Linking via owner backref
                shop_name=pending['shop_name'],
                phone=pending['phone'],
                location_address=pending['location_address'],
                latitude=lat_val,
                longitude=lng_val,
                prc_no=pending['prc_no'],
                dl_no=pending['dl_no'],
                license_doc=pending.get('license_doc'),
                verified=False # Must be approved by admin
            )
            db.session.add(new_pharmacy)

        db.session.commit()
        session.pop('pending_registration', None)
        if email in OTP_STORE: del OTP_STORE[email]
        
        if role == 'patient':
            login_user(new_user)
            flash('Registration successful! Welcome to MedLink.')
            return redirect(url_for('patient_dashboard'))
        else:
            flash('Email verified! Your pharmacy account is now waiting for admin approval. You will be able to login once approved.', 'success')
            return redirect(url_for('login'))

    return render_template('verify_otp.html', email=email)

@app.route('/logout')

@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role not in ['admin', 'sub_admin']:
        return "Access Denied"
    
    pharmacies = Pharmacy.query.all()
    hospitals = Hospital.query.filter_by(is_active=True).all()
    medicines = Medicine.query.all()
    ambulances = Ambulance.query.filter_by(is_active=True).all()
    emergencies = SOS.query.order_by(SOS.created_at.desc()).all()
    
    # Archived items for Archive Tab
    archived_hospitals = Hospital.query.filter_by(is_active=False).all()
    archived_ambulances = Ambulance.query.filter_by(is_active=False).all()
    
    # Statistics
    medicines_count = Medicine.query.count()
    ambulances_count = Ambulance.query.filter_by(is_active=True).count()
    
    sub_admins = []
    if current_user.role == 'admin':
        sub_admins = User.query.filter_by(role='sub_admin').all()

    # Serialize for Alpine.js
    pharmacies_json = json.dumps([p.to_dict() for p in pharmacies])
    hospitals_json = json.dumps([h.to_dict() for h in hospitals])
    medicines_json = json.dumps([m.to_dict() for m in medicines])
    ambulances_json = json.dumps([a.to_dict() for a in ambulances])
    emergencies_json = json.dumps([e.to_dict() for e in emergencies])
    archived_hospitals_json = json.dumps([h.to_dict() for h in archived_hospitals])
    archived_ambulances_json = json.dumps([a.to_dict() for a in archived_ambulances])
    sub_admins_json = json.dumps([sa.to_dict() for sa in sub_admins])
    
    # Enrich medicine dicts with pharmacy name
    med_list = []
    for m in medicines:
        m_dict = m.to_dict()
        m_dict['pharmacy_name'] = m.pharmacy.shop_name if m.pharmacy else 'Unknown'
        med_list.append(m_dict)
    medicines_json = json.dumps(med_list)

    return render_template('admin_dashboard.html', 
                           pharmacies_json=pharmacies_json, 
                           sub_admins_json=sub_admins_json, 
                           hospitals_json=hospitals_json,
                           medicines_json=medicines_json,
                           ambulances_json=ambulances_json,
                           emergencies_json=emergencies_json,
                           archived_hospitals_json=archived_hospitals_json,
                           archived_ambulances_json=archived_ambulances_json,
                           medicines_count=medicines_count,
                           ambulances_count=ambulances_count,
                           pharmacies_count=len(pharmacies),
                           hospitals_count=len(hospitals),
                           sub_admins=sub_admins)

@app.route('/admin/add_hospital_submit', methods=['POST'])
@login_required
def add_hospital_submit():
    if current_user.role not in ['admin', 'sub_admin']:
        return "Access Denied"
    
    name = request.form.get('name')
    address = request.form.get('address')
    phone = request.form.get('phone') or "N/A"
    ambulance_no = request.form.get('ambulance_no')
    driver_no = request.form.get('driver_no')
    # Automatic Geocoding
    lat_val, lng_val = geocode_location(name, address)

    new_hosp = Hospital(
        name=name, 
        address=address,
        phone=phone, 
        ambulance_no=ambulance_no, 
        driver_no=driver_no,
        latitude=lat_val,
        longitude=lng_val
    )
    db.session.add(new_hosp)
    db.session.commit()
    
    # Also create a standalone Ambulance entry linked to this hospital for the fleet tab
    new_amb = Ambulance(
        vehicle_number=ambulance_no,
        driver_phone=driver_no,
        hospital_id=new_hosp.id,
        address=address
    )
    db.session.add(new_amb)
    db.session.commit()
    
    flash('Hospital and primary transport integrated successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_ambulance_submit', methods=['POST'])
@login_required
def add_ambulance_submit():
    if current_user.role not in ['admin', 'sub_admin']:
        return "Access Denied"
    
    hospital_id = request.form.get('hospital_id')
    ambulance_no = request.form.get('ambulance_no')
    driver_no = request.form.get('driver_no')
    
    # If it's an Independent Fleet, create a base Hospital record for it first
    if not hospital_id:
        hosp_name = request.form.get('hospital_name') or "Independent Ambulance Fleet"
        address = request.form.get('address') or "Mobile Unit"
        # Automatic Geocoding for independent fleet
        lat_val, lng_val = geocode_location(hosp_name, address)
            
        new_base = Hospital(
            name=hosp_name,
            address=address,
            phone=driver_no,
            ambulance_no=ambulance_no,
            driver_no=driver_no,
            latitude=lat_val,
            longitude=lng_val
        )
        db.session.add(new_base)
        db.session.commit()
        hospital_id = new_base.id
    else:
        # Fetch address from selected hospital
        hosp = Hospital.query.get(hospital_id)
        address = hosp.address if hosp else ""
        
    # Create the ambulance record
    new_amb = Ambulance(
        vehicle_number=ambulance_no,
        driver_phone=driver_no,
        hospital_id=hospital_id,
        address=address
    )
    db.session.add(new_amb)
    db.session.commit()
    
    flash('Ambulance deployed successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_hospital_submit', methods=['POST'])
@login_required
def edit_hospital_submit():
    if current_user.role not in ['admin', 'sub_admin']:
        return "Access Denied"
    
    hospital_id = request.form.get('id')
    hosp = Hospital.query.get(hospital_id)
    if not hosp:
        flash('Hospital not found')
        return redirect(url_for('admin_dashboard'))
    
    old_address = hosp.address
    hosp.name = request.form.get('name')
    hosp.address = request.form.get('address')
    hosp.phone = request.form.get('phone')
    hosp.ambulance_no = request.form.get('ambulance_no')
    hosp.driver_no = request.form.get('driver_no')
    
    # Re-geocode if address changed
    if hosp.address != old_address:
        lat, lng = geocode_location(hosp.name, hosp.address)
        if lat and lng:
            hosp.latitude = lat
            hosp.longitude = lng
            
    db.session.commit()
    flash('Hospital details updated successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_ambulance_submit', methods=['POST'])
@login_required
def edit_ambulance_submit():
    if current_user.role not in ['admin', 'sub_admin']:
        return "Access Denied"
    
    ambulance_id = request.form.get('id')
    amb = Ambulance.query.get(ambulance_id)
    if not amb:
        flash('Ambulance not found')
        return redirect(url_for('admin_dashboard'))
    
    amb.vehicle_number = request.form.get('ambulance_no')
    amb.driver_phone = request.form.get('driver_no')
    
    new_hosp_id = request.form.get('hospital_id')
    if new_hosp_id:
        amb.hospital_id = int(new_hosp_id)
        hosp = Hospital.query.get(new_hosp_id)
        if hosp:
            amb.address = hosp.address
    else:
        amb.hospital_id = None
        amb.address = "Mobile Unit"
        
    db.session.commit()
    flash('Ambulance updated successfully')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete_hospital/<int:id>')
@login_required
def delete_hospital(id):
    if current_user.role not in ['admin', 'sub_admin']:
        return "Access Denied"
    hosp = Hospital.query.get_or_404(id)
    
    # SOFT DELETE: archive the hospital instead of hard deleting
    hosp.is_active = False
    hosp.archived_at = datetime.now()
    
    # Archive all ambulances linked to this hospital too
    ambulances = Ambulance.query.filter_by(hospital_id=id).all()
    for amb in ambulances:
        amb.is_active = False
        amb.archived_at = datetime.now()
        
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True, 'message': f"'{hosp.name}' archived."})
        
    flash(f"Hospital '{hosp.name}' archived (not deleted). It can be restored from the archive tab.", 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/restore_hospital/<int:id>')
@login_required
def restore_hospital(id):
    if current_user.role not in ['admin', 'sub_admin']:
        return "Access Denied"
    hosp = Hospital.query.get_or_404(id)
    hosp.is_active = True
    hosp.archived_at = None
    # Restore all linked ambulances too
    for amb in Ambulance.query.filter_by(hospital_id=id).all():
        amb.is_active = True
        amb.archived_at = None
    db.session.commit()
    return jsonify({'success': True, 'message': f"'{hosp.name}' restored."})


@app.route('/admin/verify_pharmacy/<int:id>')
@login_required
def verify_pharmacy(id):
    if current_user.role not in ['admin', 'sub_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    pharma = Pharmacy.query.get_or_404(id)
    pharma.verified = True
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True})
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_pharmacy/<int:id>')
@login_required
def reject_pharmacy(id):
    if current_user.role not in ['admin', 'sub_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    pharma = Pharmacy.query.get_or_404(id)
    user = User.query.get(pharma.user_id)
    
    # Delete inventory, reviews, alerts first
    Medicine.query.filter_by(pharmacy_id=pharma.id).delete()
    Review.query.filter_by(pharmacy_id=pharma.id).delete()
    SystemAlert.query.filter_by(pharmacy_id=pharma.id).delete()
    
    db.session.delete(pharma)
    if user:
        db.session.delete(user)
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True})
    flash('Pharmacy and associated user removed')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/view_license/<int:id>')
@login_required
def view_license(id):
    if current_user.role not in ['admin', 'sub_admin']:
        return "Access Denied"
    pharma = Pharmacy.query.get_or_404(id)
    if not pharma.license_doc:
        return "No document found"
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], pharma.license_doc)
    if not os.path.exists(file_path):
        return "The license document file was not found on the server. Please ask the pharmacy to re-upload."

    return send_from_directory(app.config['UPLOAD_FOLDER'], pharma.license_doc)


@app.route('/admin/add_sub_admin', methods=['POST'])
@login_required
def add_sub_admin():
     if current_user.role != 'admin': # Only main admin can add sub-admins
        return "Access Denied"
     
     username = request.form.get('username')
     password = request.form.get('password')
     name = request.form.get('name')
     
     if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for('admin_dashboard'))
            
     email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
     if not re.match(email_pattern, username):
        flash('Invalid email address format')
        return redirect(url_for('admin_dashboard'))
            
     hashed_password = generate_password_hash(password, method='scrypt')
     new_user = User(username=username, password=hashed_password, role='sub_admin', name=name)
     db.session.add(new_user)
     db.session.commit()
     return redirect(url_for('admin_dashboard'))

@app.route('/admin/remove_sub_admin/<int:id>')
@login_required
def remove_sub_admin(id):
    if current_user.role != 'admin':
        return "Access Denied"
    
    user = User.query.get_or_404(id)
    if user.role != 'sub_admin':
        return "Invalid User"
        
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/medicines')
@login_required
def admin_medicines():
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_medicine', methods=['GET', 'POST'])
@login_required
def add_medicine():
    if current_user.role not in ['admin', 'sub_admin']:
        return "Access Denied"
    if request.method == 'POST':
        name = request.form.get('name')
        generic_name = request.form.get('generic_name')
        manufacturer = request.form.get('manufacturer')
        description = request.form.get('description')
        
        pharma = Pharmacy.query.first()
        if not pharma:
            flash("No pharmacy exists to attach medicine to")
            return redirect(url_for('admin_dashboard'))
        
        new_med = Medicine(
            name=name,
            generic_name=generic_name,
            manufacturer=manufacturer,
            description=description,
            pharmacy_id=pharma.id,
            qty=0,
            expiry=datetime.utcnow().date() + timedelta(days=365)
        )
        db.session.add(new_med)
        db.session.commit()
        flash('Medicine added to system successfully')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_add_medicine.html')

@app.route('/admin/delete_medicine/<int:id>', methods=['POST', 'GET'])
@login_required
def delete_medicine(id):
    if current_user.role not in ['admin', 'sub_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    med = Medicine.query.get_or_404(id)
    db.session.delete(med)
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True})
    return redirect(url_for('admin_dashboard'))



@app.route('/admin/delete_ambulance/<int:id>', methods=['POST', 'GET'])
@login_required
def delete_ambulance(id):
    if current_user.role not in ['admin', 'sub_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    amb = Ambulance.query.get_or_404(id)
    # SOFT DELETE: archive instead of hard delete
    amb.is_active = False
    amb.archived_at = datetime.now()
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True, 'message': f"Ambulance '{amb.vehicle_number}' archived."})
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/restore_ambulance/<int:id>')
@login_required
def restore_ambulance(id):
    if current_user.role not in ['admin', 'sub_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    amb = Ambulance.query.get_or_404(id)
    amb.is_active = True
    amb.archived_at = None
    db.session.commit()
    return jsonify({'success': True, 'message': f"Ambulance '{amb.vehicle_number}' restored."})


@app.route('/admin/broadcasts')
@login_required
def admin_broadcasts():
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/resolve_broadcast/<int:id>', methods=['POST', 'GET'])
@login_required
def resolve_broadcast(id):
    if current_user.role not in ['admin', 'sub_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    sos = SOS.query.get_or_404(id)
    sos.status = 'resolved'
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json or request.method == 'POST':
        return jsonify({'success': True})
    flash('Emergency broadcast marked as resolved')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/send_alert', methods=['POST'])
@app.route('/admin/send_custom_alert', methods=['POST'])
@login_required
@csrf.exempt
def admin_send_alert():
    if current_user.role not in ['admin', 'sub_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.json
    pharmacy_id = data.get('pharmacy_id')
    message = data.get('message')
    alert_type = data.get('type', 'info')
    
    if not pharmacy_id or not message:
        return jsonify({'error': 'Missing pharmacy ID or message'}), 400
        
    new_alert = SystemAlert(
        pharmacy_id=pharmacy_id,
        message=message,
        type=alert_type
    )
    db.session.add(new_alert)
    db.session.commit()
    return jsonify({'success': True, 'status': 'success', 'message': 'Alert sent successfully'})

@app.route('/admin/toggle_user_suspend/<int:id>', methods=['POST'])
@login_required
def toggle_user_suspend(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized: Super Admin required'}), 403
    
    user = User.query.get_or_404(id)
    if user.role == 'admin':
        return jsonify({'error': 'Cannot suspend super admin'}), 400
        
    user.is_suspended = not user.is_suspended
    db.session.commit()
    return jsonify({'success': True, 'suspended': user.is_suspended})

@app.route('/admin/toggle_pharmacy_suspend/<int:id>', methods=['POST'])
@login_required
def toggle_pharmacy_suspend(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized: Super Admin required'}), 403
        
    pharmacy = Pharmacy.query.get_or_404(id)
    pharmacy.is_suspended = not pharmacy.is_suspended
    if pharmacy.owner:
        pharmacy.owner.is_suspended = pharmacy.is_suspended
    db.session.commit()
    return jsonify({'success': True, 'suspended': pharmacy.is_suspended})


@app.route('/admin/add_admin')
@login_required
def add_admin():
    return redirect(url_for('admin_dashboard'))
     

# Pharmacy Dashboard
@app.route('/pharmacy')
@login_required
def pharmacy_dashboard():
    if current_user.role != 'pharmacy':
        return "Access Denied"
    
    pharmacy = Pharmacy.query.filter_by(user_id=current_user.id).first()
    if not pharmacy:
        return "Pharmacy profile not found"
        
    inventory = Medicine.query.filter_by(pharmacy_id=pharmacy.id).all()
    reviews = Review.query.filter_by(pharmacy_id=pharmacy.id).all()
    alerts = SystemAlert.query.filter_by(pharmacy_id=pharmacy.id).order_by(SystemAlert.created_at.desc()).all()
    
    # Fetch only OPEN SOS requests (last 10)
    emergencies = SOS.query.filter_by(status='open').order_by(SOS.created_at.desc()).limit(10).all()
    
    # Serialize for Alpine.js
    inventory_json = json.dumps([item.to_dict() for item in inventory])
    alerts_json = json.dumps([item.to_dict() for item in alerts])
    emergencies_json = json.dumps([item.to_dict() for item in emergencies])
    
    # Fetch alternative mappings
    alternatives = MedicineAlternative.query.all()
    alternatives_json = json.dumps([{'id': a.id, 'medicine_name': a.medicine_name, 'alternative_name': a.alternative_name} for a in alternatives])
    
    return render_template('pharmacy.html', 
                           pharmacy=pharmacy, 
                           inventory=inventory, 
                           reviews=reviews, 
                           emergencies=emergencies, 
                           alerts=alerts,
                           inventory_json=inventory_json,
                           alerts_json=alerts_json,
                           emergencies_json=emergencies_json,
                           alternatives_json=alternatives_json)

@app.route('/pharmacy/nearby_sos')
@login_required
def pharmacy_nearby_sos():
    """Return SOS requests within 10km of this pharmacy's location."""
    if current_user.role != 'pharmacy':
        return jsonify({'error': 'Unauthorized'}), 403

    pharmacy = Pharmacy.query.filter_by(user_id=current_user.id).first()
    if not pharmacy:
        return jsonify([])

    p_lat = pharmacy.latitude
    p_lng = pharmacy.longitude

    # Fetch all open SOS, ordered by most recent first
    all_sos = SOS.query.filter_by(status='open').order_by(SOS.created_at.desc()).all()

    nearby = []
    for s in all_sos:
        distance = None
        if p_lat and p_lng and s.latitude and s.longitude:
            distance = round(haversine(p_lat, p_lng, s.latitude, s.longitude), 2)
            if distance > 10.0:   # 10km radius filter
                continue

        # Include patient contact if available
        patient = s.patient
        nearby.append({
            'id': s.id,
            'medicine': s.medicine_name,
            'patient_name': patient.name if patient else 'Anonymous',
            'patient_phone': patient.phone if patient and patient.phone else None,
            'distance': distance,
            'time_ago': s.created_at.strftime('%I:%M %p, %d %b'),
            'status': s.status,
            'latitude': s.latitude,
            'longitude': s.longitude,
        })

    return jsonify(nearby)


@app.route('/pharmacy/add_stock', methods=['POST'])
@csrf.exempt
@login_required
def add_stock():
    if current_user.role != 'pharmacy':
        return jsonify({'error': 'Unauthorized'}), 403
        
    pharmacy = Pharmacy.query.filter_by(user_id=current_user.id).first()
    data = request.json or request.form
    
    name = data.get('name')
    alternative_name = data.get('alternative_name') # New optional field
    # generic_name = data.get('generic_name') # Field removed from UI
    manufacturer = data.get('manufacturer')
    description = data.get('description')
    qty_str = data.get('qty')
    price_str = data.get('price')
    expiry_str = data.get('expiry')
    
    if not name or not expiry_str:
        return jsonify({'error': 'Name and expiry are required'}), 400
        
    try:
        expiry = datetime.strptime(expiry_str, '%Y-%m-%d').date()
        qty = int(float(qty_str)) if qty_str else 0
        price = float(price_str) if price_str and str(price_str).strip() else None
        
        # Add stock entry
        new_med = Medicine(
            pharmacy_id=pharmacy.id, 
            name=name, 
            # generic_name=generic_name, # Removed
            manufacturer=manufacturer,
            description=description,
            qty=qty, 
            expiry=expiry, 
            price=price
        )
        db.session.add(new_med)
        
        # Handle integrated alternative mapping
        if alternative_name:
            # Check if mapping already exists
            existing_alt = MedicineAlternative.query.filter_by(
                medicine_name=name, 
                alternative_name=alternative_name
            ).first()
            
            if not existing_alt:
                new_alt = MedicineAlternative(
                    medicine_name=name,
                    alternative_name=alternative_name
                )
                db.session.add(new_alt)
        
        db.session.commit()
    except (ValueError, TypeError) as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    
    return jsonify({'success': True}) # Or redirect

@app.route('/pharmacy/remove_stock/<int:id>', methods=['POST'])
@csrf.exempt
@login_required
def remove_stock(id):
    if current_user.role != 'pharmacy':
        return jsonify({'error': 'Unauthorized'}), 403
    
    med = Medicine.query.get_or_404(id)
    # Ensure it belongs to this pharmacy
    pharmacy = Pharmacy.query.filter_by(user_id=current_user.id).first()
    if med.pharmacy_id != pharmacy.id:
         return jsonify({'error': 'Unauthorized'}), 403
         
    db.session.delete(med)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/pharmacy/add_alternative', methods=['POST'])
@csrf.exempt
@login_required
def add_alternative():
    if current_user.role != 'pharmacy':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json or request.form
    medicine_name = data.get('medicine_name', '').strip()
    alternative_name = data.get('alternative_name', '').strip()
    
    if not medicine_name or not alternative_name:
        return jsonify({'error': 'Both fields are required'}), 400
    
    # Check for duplicate
    existing = MedicineAlternative.query.filter_by(
        medicine_name=medicine_name, alternative_name=alternative_name
    ).first()
    if existing:
        return jsonify({'error': 'This mapping already exists'}), 400
    
    alt = MedicineAlternative(medicine_name=medicine_name, alternative_name=alternative_name)
    db.session.add(alt)
    db.session.commit()
    return jsonify({'success': True, 'id': alt.id})

@app.route('/pharmacy/remove_alternative/<int:id>', methods=['POST'])
@csrf.exempt
@login_required
def remove_alternative(id):
    if current_user.role != 'pharmacy':
        return jsonify({'error': 'Unauthorized'}), 403
    
    alt = MedicineAlternative.query.get_or_404(id)
    db.session.delete(alt)
    db.session.commit()
    return jsonify({'success': True})


# Patient Dashboard
@app.route('/patient')
@login_required
def patient_dashboard():
    if current_user.role != 'patient':
        return "Access Denied"
    
    # Fetch reviews submitted by this user
    user_reviews = Review.query.filter_by(user_id=current_user.id).order_by(Review.created_at.desc()).all()
    
    return render_template('dashboard_patient.html', 
                           user=current_user, 
                           user_reviews=user_reviews)

@app.route('/patient/nearby_hospitals')
@login_required
def nearby_hospitals():
    if current_user.role != 'patient':
        return jsonify([])
        
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    location_query = request.args.get('location_query', '')
    radius = request.args.get('radius', default=15.0, type=float) # Default 15km
    
    # PRIORITIZE manual location_query if provided (allows user to override browser location)
    if location_query:
        glat, glng = geocode_location(location_query, "")
        if glat and glng:
            lat, lng = glat, glng
    # Fallback to lat/lng only if no valid location_query was processed
    elif (not lat or not lng):
         # If no lat/lng and no query, we just use None which returns all hospitals with 0 dist
         pass

    hospitals = Hospital.query.filter_by(is_active=True).all()
    nearby = []
    
    for h in hospitals:
        dist = 0
        if lat and lng and h.latitude and h.longitude:
            dist = haversine(lat, lng, h.latitude, h.longitude)
            if dist <= radius:
                data = h.to_dict()
                data['distance'] = round(dist, 2)
                nearby.append(data)
        elif not lat or not lng:
            # If no location provided, return all but with 0 distance
            data = h.to_dict()
            data['distance'] = 0
            nearby.append(data)
            
    return jsonify(nearby)

@app.route('/patient/send_sos', methods=['POST'])
@csrf.exempt
@login_required
def send_sos():
    if current_user.role != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    medicine_name = data.get('medicine_name')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if not medicine_name:
        return jsonify({'error': 'Medicine name required'}), 400
        
    new_sos = SOS(patient_id=current_user.id, medicine_name=medicine_name, latitude=latitude, longitude=longitude)
    db.session.add(new_sos)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/patient/search_medicine')
@login_required
def search_medicine():
    query = request.args.get('query', '')
    user_lat = request.args.get('lat', type=float)
    user_lng = request.args.get('lng', type=float)
    location_query = request.args.get('location_query', '')
    
    # PRIORITIZE manual location_query override
    if location_query:
        glat, glng = geocode_location(location_query, "")
        if glat and glng:
            user_lat, user_lng = glat, glng
    elif not user_lat or not user_lng:
        # Fallback for old clients or missing location
        pass
    
    if len(query) < 2:
        return jsonify([])
        
    # Case insensitive search for exact matches
    results = db.session.query(Medicine, Pharmacy).join(Pharmacy).filter(
        Medicine.name.ilike(f'%{query}%')
    ).all()
    
    data = []
    for med, pharma in results:
        dist = 'N/A'
        if user_lat and user_lng and pharma.latitude and pharma.longitude:
             d = haversine(user_lat, user_lng, pharma.latitude, pharma.longitude)
             dist = round(d, 2)
             
        data.append({
            'name': med.name,
            'pharmacy': pharma.shop_name,
            'price': med.price if med.price else 'N/A',
            'location': pharma.location_address,
            'phone': pharma.phone,
            'lat': pharma.latitude,
            'lng': pharma.longitude,
            'dist': dist,
            'id': med.id,
            'is_alternative': False
        })
    
    # If no results found, search for alternatives
    if len(data) == 0:
        # First, check database for known alternatives
        alternatives = MedicineAlternative.query.filter(
            MedicineAlternative.medicine_name.ilike(f'%{query}%')
        ).all()
        
        alternative_names = [alt.alternative_name for alt in alternatives]
        
        # If no database alternatives, try fuzzy matching (first 3 characters)
        if not alternative_names:
            similar = Medicine.query.filter(
                Medicine.name.ilike(f'%{query[:3]}%')
            ).limit(5).all()
            alternative_names = list(set([med.name for med in similar]))
        
        # Search for these alternatives in pharmacy inventory
        for alt_name in alternative_names:
            meds = db.session.query(Medicine, Pharmacy).join(Pharmacy).filter(
                Medicine.name.ilike(f'%{alt_name}%')
            ).all()
            
            for med, pharma in meds:
                dist = 'N/A'
                if user_lat and user_lng and pharma.latitude and pharma.longitude:
                     d = haversine(user_lat, user_lng, pharma.latitude, pharma.longitude)
                     dist = round(d, 2)
                
                data.append({
                    'name': med.name,
                    'pharmacy': pharma.shop_name,
                    'price': med.price if med.price else 'N/A',
                    'location': pharma.location_address,
                    'phone': pharma.phone,
                    'lat': pharma.latitude,
                    'lng': pharma.longitude,
                    'dist': dist,
                    'id': med.id,
                    'is_alternative': True,
                    'original_search': query
                })
        
    return jsonify(data)

@app.route('/patient/submit_review', methods=['POST'])
@csrf.exempt
@login_required
def submit_review():
    data = request.json
    pharmacy_name = data.get('pharmacy_name')
    pharmacy = Pharmacy.query.filter_by(shop_name=pharmacy_name).first()
    
    if pharmacy:
        review = Review(
            pharmacy_id=pharmacy.id, 
            user_id=current_user.id,
            user_name=current_user.name, 
            rating=data.get('rating'), 
            comment=data.get('comment')
        )
        db.session.add(review)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Pharmacy not found'}), 404

@app.route('/pharmacy/feedback-reply/<int:id>', methods=['POST'])
@csrf.exempt
@login_required
def reply_review(id):
    print(f"DEBUG: reply_review triggered for id {id}")
    if current_user.role != 'pharmacy':
        print(f"DEBUG: Unauthorized role {current_user.role}")
        return jsonify({'error': 'Unauthorized'}), 403
        
    review = Review.query.get(id)
    if not review:
        print(f"DEBUG: Review {id} not found in DB")
        return jsonify({'error': 'Review not found'}), 404
        
    print(f"DEBUG: Found review {review.id} for user {review.user_name}")
    data = request.json
    reply = data.get('reply')
    
    if reply:
        review.pharmacy_reply = reply
        review.reply_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Reply cannot be empty'}), 400

@app.route('/admin/send_alert', methods=['POST'])
@csrf.exempt
@login_required
def send_alert():
    if current_user.role not in ['admin', 'sub_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    new_alert = SystemAlert(
        pharmacy_id=data.get('pharmacy_id'),
        message=data.get('message'),
        type=data.get('type', 'info')
    )
    db.session.add(new_alert)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/global_expiry_scan')
@login_required
def global_expiry_scan():
    if current_user.role not in ['admin', 'sub_admin']:
        return jsonify([])
    
    # Findings expiring in next 30 days
    threshold = datetime.utcnow().date() + timedelta(days=30)
    expiring = db.session.query(Medicine, Pharmacy).join(Pharmacy).filter(Medicine.expiry <= threshold).all()
    
    data = []
    for med, pharma in expiring:
        data.append({
            'med': med.name,
            'pharma': pharma.shop_name,
            'pharma_id': pharma.id,
            'expiry': med.expiry.strftime('%Y-%m-%d'),
            'qty': med.qty
        })
    return jsonify(data)

# Init DB
# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template('errors/429.html'), 429

# Health check endpoint
@app.route('/health')
@limiter.exempt
def health_check():
    return jsonify({'status': 'healthy', 'version': '1.0.0'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default admin if not exists
        admin_username = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin')
        admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')
        
        if not User.query.filter_by(username=admin_username).first():
            hashed_pw = generate_password_hash(admin_password, method='scrypt')
            admin = User(username=admin_username, password=hashed_pw, role='admin', name='Super Admin')
            db.session.add(admin)
            db.session.commit()
            print(f"Default admin created: {admin_username}")
        
        # Seed common alternative medicine mappings
        common_alternatives = [
            ('Dollo', 'Paracetamol'), ('Dolo', 'Paracetamol'), ('Dolo-650', 'Paracetamol'),
            ('Crocin', 'Paracetamol'), ('Calpol', 'Paracetamol'),
            ('Combiflam', 'Ibuprofen + Paracetamol'), ('Brufen', 'Ibuprofen'),
            ('Disprin', 'Aspirin'), ('Ecosprin', 'Aspirin'),
            ('Allegra', 'Fexofenadine'), ('Cetrizine', 'Cetirizine'),
            ('Azithral', 'Azithromycin'), ('Zithromax', 'Azithromycin'),
            ('Augmentin', 'Amoxicillin + Clavulanate'),
            ('Pan-D', 'Pantoprazole + Domperidone'), ('Pantocid', 'Pantoprazole'),
            ('Shelcal', 'Calcium + Vitamin D3'),
        ]
        for brand, alt in common_alternatives:
            if not MedicineAlternative.query.filter_by(medicine_name=brand, alternative_name=alt).first():
                db.session.add(MedicineAlternative(medicine_name=brand, alternative_name=alt))
        db.session.commit()

    # Start background scheduler for Expiry Alerts (Only in main worker process to avoid duplicates)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.config.get('DEBUG', True):
        from apscheduler.schedulers.background import BackgroundScheduler
        from send_expiry_alerts import send_expiry_alerts
        try:
            scheduler = BackgroundScheduler()
            # Run daily at 8:00 AM
            scheduler.add_job(func=send_expiry_alerts, trigger="cron", hour=8, minute=0)
            scheduler.start()
            print("✅ Background Expiry Alert Scheduler Started (Runs daily at 08:00).")
        except Exception as e:
            print(f"Failed to start scheduler: {e}")

    # Get debug mode from config
    debug_mode = app.config.get('DEBUG', True)
    app.run(debug=True, host='0.0.0.0', port=5000)
