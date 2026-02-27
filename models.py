from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True) # Added for SOS functionality
    email = db.Column(db.String(120), nullable=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'sub_admin', 'pharmacy', 'patient'
    name = db.Column(db.String(100), nullable=False)
    email_verified = db.Column(db.Boolean, default=True)  # True for existing users; new users set to False
    
    # Relationships
    pharmacy_details = db.relationship('Pharmacy', backref='owner', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'username': self.username,
            'role': self.role,
            'email': self.email,
            'phone': self.phone
        }

class Pharmacy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shop_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    dl_no = db.Column(db.String(50), nullable=True)
    prc_no = db.Column(db.String(50), nullable=True)
    license_doc = db.Column(db.String(255), nullable=True) # Filename of uploaded doc
    verified = db.Column(db.Boolean, default=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location_address = db.Column(db.String(255), nullable=True) # Added location address
    
    inventory = db.relationship('Medicine', backref='pharmacy', lazy=True)
    reviews = db.relationship('Review', backref='pharmacy', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'shop_name': self.shop_name,
            'phone': self.phone,
            'email': self.owner.email if self.owner else '',
            'dl_no': self.dl_no,
            'prc_no': self.prc_no,
            'verified': self.verified,
            'license_doc': self.license_doc,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'location_address': self.location_address
        }

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    generic_name = db.Column(db.String(100), nullable=True)
    manufacturer = db.Column(db.String(100), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    qty = db.Column(db.Integer, nullable=False)
    expiry = db.Column(db.Date, nullable=False)
    price = db.Column(db.Float, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'qty': self.qty,
            'price': self.price,
            'expiry': self.expiry.strftime('%Y-%m-%d') if self.expiry else None,
            'description': self.description,
            'manufacturer': self.manufacturer
        }

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.id'), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_name': self.user_name,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.strftime('%b %d')
        }

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=False)
    ambulance_no = db.Column(db.String(20), nullable=True)
    driver_name = db.Column(db.String(100), nullable=True)
    driver_no = db.Column(db.String(20), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'address': self.address,
            'ambulance_no': self.ambulance_no,
            'driver_name': self.driver_name,
            'driver_no': self.driver_no,
            'latitude': self.latitude,
            'longitude': self.longitude
        }

class SOS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medicine_name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='open') # 'open', 'resolved'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    patient = db.relationship('User', backref='sos_requests')

    def to_dict(self):
        return {
            'id': self.id,
            'medicine_name': self.medicine_name,
            'patient_name': self.patient.name if self.patient else 'Unknown',
            'time': self.created_at.strftime("%H:%M"),
            'time_ago': self.created_at.strftime("%Y-%m-%d %H:%M"),
            'phone': self.patient.phone or self.patient.username if self.patient else '',
            'status': self.status,
            'latitude': self.latitude,
            'longitude': self.longitude
        }

class Ambulance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(50), nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    driver_phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    area = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_number': self.vehicle_number,
            'driver_name': self.driver_name,
            'driver_phone': self.driver_phone,
            'address': self.address,
            'area': self.area
        }

class SystemAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(50), default='info') # 'info', 'warning', 'danger'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    pharmacy = db.relationship('Pharmacy', backref='alerts')

    def to_dict(self):
        return {
            'id': self.id,
            'msg': self.message,
            'type': self.type,
            'time': self.created_at.strftime("%b %d, %H:%M")
        }

class MedicineAlternative(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicine_name = db.Column(db.String(100), nullable=False)  # Brand name (e.g., "Dolo")
    alternative_name = db.Column(db.String(100), nullable=False)  # Generic/Alternative (e.g., "Paracetamol")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
