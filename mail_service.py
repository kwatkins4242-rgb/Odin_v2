import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import os
import sys

# Path Setup
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from settings import get_settings
settings = get_settings()

class MailService:
    def __init__(self):
        # Default to Gmail based on .env hints, but these should be in settings/env
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.imap_server = "imap.gmail.com"
        self.username = os.getenv("EMAIL_USER", "kwatkins.4242@gmail.com")
        self.password = os.getenv("EMAIL_PASS", "Balvenie4242@") # From .env n8n clues

    def send_email(self, to_address, subject, body):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to_address
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            return {"success": True, "message": f"Email sent to {to_address}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_inbox(self, limit=5):
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.username, self.password)
            mail.select("inbox")

            status, messages = mail.search(None, "ALL")
            mail_ids = messages[0].split()
            
            results = []
            for i in mail_ids[-limit:]:
                res, msg = mail.fetch(i, "(RFC822)")
                for response in msg:
                    if isinstance(response, tuple):
                        msg = email.message_from_bytes(response[1])
                        results.append({
                            "id": i.decode(),
                            "from": msg.get("From"),
                            "subject": msg.get("Subject"),
                            "date": msg.get("Date")
                        })
            mail.close()
            mail.logout()
            return {"success": True, "emails": results}
        except Exception as e:
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Simple CLI test
    svc = MailService()
    print("ODIN Mail Service Initialized.")
    # print(svc.check_inbox(limit=1))
