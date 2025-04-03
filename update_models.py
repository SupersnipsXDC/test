from datetime import datetime, timedelta
import pandas as pd
import sqlite3
from ml_components import EmbeddingGenerator, TopicModeler
from config import DB_NAME
import logging

logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def update_topic_model():
    """Update the topic model with data from the last 7 days."""
    embedding_generator = EmbeddingGenerator()
    topic_modeler = TopicModeler(embedding_generator)

    with sqlite3.connect(DB_NAME) as conn:
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        df = pd.read_sql_query(f"SELECT text FROM narratives WHERE date >= '{seven_days_ago}'", conn)

    if df.empty:
        logging.info("No new data from the last 7 days. Skipping update.")
        return

    texts = df['text'].tolist()
    topic_modeler.partial_fit(texts)
    logging.info("Weekly topic model update completed.")

if __name__ == "__main__":
    update_topic_model()