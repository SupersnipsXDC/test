import os
from datetime import datetime
import joblib
import pandas as pd
import re
from transformers import pipeline, BertTokenizer
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
import sqlite3
from config import DB_NAME
import logging
import nltk
from nltk.corpus import stopwords

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Download and load German stop words
nltk.download('stopwords', quiet=True)  # Download stopwords quietly to avoid cluttering logs
german_stop_words = stopwords.words('german')

# Function to load the latest topic model
def load_latest_topic_model():
    """Loads the latest BERTopic model from the models/ directory."""
    model_dir = "models"
    if not os.path.exists(model_dir):
        logging.warning("Model directory does not exist.")
        return None
    
    # Find all BERTopic model files
    model_files = [f for f in os.listdir(model_dir) if f.startswith("BERTopic_") and f.endswith(".pkl")]
    if not model_files:
        logging.warning("No BERTopic models found.")
        return None
    
    # Select the latest model based on the date in the filename
    latest_model = max(model_files, key=lambda x: datetime.strptime(x.split("_")[1].split(".")[0], "%Y-%m-%d"))
    model_path = os.path.join(model_dir, latest_model)
    
    try:
        topic_model = joblib.load(model_path)
        logging.info(f"Latest model loaded: {model_path}")
        return topic_model
    except Exception as e:
        logging.error(f"Error loading topic model: {e}")
        return None

# Define toxic keywords
TOXIC_KEYWORDS = ["hass", "gewalt", "rassist", "feind"]

class NarrativeAnalyzer:
    def __init__(self):
        self.sentiment_analyzer = None
        self.classifier = None
        self.topic_model = load_latest_topic_model()  # Load the latest model
        self.tokenizer = BertTokenizer.from_pretrained("bert-base-multilingual-cased")
        self._load_models()

    def _load_models(self):
        """Loads AI models for sentiment analysis, classification, and topic modeling."""
        try:
            logging.info("Loading AI models...")
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=0  # Use GPU if available
            )
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0
            )
            # Topic model is loaded via load_latest_topic_model()
            if self.topic_model is None:
                logging.warning("No topic model available. Clustering will be skipped.")
            logging.info("Models successfully loaded.")
        except Exception as e:
            logging.error(f"Error loading models: {e}")
            raise

    def truncate_text(self, text, max_tokens=510):
        """Truncates text to the maximum token length using BERT tokenizer."""
        tokens = self.tokenizer.tokenize(text)
        if len(tokens) > max_tokens:
            tokens = tokens[:max_tokens]
        return self.tokenizer.convert_tokens_to_string(tokens)

    def cluster_narratives(self, df: pd.DataFrame):
        """Clusters narratives using BERTopic."""
        if len(df) < 5:
            df['topic'] = -1
            return df, None
        try:
            logging.info("Starting narrative clustering...")
            texts = df['text'].tolist()
            if self.topic_model is None:
                # Use CountVectorizer with German stop words
                vectorizer = CountVectorizer(stop_words=german_stop_words)
                self.topic_model = BERTopic(
                    vectorizer_model=vectorizer,
                    language="multilingual",
                    verbose=True
                )
            topics, _ = self.topic_model.fit_transform(texts)
            df['topic'] = topics
            logging.info("Clustering completed.")
            return df, self.topic_model
        except Exception as e:
            logging.error(f"Error during clustering: {e}")
            df['topic'] = -1
            return df, None

    def classify_narratives(self, df: pd.DataFrame):
        """Classify narratives into positive, negative, or neutral."""
        if self.classifier is None:
            logging.error("Classifier not loaded.")
            df['narrative_type'] = "unknown"
            return df
        try:
            logging.info("Starting narrative classification...")
            texts = df['text'].tolist()
            labels = ["positive", "negative", "neutral"]
            results = self.classifier(texts, candidate_labels=labels, batch_size=8)
            df['narrative_type'] = [result['labels'][0] for result in results]
            logging.info("Classification completed.")
            return df
        except Exception as e:
            logging.error(f"Error during classification: {e}")
            df['narrative_type'] = "unknown"
            return df

    def calculate_toxicity(self, text: str) -> float:
        """Calculate toxicity score based on toxic keywords."""
        text_lower = text.lower()
        toxic_count = sum(1 for word in TOXIC_KEYWORDS if re.search(r'\b' + re.escape(word) + r'\b', text_lower))
        return min(toxic_count / len(text.split()) if text.split() else 0.0, 1.0)

    def calculate_danger_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate danger score based on toxicity and escalation."""
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.sort_values('date')
        df['toxicity'] = df['text'].apply(self.calculate_toxicity)
        df['daily_toxicity'] = df.groupby(df['date'].dt.date)['toxicity'].transform('mean')
        df['escalation'] = df['daily_toxicity'].diff().fillna(0)
        df['danger_score'] = df['toxicity'] + df['escalation'].clip(lower=0)
        return df

    def process_narratives(self, df: pd.DataFrame):
        """Process narratives through sentiment, clustering, classification, and danger scoring."""
        try:
            # Truncate texts to avoid token length issues
            df['text'] = df['text'].apply(lambda x: self.truncate_text(x, max_tokens=510))

            # Batch sentiment analysis
            logging.info("Starting sentiment analysis...")
            texts = df['text'].tolist()
            sentiments = self.sentiment_analyzer(texts, batch_size=8)
            df['sentiment'] = [
                sent['score'] if sent['label'] == 'POSITIVE' else -sent['score']
                for sent in sentiments
            ]

            # Clustering
            df, local_topic_model = self.cluster_narratives(df)

            # Classification
            df = self.classify_narratives(df)

            # Danger score calculation
            df = self.calculate_danger_score(df)

            return df, local_topic_model
        except Exception as e:
            logging.error(f"Error in process_narratives: {e}")
            return df, None

    def detect_new_narratives(self, df: pd.DataFrame, topic_model):
        """Detect new narratives by comparing with historical data."""
        if topic_model is None:
            return set()
        try:
            with sqlite3.connect(DB_NAME) as conn:
                old_topics_df = pd.read_sql_query("SELECT DISTINCT topic FROM narratives", conn)
            old_topics = set(old_topics_df['topic'].dropna().astype(int).tolist())
            new_topics = set(df['topic'].dropna().astype(int).tolist())
            unseen_topics = new_topics - old_topics
            if unseen_topics:
                from email_alert import send_alert_email
                send_alert_email(f"New narratives detected in clusters: {unseen_topics}")
            return unseen_topics
        except Exception as e:
            logging.error(f"Error detecting new narratives: {e}")
            return set()

# Initialize the analyzer
analyzer = NarrativeAnalyzer()