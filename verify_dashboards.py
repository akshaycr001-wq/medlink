
import unittest
import json
from app import app, db, User, Pharmacy, SystemAlert
from werkzeug.security import generate_password_hash

class TestPremiumDashboards(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        
        self.admin_email = "admin_test@medlink.com"
        self.pharma_email = "pharma_test@medlink.com"
        self.patient_email = "patient_test@medlink.com"
        
        # Admin
        admin = User(username=self.admin_email, password=generate_password_hash('pass123'), role='admin', name='Main Admin')
        db.session.add(admin)
        
        # Pharmacy
        pharma_user = User(username=self.pharma_email, password=generate_password_hash('pass123'), role='pharmacy', name='Shop Owner')
        db.session.add(pharma_user)
        db.session.flush()
        p = Pharmacy(user_id=pharma_user.id, shop_name='Global Meds', phone='0987654321', verified=False)
        db.session.add(p)
        
        # Patient
        patient_user = User(username=self.patient_email, password=generate_password_hash('pass123'), role='patient', name='Joe Patient')
        db.session.add(patient_user)
        
        db.session.commit()
        self.pharma_id = p.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email, admin=False):
        path = '/admin_login' if admin else '/login'
        data = {'username' if admin else 'identifier': email, 'password': 'pass123'}
        res = self.client.post(path, data=data, follow_redirects=True)
        # Success if we see the flash OR a dashboard title
        success_indicators = [b'Logged in successfully', b'Terminal', b'Control']
        if not any(x in res.data for x in success_indicators):
             print(f"Login might have failed for {email} on {path}. Response snippet: {res.data[:500]}")
        return res

    def test_admin_dashboard_render(self):
        login_res = self.login(self.admin_email, admin=True)
        print(f"\nAdmin Login Status: {login_res.status_code}")
        res = self.client.get('/admin')
        self.assertEqual(res.status_code, 200, f"Expected 200 for /admin but got {res.status_code}. Response: {res.data[:200]}")
        self.assertIn(b'MedLink Control', res.data)

    def test_pharmacy_dashboard_render(self):
        login_res = self.login(self.pharma_email)
        print(f"\nPharma Login Status: {login_res.status_code}")
        res = self.client.get('/pharmacy')
        self.assertEqual(res.status_code, 200, f"Expected 200 for /pharmacy but got {res.status_code}. Response: {res.data[:200]}")
        self.assertIn(b'Pharmacy Terminal', res.data)

    def test_patient_dashboard_render(self):
        login_res = self.login(self.patient_email)
        print(f"\nPatient Login Status: {login_res.status_code}")
        res = self.client.get('/patient')
        self.assertEqual(res.status_code, 200, f"Expected 200 for /patient but got {res.status_code}. Response: {res.data[:200]}")
        self.assertIn(b'Patient Terminal', res.data)

    def test_admin_send_alert(self):
        self.login(self.admin_email, admin=True)
        res = self.client.post('/admin/send_alert', 
                               data=json.dumps({
                                   'pharmacy_id': self.pharma_id,
                                   'message': 'System Maintenance Tonight',
                                   'type': 'info'
                               }),
                               content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])

if __name__ == '__main__':
    unittest.main()
