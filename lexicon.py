import sqlite3
from config import DB_NAME  # Assuming a config file exists

class NarrativeLexicon:
    """Manage the narrative lexicon stored in the database."""
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name

    def update_lexicon(self, topic_id, description):
        """Update the lexicon with new or updated cluster descriptions."""
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO known_topics (topic_id, description) VALUES (?, ?)", 
                      (topic_id, description))
            conn.commit()

    def get_lexicon(self):
        """Retrieve the current lexicon."""
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("SELECT topic_id, description FROM known_topics")
            return {row[0]: row[1] for row in c.fetchall()}