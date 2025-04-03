import smtplib
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL
import logging

logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def send_alert_email(message, cluster_details=None):
    if not all([SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL]):
        logging.error("SMTP-Konfiguration fehlt in .env.")
        return

    try:
        msg = MIMEText(f"{message}\nDetails: {cluster_details}" if cluster_details else message)
        msg['Subject'] = "Frühwarnung: Neue Narrative erkannt"
        msg['From'] = SENDER_EMAIL
        msg['To'] = SENDER_EMAIL
        with smtplib.SMTP(SMTP_SERVER, 587) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, SENDER_EMAIL, msg.as_string())
        logging.info(f"E-Mail erfolgreich gesendet: {message}")
    except Exception as e:
        logging.error(f"Fehler beim Senden der E-Mail: {e}")