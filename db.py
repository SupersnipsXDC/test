import sqlite3
from typing import Dict
import logging
from config import DB_NAME

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def init_db():
    """
    Initializes the database with required tables and ensures the 'danger_score' column exists.
    """
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            # Create the table if it doesn't exist (initial schema without danger_score)
            c.execute('''CREATE TABLE IF NOT EXISTS narratives 
                         (tweet_id TEXT PRIMARY KEY, text TEXT, user TEXT, date TEXT, sentiment REAL, 
                          keywords TEXT, topic INTEGER, narrative_type TEXT, 
                          followers INTEGER, retweets INTEGER, likes INTEGER)''')
            # Check if 'danger_score' column exists
            c.execute("PRAGMA table_info(narratives)")
            columns = [col[1] for col in c.fetchall()]
            if 'danger_score' not in columns:
                c.execute("ALTER TABLE narratives ADD COLUMN danger_score REAL DEFAULT 0.0")
                logging.info("Added 'danger_score' column to narratives table.")
            conn.commit()
            logging.info("Datenbank erfolgreich initialisiert.")
    except Exception as e:
        logging.error(f"Fehler beim Initialisieren der Datenbank: {e}")
        raise

def insert_tweet(tweet: Dict):
    """
    Inserts a tweet into the database.
    
    Args:
        tweet (Dict): Dictionary containing tweet data.
    """
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""INSERT OR IGNORE INTO narratives 
                         (tweet_id, text, user, date, sentiment, keywords, topic, narrative_type, 
                          followers, retweets, likes, danger_score)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                tweet["tweet_id"], tweet["text"], tweet["user"], str(tweet["date"]),
                tweet.get("sentiment", 0.0), tweet["keywords"], tweet.get("topic", -1),
                tweet.get("narrative_type", ""), tweet["followers"], tweet["retweets"],
                tweet["likes"], tweet.get("danger_score", 0.0)))
            conn.commit()
            logging.info(f"Tweet {tweet['tweet_id']} erfolgreich eingefügt.")
    except Exception as e:
        logging.error(f"Fehler beim Einfügen des Tweets: {e}")

# Optional: Call init_db() at application startup if not already done elsewhere
if __name__ == "__main__":
    init_db()