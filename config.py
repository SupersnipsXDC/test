import json
import os
from dotenv import load_dotenv
import logging

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Umgebungsvariablen laden
load_dotenv()

# Standardkonfiguration
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "keywords": ["migration", "umvolkung", "asylpolitik", "grenzen", "invasion", "HorizonEU", "EU funding", "research funding"],
    "hashtags": ["#nomigration", "#grenzenzu", "#remigration", "#HorizonEU"],
    "target_accounts": ["example_user1", "example_user2"]
}

def load_config():
    """Lädt die Konfigurationsdatei oder erstellt eine Standardkonfiguration."""
    try:
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            logging.info("Standardkonfiguration erstellt.")
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Fehler beim Laden der Konfiguration: {e}")
        return DEFAULT_CONFIG

CONFIG = load_config()
KEYWORDS = CONFIG["keywords"]
DB_NAME = os.getenv("DB_NAME", "migration_narratives.db")

# Twitter API-Zugangsdaten
TWITTER_CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# Chromium Zugangsdaten
X_USERNAME = os.getenv("X_USERNAME")
X_PASSWORD = os.getenv("X_PASSWORD")

# SMTP-Konfiguration für E-Mail-Benachrichtigungen
SMTP_SERVER = os.getenv("SMTP_SERVER", "in-v3.mailjet.com")
SMTP_USERNAME = os.getenv("MAILJET_API_KEY")
SMTP_PASSWORD = os.getenv("MAILJET_SECRET_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

def validate_credentials():
    """Validiert alle Zugangsdaten."""
    if not all([TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
        logging.error("Twitter API-Zugangsdaten fehlen oder sind unvollständig.")
        raise ValueError("Twitter API-Zugangsdaten fehlen. Bitte überprüfe die .env-Datei.")
    if not all([X_USERNAME, X_PASSWORD]):
        logging.error("Chromium-Zugangsdaten fehlen oder sind unvollständig.")
        raise ValueError("Chromium-Zugangsdaten fehlen. Bitte überprüfe die .env-Datei.")
    if not all([SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL]):
        logging.error("SMTP-Konfiguration fehlt in .env.")
        raise ValueError("SMTP-Konfiguration fehlt. Bitte überprüfe die .env-Datei.")
    logging.info("Zugangsdaten erfolgreich validiert.")

# Initiale Validierung
validate_credentials()