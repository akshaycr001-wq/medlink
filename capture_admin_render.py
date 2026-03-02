from app import app, db, User, Pharmacy, Hospital, Medicine, Ambulance, SOS
from flask import url_for
import json

with app.test_request_context():
    with app.test_client() as client:
        # We need to be logged in. Let's find an admin.
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            print("No admin user found")
            exit(1)
            
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True
            
        response = client.get('/admin')
        
        with open('rendered_admin_dashboard.html', 'w', encoding='utf-8') as f:
            f.write(response.get_data(as_text=True))
        
        print("Rendered HTML saved to rendered_admin_dashboard.html")
