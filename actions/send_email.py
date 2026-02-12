import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
DIRECTOR_EMAIL = os.getenv("DIRECTOR_EMAIL")


def send_email(subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = DIRECTOR_EMAIL
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print("Erreur envoi email :", e)
        return False
