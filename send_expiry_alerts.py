import sys
import os
from datetime import datetime, timedelta

# Ensure we're running in the correct directory context
sys.path.append(r"c:\Users\eldho\Downloads\Templatefolder")

from app import app, mail, MAIL_DEBUG_MODE
from models import db, Medicine, Pharmacy, User
from flask_mail import Message

def send_expiry_alerts():
    """
    Finds all medicines expiring within the next 7 days and sends 
    a single summary email to each respective pharmacy.
    """
    with app.app_context():
        print("Starting MedLink Expiry Alert Job...")
        
        today = datetime.now().date()
        warning_date = today + timedelta(days=7)
        
        # Query medicines expiring between today and warning_date
        expiring_meds = Medicine.query.filter(
            Medicine.expiry >= today,
            Medicine.expiry <= warning_date
        ).all()
        
        # Group expiring medicines by pharmacy
        pharmacy_alerts = {}
        for med in expiring_meds:
            pharma = med.pharmacy
            if pharma not in pharmacy_alerts:
                pharmacy_alerts[pharma] = []
            pharmacy_alerts[pharma].append(med)
            
        if not pharmacy_alerts:
            print("No medicines are expiring within the next 7 days. Job complete.")
            return

        print(f"Found {len(expiring_meds)} expiring medicines across {len(pharmacy_alerts)} pharmacies.")
        
        emails_sent = 0
        emails_failed = 0
        
        for pharma, meds in pharmacy_alerts.items():
            owner = pharma.owner
            if not owner or not owner.email:
                print(f"Skipping {pharma.shop_name} - No valid owner email found.")
                continue
                
            email = owner.email
            med_list_html = ""
            for m in meds:
                days_left = (m.expiry - today).days
                color = "#dc2626" if days_left <= 3 else "#ca8a04" # Red if <= 3 days, Yellow if 4-7
                med_list_html += f"""
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 0; color: #1e293b; font-weight: 600;">{m.name}</td>
                    <td style="padding: 10px 0; color: #64748b;">Qty: {m.qty}</td>
                    <td style="padding: 10px 0; color: {color}; font-weight: bold;">Expires in {days_left} days ({m.expiry.strftime('%b %d, %Y')})</td>
                </tr>
                """
                
            html_body = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
                <h2 style="color: #0f172a; border-bottom: 2px solid #0d9488; padding-bottom: 10px;">MedLink Expiry Alert</h2>
                <p style="color: #475569; font-size: 16px;">Hello <strong>{pharma.shop_name}</strong>,</p>
                <p style="color: #475569; font-size: 16px;">This is an automated alert from MedLink. You have <strong>{len(meds)} medicine(s)</strong> expiring within the next 7 days.</p>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    {med_list_html}
                </table>
                
                <p style="color: #64748b; font-size: 14px; margin-top: 30px; text-align: center;">
                    Please log into your MedLink Pharmacy Dashboard to update your inventory.<br>
                    <a href="http://127.0.0.1:5000/login" style="color: #0d9488; text-decoration: none; font-weight: bold;">Go to Dashboard</a>
                </p>
            </div>
            """
            
            if MAIL_DEBUG_MODE or not app.config.get('MAIL_USERNAME') or app.config.get('MAIL_USERNAME') == 'your_gmail@gmail.com':
                print(f"\n[DEBUG EMAIL] To: {email} | Shop: {pharma.shop_name}")
                print(f"Subject: Urgent: {len(meds)} Medicines Expiring Soon")
                print("--- HTML Body ---")
                print(html_body)
                print("-----------------\n")
                emails_sent += 1
            else:
                try:
                    msg = Message(
                        subject=f"Urgent: {len(meds)} Medicines Expiring Soon",
                        recipients=[email],
                        html=html_body
                    )
                    mail.send(msg)
                    emails_sent += 1
                    print(f"Alert sent to {email} ({pharma.shop_name})")
                except Exception as e:
                    emails_failed += 1
                    print(f"Failed to send to {email}: {e}")
                    
        print(f"Job finished. Sent: {emails_sent}, Failed: {emails_failed}")

if __name__ == "__main__":
    send_expiry_alerts()
