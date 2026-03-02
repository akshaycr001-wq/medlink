from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    admins = User.query.filter(User.role.in_(['admin', 'sub_admin'])).all()
    for admin in admins:
        admin.password = generate_password_hash('admin123', method='scrypt')
        admin.email_verified = True
    db.session.commit()
    print("All admin/sub-admin passwords reset to: admin123")
