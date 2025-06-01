# services/reminder_service.py
import os
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv()

class ReminderService:
    @staticmethod
    def send_email(to_email: str, subject: str, content: str):
        sender_email = os.getenv("EMAIL_USER")
        sender_name = os.getenv("EMAIL_NAME", "Pet 管理系統")
        app_password = os.getenv("EMAIL_PASSWORD")

        msg = MIMEText(content, 'plain', 'utf-8')
        msg['From'] = formataddr((sender_name, sender_email))
        msg['To'] = to_email
        msg['Subject'] = subject

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, app_password)
                server.sendmail(sender_email, [to_email], msg.as_string())
            print("Email 發送成功")
        except Exception as e:
            print("Email 發送失敗：", e)