import sqlite3
import logging
from config import DB_NAME

logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS narratives 
                     (tweet_id TEXT PRIMARY KEY, text TEXT, language TEXT, date TEXT)''')
        c.execute("PRAGMA table_info(narratives)")
        columns = [col[1] for col in c.fetchall()]
        for col, col_type in [('topic_id', 'INTEGER'), ('risk_score', 'REAL'), ('toxicity_score', 'REAL'), ('sentiment', 'REAL')]:
            if col not in columns:
                c.execute(f"ALTER TABLE narratives ADD COLUMN {col} {col_type}")
        c.execute('''CREATE TABLE IF NOT EXISTS known_topics 
                     (topic_id INTEGER PRIMARY KEY, description TEXT, first_seen TEXT)''')
        conn.commit()
        logging.info("Database initialized successfully.")