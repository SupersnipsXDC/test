import sqlite3
import logging
from datetime import datetime
from ml_components import ToxicityDetector, SentimentAnalyzer
from topic_modeler import TopicModeler
from lexicon import NarrativeLexicon
from utils import send_alert_email

DB_NAME = "narrative_db.sqlite"

class NarrativeAnalyzer:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.toxicity_detector = ToxicityDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.topic_modeler = TopicModeler()
        self.lexicon = NarrativeLexicon(db_name)
        logging.info("NarrativeAnalyzer initialized.")

    def process_new_data(self, df):
        texts = df['text'].tolist()
        languages = df['language'].tolist()
        df['toxicity_score'] = self.toxicity_detector.detect_toxicity(texts)
        df['sentiment'] = self.sentiment_analyzer.analyze_sentiment(texts, languages)
        topics = self.topic_modeler.fit_transform(df['text'])
        df['topic_id'] = topics
        df = self.calculate_risk_score(df)
        self.detect_new_narratives(topics, df)
        self.save_to_db(df)
        return df

    def calculate_risk_score(self, df):
        freq = df['text'].value_counts(normalize=True)
        df['frequency_factor'] = df['text'].map(freq)
        cluster_toxicity = df.groupby('topic_id')['toxicity_score'].mean()
        df['cluster_toxicity'] = df['topic_id'].map(cluster_toxicity)
        df['risk_score'] = (df['toxicity_score'] * (1 - df['sentiment']) * 
                           df['frequency_factor'] * df['cluster_toxicity'])
        return df

    def detect_new_narratives(self, topics, df):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("SELECT topic_id FROM known_topics")
            known_topics = set(row[0] for row in c.fetchall())
            current_topics = set(topics)
            new_topics = current_topics - known_topics
            if new_topics and self.topic_modeler.topic_model:
                for topic in new_topics:
                    topic_info = self.topic_modeler.topic_model.get_topic(topic)
                    description = ", ".join([word for word, _ in topic_info[:5]]) if topic_info else "Unknown"
                    c.execute(
                        "INSERT INTO known_topics (topic_id, description, first_seen) VALUES (?, ?, ?)",
                        (topic, description, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    )
                    self.lexicon.update_lexicon(topic, description)
                    cluster_df = df[df['topic_id'] == topic]
                    max_risk = cluster_df['risk_score'].max()
                    if max_risk > 0.5:
                        send_alert_email(f"High-risk new narrative detected in cluster {topic}", 
                                        cluster_details=description)
                conn.commit()
                if new_topics:
                    send_alert_email(f"New narratives detected in clusters: {new_topics}", 
                                    cluster_details=str(new_topics))
                logging.info(f"New topics detected: {new_topics}")

    def save_to_db(self, df):
        with sqlite3.connect(self.db_name) as conn:
            df.to_sql('narratives', conn, if_exists='append', index=False)