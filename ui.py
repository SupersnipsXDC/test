# ui.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from scraper import TwitterAPIClient
from chromium_scraper import scrape_x_data as chromium_scrape
from twscrape_scraper import scrape_x_data as twscrape_scrape
from analyzer_refactored import NarrativeAnalyzer, load_latest_topic_model
from narrative_analyzer import NarrativeAnalyzer
from db import insert_tweet
from config import KEYWORDS
import pandas as pd
from dashboard import launch_dashboard
from generate_pdf_report import generate_pdf_report
import logging
import asyncio
import json
import os

# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class MigrationAnalyzerApp:
    def __init__(self, root, analyzer=None):
        self.root = root
        self.analyzer = NarrativeAnalyzer() if analyzer is None else analyzer
        self.root.title("Migration Narrative Analyzer")
        self.root.geometry("1000x700")
        self.root.configure(bg="#1E1E1E")
        self.monitoring_active = False
        self.df = None
        self.topic_model = None

        # Styling
        style = ttk.Style()
        style.configure("TButton", font=("Arial", 12, "bold"), padding=10)
        style.map("TButton", background=[("active", "#45a049")])
        style.configure("TLabel", font=("Arial", 12), background="#1E1E1E", foreground="white")
        style.configure("TCombobox", font=("Arial", 11))

        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Text display area
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(pady=10)
        self.result_text = tk.Text(text_frame, height=20, width=100, bg="#2D2D2D", fg="#00FF00",
                                  font=("Courier", 11), insertbackground="white")
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        self.result_text.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")

        # Keyword input
        ttk.Label(main_frame, text="🔍 Keywords (comma-separated):").pack(pady=5)
        self.keyword_entry = ttk.Entry(main_frame, width=70, font=("Arial", 11))
        self.keyword_entry.insert(0, ",".join(KEYWORDS))
        self.keyword_entry.pack()

        # Tweet type selection
        ttk.Label(main_frame, text="📊 Tweet Type:").pack(pady=5)
        self.tweet_type = ttk.Combobox(main_frame, values=["recent", "popular"], state="readonly", width=20)
        self.tweet_type.set("recent")
        self.tweet_type.pack()

        # Max tweets input
        ttk.Label(main_frame, text="📈 Max Tweets:").pack(pady=5)
        self.limit_entry = ttk.Entry(main_frame, width=20, font=("Arial", 11))
        self.limit_entry.insert(0, "100")
        self.limit_entry.pack()

        # Scraping method selection
        ttk.Label(main_frame, text="🔧 Scraping Method:").pack(pady=5)
        self.scraping_method = ttk.Combobox(main_frame, values=["API", "Chromium", "twscrape"], state="readonly", width=20)
        self.scraping_method.set("API")
        self.scraping_method.pack()

        # Label für letzte Aktualisierung
        self.last_update_label = ttk.Label(main_frame, text="Modell zuletzt aktualisiert am: N/A")
        self.last_update_label.pack(pady=5)
        self.update_last_update_label()  # Initiale Anzeige setzen

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)

        self.start_analysis_button = ttk.Button(button_frame, text="📥 Start Analysis",
                                                command=self.run_historical_analysis)
        self.start_analysis_button.grid(row=0, column=0, padx=5)

        self.start_monitoring_button = ttk.Button(button_frame, text="📡 Start Live Monitoring",
                                                  command=self.run_real_time_monitoring)
        self.start_monitoring_button.grid(row=0, column=1, padx=5)

        self.stop_monitoring_button = ttk.Button(button_frame, text="🛑 Stop Monitoring",
                                                 command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_monitoring_button.grid(row=0, column=2, padx=5)

        self.visualize_button = ttk.Button(button_frame, text="📊 Show Dashboard",
                                           command=self.run_visualization)
        self.visualize_button.grid(row=0, column=3, padx=5)

        self.report_button = ttk.Button(button_frame, text="📄 Generate Report",
                                        command=self.generate_report)
        self.report_button.grid(row=0, column=4, padx=5)

        self.retrain_button = ttk.Button(button_frame, text="🔄 Retrain Model",
                                         command=self.retrain_model)
        self.retrain_button.grid(row=0, column=5, padx=5)

        # Initial log message
        self.result_text.insert("end", "🚀 Application initialized. Ready for your input!\n")

    def log(self, message):
        """Log messages to the UI."""
        self.result_text.insert("end", f"{message}\n")
        self.result_text.see("end")
        self.root.update_idletasks()

    def retrain_model(self):
        """Führt manuelles Re-Training aus."""
        self.log("🔄 Initiere Modell-Retraining...")
        threading.Thread(target=self._run_retrain, daemon=True).start()

    def _run_retrain(self):
        """Führt das Re-Training im Hintergrund aus."""
        from update_models import update_topic_model
        update_topic_model()
        self.update_last_update_label()
        self.log("✅ Modell-Retraining abgeschlossen.")
        self.analyzer.topic_model = load_latest_topic_model()  # Neuestes Modell laden

    def update_last_update_label(self):
        """Aktualisiert das Label mit dem letzten Trainingsdatum."""
        meta_file = os.path.join("models", "model_meta.json")
        if os.path.exists(meta_file):
            with open(meta_file, "r") as f:
                meta_data = json.load(f)
            self.last_update_label.config(text=f"Modell zuletzt aktualisiert am: {meta_data['date']}")
        else:
            self.last_update_label.config(text="Modell zuletzt aktualisiert am: N/A")

    # Restliche Methoden bleiben unverändert...

    def run_historical_analysis(self):
        def thread_task():
            try:
                self.start_analysis_button.config(state=tk.DISABLED)
                self.log("📥 Starting historical analysis...")
                keywords = [kw.strip() for kw in self.keyword_entry.get().split(",") if kw.strip()] or KEYWORDS
                limit = int(self.limit_entry.get()) if self.limit_entry.get().isdigit() else 100
                tweet_type = self.tweet_type.get()
                method = self.scraping_method.get()

                # Select scraping method
                if method == "API":
                    data = TwitterAPIClient().scrape_x_data(keywords, limit=limit, tweet_type=tweet_type)
                elif method == "Chromium":
                    data = chromium_scrape(keywords, limit=limit, tweet_type=tweet_type, log_fn=self.log)
                elif method == "twscrape":
                    data = asyncio.run(twscrape_scrape(keywords, limit=limit, tweet_type=tweet_type))
                else:
                    self.log("❌ Invalid scraping method selected.")
                    return

                if not data:
                    self.log("⚠ No tweets found. Try broader keywords or check configuration.")
                    messagebox.showwarning("Warning", "No tweets found. Please check inputs.")
                    return

                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'], utc=True, errors='coerce')
                self.df, self.topic_model = self.analyzer.process_narratives(df)
                if self.topic_model is None:
                    self.log("⚠ Topic model creation failed. Check data or models.")
                    return
                unseen_topics = self.analyzer.detect_new_narratives(self.df, self.topic_model)
                if unseen_topics:
                    self.log(f"⚠ New narratives detected: {list(unseen_topics)}")
                for _, tweet in self.df.iterrows():
                    insert_tweet(tweet.to_dict())
                self.log("✅ Historical analysis completed.")
            except Exception as e:
                logging.error(f"Error in historical analysis: {e}")
                self.log(f"❌ Error: {e}")
                messagebox.showerror("Error", f"An error occurred: {e}")
            finally:
                self.start_analysis_button.config(state=tk.NORMAL)

        self.result_text.delete("1.0", "end")
        threading.Thread(target=thread_task, daemon=True).start()

    def run_real_time_monitoring(self):
        self.monitoring_active = True
        self.start_monitoring_button.config(state=tk.DISABLED)
        self.stop_monitoring_button.config(state=tk.NORMAL)
        self.log("📡 Live monitoring started...")

        def monitor():
            while self.monitoring_active:
                try:
                    keywords = [kw.strip() for kw in self.keyword_entry.get().split(",") if kw.strip()] or KEYWORDS
                    limit = 10
                    tweet_type = self.tweet_type.get()
                    method = self.scraping_method.get()

                    # Select scraping method
                    if method == "API":
                        data = TwitterAPIClient().scrape_x_data(keywords, limit=limit, tweet_type=tweet_type)
                    elif method == "Chromium":
                        data = chromium_scrape(keywords, limit=limit, tweet_type=tweet_type, log_fn=self.log)
                    elif method == "twscrape":
                        data = asyncio.run(twscrape_scrape(keywords, limit=limit, tweet_type=tweet_type))
                    else:
                        self.log("❌ Invalid scraping method selected.")
                        return

                    if data:
                        df = pd.DataFrame(data)
                        df['date'] = pd.to_datetime(df['date'], utc=True, errors='coerce')
                        self.df, self.topic_model = self.analyzer.process_new_data()
                        if self.topic_model:
                            unseen_topics = self.analyzer.detect_new_narratives(self.df, self.topic_model)
                            if unseen_topics:
                                self.log(f"⚠ New narratives detected: {list(unseen_topics)}")
                            for _, tweet in self.df.iterrows():
                                insert_tweet(tweet.to_dict())
                            self.log(f"✅ Processed {len(data)} new tweets.")
                except Exception as e:
                    self.log(f"❌ Monitoring error: {e}")
                    logging.error(f"Monitoring error: {e}")
                time.sleep(60)  # Configurable interval

        threading.Thread(target=monitor, daemon=True).start()

    def stop_monitoring(self):
        self.monitoring_active = False
        self.start_monitoring_button.config(state=tk.NORMAL)
        self.stop_monitoring_button.config(state=tk.DISABLED)
        self.log("🛑 Live monitoring stopped.")

    def run_visualization(self):
        self.log("📊 Starting dashboard...")
        threading.Thread(target=launch_dashboard, daemon=True).start()

    def generate_report(self):
        if self.df is None or self.topic_model is None:
            self.log("❌ No data or model available for the report.")
            messagebox.showwarning("Warning", "No data or model available. Please run an analysis first.")
            return
        self.log("📄 Generating report...")
        threading.Thread(target=generate_pdf_report, args=(self.df, self.topic_model), daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    analyzer = NarrativeAnalyzer()
    app = MigrationAnalyzerApp(root, analyzer)
    root.mainloop()