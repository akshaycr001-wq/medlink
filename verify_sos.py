import os
os.environ['FLASK_TESTING'] = '1'
os.environ['RATELIMIT_ENABLED'] = 'False'
import unittest
import tempfile
from app import app, db, User, Pharmacy, SOS
from werkzeug.security import generate_password_hash

class SOSVerifyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_fd, cls.db_path = tempfile.mkstemp()
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + cls.db_path.replace('\\', '/')
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['RATELIMIT_ENABLED'] = False
        db.init_app(app)
        
    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        os.close(cls.db_fd)
        try:
            os.unlink(cls.db_path)
        except PermissionError:
            pass

    def setUp(self):
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            # Create a patient and a pharmacy
            patient = User(username='patient@test.com', password=generate_password_hash('pass'), role='patient', name='Test Patient')
            pharma_user = User(username='pharma@test.com', password=generate_password_hash('pass'), role='pharmacy', name='Pharma Owner')
            db.session.add_all([patient, pharma_user])
            db.session.commit()
            
            pharma = Pharmacy(user_id=pharma_user.id, shop_name='Test Pharma', phone='1122334455', verified=True)
            db.session.add(pharma)
            db.session.commit()
            self.patient_id = patient.id
            self.pharma_user_id = pharma_user.id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_sos_flow(self):
        # 1. Login as patient
        self.client.post('/login', data=dict(username='patient@test.com', password='pass'), follow_redirects=True)
        
        # 2. Send SOS
        rv = self.client.post('/patient/send_sos', json=dict(
            medicine_name='Insulin',
            latitude=10.0,
            longitude=20.0
        ))
        self.assertEqual(rv.status_code, 200)
        
        # 3. Verify SOS in DB
        with app.app_context():
            sos = SOS.query.filter_by(medicine_name='Insulin').first()
            self.assertIsNotNone(sos)
            self.assertEqual(sos.patient_id, self.patient_id)
            
        # 4. Login as pharmacy
        self.client.get('/logout')
        self.client.post('/login', data=dict(username='pharma@test.com', password='pass'), follow_redirects=True)
        
        # 5. Check pharmacy dashboard (should contain emergencies)
        rv = self.client.get('/pharmacy')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Insulin', rv.data)
        self.assertIn(b'Emergency Broadcasts', rv.data)

if __name__ == '__main__':
    unittest.main()
