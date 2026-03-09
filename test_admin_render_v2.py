import os
import sys
from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_wtf.csrf import CSRFProtect

# Mocking the environment
app = Flask(__name__, template_folder='c:/Users/eldho/Downloads/Templatefolder/templates')
app.config['SECRET_KEY'] = 'test-key'
csrf = CSRFProtect(app)

class MockUser(UserMixin):
    def __init__(self):
        self.id = 1
        self.name = "Super Admin"
        self.role = "admin"

@app.route('/test_render')
def test_render():
    from flask_login import login_user
    # Mock data
    pharmacies_json = '[]'
    sub_admins_json = '[]'
    hospitals_json = '[]'
    medicines_json = '[]'
    ambulances_json = '[]'
    emergencies_json = '[]'
    
    return render_template('admin_dashboard.html',
                           current_user=MockUser(),
                           pharmacies_json=pharmacies_json,
                           sub_admins_json=sub_admins_json,
                           hospitals_json=hospitals_json,
                           medicines_json=medicines_json,
                           ambulances_json=ambulances_json,
                           emergencies_json=emergencies_json,
                           pharmacies_count=0,
                           hospitals_count=0,
                           medicines_count=0,
                           ambulances_count=0,
                           csrf_token=lambda: "test-token")

if __name__ == "__main__":
    with app.test_request_context():
        try:
            rendered = test_render()
            print("SUCCESS: Template rendered correctly.")
            # Check for specific strings
            if 'adminName: "Super Admin"' in rendered:
                print("SUCCESS: adminName correctly escaped with tojson.")
            else:
                print("FAILURE: adminName not found or improperly rendered.")
                # Print a snippet around adminName
                idx = rendered.find('adminName:')
                print(f"Snippet: {rendered[idx:idx+50]}")
                
            if 'openMap(lat, lng)' in rendered:
                print("SUCCESS: openMap method exists.")
            if 'fas fa-location-dot' in rendered:
                print("SUCCESS: Map icon exists in SOS feed.")
        except Exception as e:
            print(f"FAILURE: {str(e)}")
            import traceback
            traceback.print_exc()
