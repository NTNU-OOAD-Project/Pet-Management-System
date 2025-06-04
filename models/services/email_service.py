import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.email_user = os.getenv("EMAIL_USER")
        self.email_pass = os.getenv("EMAIL_PASS")
        self.display_name = os.getenv("EMAIL_DISPLAY_NAME")
        self.smtp_server = os.getenv("EMAIL_SMTP", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("EMAIL_PORT", 587))

    def send_email(self, to_email: str, subject: str, content: str):
        msg = MIMEMultipart()
        msg["From"] = f"{self.display_name} <{self.email_user}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(content, "plain", "utf-8"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_pass)
                server.send_message(msg)
            return True
        except Exception as e:
            print("Email 發送錯誤:", e)
            return False