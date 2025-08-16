import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")


class MailService:
    @staticmethod
    def send_email(to_email: str, subject: str, body: str):
        try:
            msg = MIMEMultipart()
            msg["From"] = EMAIL
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(EMAIL, PASSWORD)
                server.send_message(msg)

            return {"status": "success", "message": f"Email sent to {to_email}"}

        except Exception as e:
            return {"status": "error", "message": str(e)}
