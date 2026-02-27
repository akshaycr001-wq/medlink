from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
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

# Security headers (only enforce HTTPS in production)
if env == 'production':
    Talisman(app, force_https=True, strict_transport_security=True)
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
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user:
            if check_password_hash(user.password, password):
                if user.role in ['admin', 'sub_admin']:
                    flash('Please use the Admin Portal', 'error')
                    return redirect(url_for('admin_login'))
                
                # Check email verification
                if not getattr(user, 'email_verified', True):
                    flash('Please verify your email before logging in. Check the server console for the verification link.')
                    return redirect(url_for('login'))

                login_user(user)
                if user.role == 'pharmacy':
                    return redirect(url_for('pharmacy_dashboard'))
                elif user.role == 'patient':
                    return redirect(url_for('patient_dashboard'))
            else:
                flash('Incorrect password. Please try again or use Forgot Password.')
        else:
            flash('Username not found. Please register or check your credentials.')
            
    return render_template('login.html')

# --- Password Reset Token Store (in-memory; swap to DB/Redis for production) ---
_reset_tokens = {}  # { token: { 'user_id': int, 'expires': datetime } }
_verify_tokens = {}  # { token: { 'user_id': int, 'expires': datetime } }

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        user = User.query.filter_by(username=username).first()
        if user:
            token = secrets.token_urlsafe(32)
            _reset_tokens[token] = {
                'user_id': user.id,
                'expires': datetime.now() + timedelta(minutes=30)
            }
            reset_url = url_for('reset_password', token=token, _external=True)
            # Log the reset link (replace with real email in production)
            print(f'[PASSWORD RESET] User: {username} | Link: {reset_url}')
            app.logger.info(f'Password reset requested for {username}. Link: {reset_url}')
        # Always show success to prevent username enumeration
        flash('If that account exists, a recovery link has been sent. Check the server console.')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    token_data = _reset_tokens.get(token)
    if not token_data or token_data['expires'] < datetime.now():
        _reset_tokens.pop(token, None)
        flash('This reset link has expired or is invalid. Please request a new one.')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if len(password) < 6:
            flash('Password must be at least 6 characters.')
            return render_template('reset_password.html')
        if password != confirm:
            flash('Passwords do not match.')
            return render_template('reset_password.html')
        
        user = User.query.get(token_data['user_id'])
        if user:
            user.password = generate_password_hash(password, method='scrypt')
            db.session.commit()
            _reset_tokens.pop(token, None)
            flash('Password reset successful! You can now log in.')
            return redirect(url_for('login'))
    
    return render_template('reset_password.html')

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
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user:
            if check_password_hash(user.password, password):
                if user.role not in ['admin', 'sub_admin']:
                    flash('Access Denied: Admins Only')
                    return redirect(url_for('login'))
                    
                login_user(user)
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Incorrect admin password')
        else:
            flash('Admin ID not found')
            
    return render_template('admin_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('gmail')
        password = request.form.get('password')
        role = request.form.get('role') # 'patient' or 'pharmacy'
        name = request.form.get('name')
        phone = request.form.get('phone') # Added phone capture
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        if len(password) < 8:
            flash('Password must be at least 8 characters long')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='scrypt')
        
        # Capture name based on role
        if role == 'pharmacy':
            name = request.form.get('shop_name')
        else:
            name = request.form.get('name')
            
        new_user = User(username=username, phone=phone, email=email, password=hashed_password, role=role, name=name, email_verified=False)
        db.session.add(new_user)
        db.session.commit()
        
        # Issue email verification token
        verify_token = secrets.token_urlsafe(32)
        _verify_tokens[verify_token] = {
            'user_id': new_user.id,
            'expires': datetime.now() + timedelta(hours=24)
        }
        verify_url = url_for('verify_email', token=verify_token, _external=True)
        print(f'[EMAIL VERIFY] User: {username} | Link: {verify_url}')
        app.logger.info(f'Verification link for {username}: {verify_url}')
        
        if role == 'pharmacy':
            # Create associated Pharmacy record
            shop_name = request.form.get('shop_name')
            phone = request.form.get('phone')
            dl_no = request.form.get('dl_no')
            prc_no = request.form.get('prc_no')
            
            if not phone or not phone.isdigit() or len(phone) != 10:
                flash('Invalid phone number. Must be 10 digits.')
                return redirect(url_for('register'))

            # Handle File Upload (Optional)
            license_doc_name = None
            if 'license_doc' in request.files:
                file = request.files['license_doc']
                if file and file.filename != '':
                    if allowed_file(file.filename):
                        filename = secure_filename(f"DL_{new_user.id}_{file.filename}")
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        license_doc_name = filename
                    else:
                        flash('Invalid file type for license document.')
                        return redirect(url_for('register'))

            location_address = request.form.get('location_address')
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')
            
            # Convert lat/long to float if present
            lat = float(latitude) if latitude else None
            lng = float(longitude) if longitude else None

            new_pharmacy = Pharmacy(
                user_id=new_user.id, 
                shop_name=shop_name, 
                phone=phone, 
                dl_no=dl_no,
                prc_no=prc_no,
                license_doc=license_doc_name,
                location_address=location_address, 
                latitude=lat, 
                longitude=lng
            )
            db.session.add(new_pharmacy)
            db.session.commit()
            
        flash('Registration successful, please login.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

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
    hospitals = Hospital.query.all()
    medicines = Medicine.query.all()
    ambulances = Ambulance.query.all()
    emergencies = SOS.query.order_by(SOS.created_at.desc()).all()
    
    # Statistics
    medicines_count = Medicine.query.count()
    ambulances_count = Ambulance.query.count()
    
    sub_admins = []
    if current_user.role == 'admin':
        sub_admins = User.query.filter_by(role='sub_admin').all()

    # Serialize for Alpine.js
    pharmacies_json = json.dumps([p.to_dict() for p in pharmacies])
    hospitals_json = json.dumps([h.to_dict() for h in hospitals])
    medicines_json = json.dumps([m.to_dict() for m in medicines])
    ambulances_json = json.dumps([a.to_dict() for a in ambulances])
    emergencies_json = json.dumps([e.to_dict() for e in emergencies])
    sub_admins_json = json.dumps([sa.to_dict() for sa in sub_admins])
    
    # Helper to get pharmacy name for medicine list 
    # (Medicine.to_dict doesn't include pharmacy name by default, let's add it client side or here)
    # Actually, let's enrich medicine dicts with pharmacy name here
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
                           medicines_count=medicines_count,
                           ambulances_count=ambulances_count,
                           pharmacies_count=len(pharmacies),
                           hospitals_count=len(hospitals))

@app.route('/admin/add_hospital_submit', methods=['POST'])
@login_required
def add_hospital_submit():
    if current_user.role not in ['admin', 'sub_admin']:
        return "Access Denied"
    
    name = request.form.get('name')
    address = request.form.get('address')
    phone = request.form.get('phone') or "N/A"
    ambulance_no = request.form.get('ambulance_no')
    driver_name = request.form.get('driver_name')
    driver_no = request.form.get('driver_no')
    lat = request.form.get('latitude')
    lng = request.form.get('longitude')
    
    new_hosp = Hospital(
        name=name, 
        address=address,
        phone=phone, 
        ambulance_no=ambulance_no, 
        driver_name=driver_name, 
        driver_no=driver_no,
        latitude=float(lat) if lat else None,
        longitude=float(lng) if lng else None
    )
    db.session.add(new_hosp)
    db.session.commit()
    
    # Also create a standalone Ambulance entry linked to this hospital for the fleet tab
    new_amb = Ambulance(
        vehicle_number=ambulance_no,
        driver_name=driver_name,
        driver_phone=driver_no,
        hospital_id=new_hosp.id,
        address=address
    )
    db.session.add(new_amb)
    db.session.commit()
    
    flash('Hospital and primary transport integrated successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_hospital/<int:id>')
@login_required
def delete_hospital(id):
    if current_user.role not in ['admin', 'sub_admin']:
        return "Access Denied"
    hosp = Hospital.query.get_or_404(id)
    db.session.delete(hosp)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

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

@app.route('/admin/ambulances')
@login_required
def admin_ambulances():
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_ambulance_submit', methods=['POST'])
@login_required
def add_ambulance_submit():
    if current_user.role not in ['admin', 'sub_admin']:
        return "Access Denied"
    veh_no = request.form.get('ambulance_no')
    driver = request.form.get('driver_name')
    phone = request.form.get('driver_no')
    hosp_id = request.form.get('hospital_id')
    
    new_amb = Ambulance(
        vehicle_number=veh_no,
        driver_name=driver,
        driver_phone=phone,
        hospital_id=hosp_id if hosp_id else None
    )
    db.session.add(new_amb)
    db.session.commit()
    flash('Ambulance driver deployed successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_ambulance/<int:id>', methods=['POST', 'GET'])
@login_required
def delete_ambulance(id):
    if current_user.role not in ['admin', 'sub_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    amb = Ambulance.query.get_or_404(id)
    db.session.delete(amb)
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True})
    return redirect(url_for('admin_dashboard'))

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

@app.route('/admin/add_admin', methods=['GET', 'POST'])
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
    
    return render_template('pharmacy.html', 
                           pharmacy=pharmacy, 
                           inventory=inventory, 
                           reviews=reviews, 
                           emergencies=emergencies, 
                           alerts=alerts,
                           inventory_json=inventory_json,
                           alerts_json=alerts_json,
                           emergencies_json=emergencies_json)

@app.route('/pharmacy/add_stock', methods=['POST'])
@csrf.exempt
@login_required
def add_stock():
    if current_user.role != 'pharmacy':
        return jsonify({'error': 'Unauthorized'}), 403
        
    pharmacy = Pharmacy.query.filter_by(user_id=current_user.id).first()
    data = request.json or request.form
    
    name = data.get('name')
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
        qty = int(qty_str) if qty_str else 0
        price = float(price_str) if price_str and str(price_str).strip() else None
        
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
        db.session.commit()
    except (ValueError, TypeError) as e:
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


# Patient Dashboard
@app.route('/patient')
@login_required
def patient_dashboard():
    if current_user.role != 'patient':
        return "Access Denied"
    
    return render_template('dashboard_patient.html', user=current_user)

@app.route('/patient/nearby_hospitals')
@login_required
def nearby_hospitals():
    if current_user.role != 'patient':
        return jsonify([])
        
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', default=15.0, type=float) # Default 15km
    
    hospitals = Hospital.query.all()
    nearby = []
    
    for h in hospitals:
        dist = 0
        if lat and lng and h.latitude and h.longitude:
            dist = haversine(lat, lng, h.latitude, h.longitude)
            if dist <= radius:
                nearby.append({
                    'id': h.id,
                    'name': h.name,
                    'phone': h.phone,
                    'ambulance_no': h.ambulance_no,
                    'driver_name': h.driver_name,
                    'driver_no': h.driver_no,
                    'latitude': h.latitude,
                    'longitude': h.longitude,
                    'distance': round(dist, 2)
                })
        elif not lat or not lng:
            # If no location provided, return all but with 0 distance
            nearby.append({
                'id': h.id,
                'name': h.name,
                'phone': h.phone,
                'ambulance_no': h.ambulance_no,
                'driver_name': h.driver_name,
                'driver_no': h.driver_no,
                'latitude': h.latitude,
                'longitude': h.longitude,
                'distance': 0
            })
            
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
    # Implementation for reviews
    data = request.json
    pharmacy_name = data.get('pharmacy_name')
    # Find pharmacy by name or pass ID
    pharmacy = Pharmacy.query.filter_by(shop_name=pharmacy_name).first()
    
    if pharmacy:
        review = Review(pharmacy_id=pharmacy.id, user_name=current_user.name, rating=data.get('rating'), comment=data.get('comment'))
        db.session.add(review)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': True})

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
    
    # Get debug mode from config
    debug_mode = app.config.get('DEBUG', False)
    app.run(debug=False, host='0.0.0.0', use_reloader=False)
