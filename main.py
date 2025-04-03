import tkinter as tk
from analyzer_refactored import NarrativeAnalyzer
from ui import MigrationAnalyzerApp
from db import init_db
from apscheduler.schedulers.background import BackgroundScheduler
from update_models import update_topic_model
import logging

logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def start_scheduler():
    """Startet den Scheduler für automatisches Re-Training alle 3 Tage."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_topic_model, 'interval', days=3)
    scheduler.start()
    logging.info("Scheduler für Modell-Updates gestartet.")

def main():
    try:
        logging.info("Starte Anwendung...")
        init_db()
        start_scheduler()  # Scheduler starten
        analyzer = NarrativeAnalyzer()
        root = tk.Tk()
        app = MigrationAnalyzerApp(root, analyzer)
        root.mainloop()
    except Exception as e:
        logging.error(f"Fehler im Hauptprogramm: {e}")
        print(f"Ein Fehler ist aufgetreten: {e}")

if __name__ == "__main__":
    main()