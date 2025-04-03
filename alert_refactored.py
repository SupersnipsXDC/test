import smtplib
from email.mime.text import MIMEText
import pandas as pd
import sqlite3
from config import DB_NAME

def check_new_narratives(df, previous_clusters):
    """Check for new clusters and trigger alerts."""
    current_clusters = set(df['topic'].unique())
    new_clusters = current_clusters - set(previous_clusters)
    if new_clusters:
        send_alert_email(f"New narratives detected in clusters: {new_clusters}")
    return current_clusters

def send_alert_email(message):
    """Send an email alert."""
    sender = "your_email@example.com"  # Replace with your email
    receiver = "alert_receiver@example.com"  # Replace with recipient email
    msg = MIMEText(message)
    msg['Subject'] = "Early Warning: New Narratives Detected"
    msg['From'] = sender
    msg['To'] = receiver
    with smtplib.SMTP('smtp.example.com') as server:  # Replace with your SMTP server
        server.login(sender, "password")  # Replace with your password
        server.sendmail(sender, receiver, msg.as_string())

# Integrate with detect_new_narratives in analyzer_refactored.py