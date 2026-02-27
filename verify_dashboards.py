
import unittest
import json
from app import app, db, User, Pharmacy, SystemAlert
from werkzeug.security import generate_password_hash

class TestAdminDashboard(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create unique users for this test run
        self.admin_email = "admin_test@medlink.com"
        self.pharma_email = "pharma_test@medlink.com"
        
        admin = User(username=self.admin_email, password=generate_password_hash('pass123'), role='admin', name='Main Admin')
        db.session.add(admin)
        
        pharma_user = User(username=self.pharma_email, password=generate_password_hash('pass123'), role='pharmacy', name='Shop Owner')
        db.session.add(pharma_user)
        db.session.flush()
        
        p = Pharmacy(user_id=pharma_user.id, shop_name='Global Meds', phone='0987654321', verified=False)
        db.session.add(p)
        db.session.commit()
        
        self.pharma_id = p.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login_admin(self):
        return self.client.post('/admin_login', data={'username': self.admin_email, 'password': 'pass123'}, follow_redirects=True)

    def test_admin_dashboard_render(self):
        self.login_admin()
        res = self.client.get('/admin')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Control Center', res.data)
        self.assertIn(b'Global Meds', res.data)

    def test_send_alert(self):
        self.login_admin()
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
        
        alert = SystemAlert.query.filter_by(pharmacy_id=self.pharma_id).first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.message, 'System Maintenance Tonight')

    def test_verify_pharmacy(self):
        self.login_admin()
        res = self.client.get(f'/admin/verify_pharmacy/{self.pharma_id}')
        self.assertEqual(res.status_code, 302)
        p = Pharmacy.query.get(self.pharma_id)
        self.assertTrue(p.verified)

if __name__ == '__main__':
    unittest.main()
