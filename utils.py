# utils.py
import smtplib
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL
import logging

# Configure logging (consistent with your project)
logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def send_alert_email(message, cluster_details=None):
    """
    Send an email alert with an optional cluster details attachment.

    Args:
        message (str): The body of the email.
        cluster_details (str, optional): Additional details to include.
    """
    if not all([SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL]):
        logging.error("SMTP configuration is missing in config.py or .env.")
        return

    try:
        # Construct the email body
        body = f"{message}\nDetails: {cluster_details}" if cluster_details else message
        msg = MIMEText(body)
        msg['Subject'] = "Early Warning: New Narratives Detected"
        msg['From'] = SENDER_EMAIL
        msg['To'] = SENDER_EMAIL

        # Send the email via SMTP
        with smtplib.SMTP(SMTP_SERVER, 587) as server:
            server.starttls()  # Enable TLS
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, SENDER_EMAIL, msg.as_string())
        logging.info(f"Email sent successfully: {message}")
    except Exception as e:
        logging.error(f"Error sending email: {e}")