import os
# Set env var BEFORE importing app to skip default db init
os.environ['FLASK_TESTING'] = '1'
os.environ['RATELIMIT_ENABLED'] = 'False'

import unittest
import tempfile
from app import app, db, User, Pharmacy, Medicine, Review, Hospital
from werkzeug.security import generate_password_hash

class MedlinkTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_fd, cls.db_path = tempfile.mkstemp()
        # Use simple slash replacement for Windows compatibility
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + cls.db_path.replace('\\', '/')
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['RATELIMIT_ENABLED'] = False
        # Initialize the db app ONCE for all tests
        db.init_app(app)
        
    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        # Clean up temp file
        os.close(cls.db_fd)
        os.unlink(cls.db_path)

    def setUp(self):
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            # Create default admin for every test
            # Use scrypt to match app.py
            admin = User(username='admin', password=generate_password_hash('admin123', method='scrypt'), role='admin', name='Super Admin')
            db.session.add(admin)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def admin_login(self, username, password):
        return self.app.post('/admin_login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_admin_login(self):
        rv = self.admin_login('admin', 'admin123')
        # Check if admin dashboard content is present
        assert b'Pharmacy Network' in rv.data 

    def test_add_sub_admin(self):
        self.admin_login('admin', 'admin123')
        rv = self.app.post('/admin/add_sub_admin', data=dict(
            username='subadmin@medlink.com',
            password='subadmin123',
            name='Sub Admin User'
        ), follow_redirects=True)
        assert rv.status_code == 200
        with app.app_context():
            sub = User.query.filter_by(username='subadmin@medlink.com').first()
            assert sub is not None
            assert sub.role == 'sub_admin'

    def test_remove_sub_admin(self):
        self.admin_login('admin', 'admin123')
        # Create a sub admin via API
        self.app.post('/admin/add_sub_admin', data=dict(
            username='subtodelete@medlink.com',
            password='pass',
            name='Delete Me'
        ), follow_redirects=True)
        
        with app.app_context():
            sub = User.query.filter_by(username='subtodelete@medlink.com').first()
            sub_id = sub.id

        rv = self.app.get(f'/admin/remove_sub_admin/{sub_id}', follow_redirects=True)
        assert rv.status_code == 200
        
        with app.app_context():
            db.session.expire_all()
            sub = User.query.get(sub_id)
            assert sub is None

    def test_pharmacy_registration(self):
        rv = self.app.post('/register', data=dict(
            username='pharma1@medlink.com',
            password='password123',
            role='pharmacy',
            name='Pharma Owner',
            shop_name='Test Pharmacy',
            location_address='123 Main St',
            phone='1234567890',
            latitude='12.3456',
            longitude='78.9012'
        ), follow_redirects=True)
        # Should redirect to login
        assert b'Log in' in rv.data or b'Login' in rv.data 
        
        with app.app_context():
            p = Pharmacy.query.filter_by(shop_name='Test Pharmacy').first()
            assert p is not None
            assert p.verified == False # Pending verification
            assert p.latitude == 12.3456
            assert p.longitude == 78.9012

    def test_approve_pharmacy(self):
        # Register first
        self.app.post('/register', data=dict(
            username='pharma1@medlink.com',
            password='password123',
            role='pharmacy',
            name='Pharma Owner',
            shop_name='Test Pharmacy',
            location_address='123 Main St',
            phone='1234567890'
        ), follow_redirects=True)

        # Login as admin and approve
        self.admin_login('admin', 'admin123')
        
        with app.app_context():
            p = Pharmacy.query.filter_by(shop_name='Test Pharmacy').first()
            rv = self.app.get(f'/admin/verify_pharmacy/{p.id}', follow_redirects=True)
            
            p_verified = Pharmacy.query.get(p.id)
            assert p_verified.verified == True

    def test_add_medicine(self):
        # Setup pharmacy user and verify
        self.app.post('/register', data=dict(
            username='pharma_active@medlink.com',
            password='password123',
            role='pharmacy',
            name='Active Pharma Owner',
            shop_name='Active Pharmacy',
            location_address='456 Test Ave',
            phone='0987654321'
        ), follow_redirects=True)
        
        with app.app_context():
            u = User.query.filter_by(username='pharma_active@medlink.com').first()
            p = Pharmacy.query.filter_by(user_id=u.id).first()
            p.verified = True
            db.session.commit()
            
        self.login('pharma_active@medlink.com', 'password123')
        
        # NOTE: Potential issue with request.json in app.py logic
        # Sending JSON request
        rv = self.app.post('/pharmacy/add_stock', json=dict(
            name='Paracetamol',
            qty=100,
            expiry='2025-12-31'
        ), follow_redirects=True) 
        
        with app.app_context():
            med = Medicine.query.filter_by(name='Paracetamol').first()
            assert med is not None
            assert med.qty == 100

if __name__ == '__main__':
    unittest.main()
