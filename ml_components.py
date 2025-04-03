import logging
from transformers import pipeline

class ToxicityDetector:
    """Detect toxicity using a pre-trained multilingual model."""
    def __init__(self, model_name='unitary/multilingual-toxic-xlm-roberta'):
        self.model = pipeline("text-classification", model=model_name, device=0)  # Use GPU if available
        logging.info(f"Toxicity model {model_name} loaded.")

    def detect_toxicity(self, texts):
        """Detect toxicity in a list of texts."""
        results = self.model(texts)
        # Map model output (e.g., 'toxic'/'non-toxic') to a score between 0 and 1
        return [result['score'] if result['label'] == 'toxic' else 1 - result['score'] for result in results]

class SentimentAnalyzer:
    """Analyze sentiment using language-specific or multilingual models."""
    def __init__(self):
        # Multilingual fallback model
        self.multilingual_model = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment", device=0)
        # Language-specific models
        self.language_models = {
            'en': pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", device=0),
            # Add more language-specific models as needed
        }
        logging.info("Sentiment models loaded.")

    def analyze_sentiment(self, texts, languages):
        """Analyze sentiment for texts based on their languages."""
        sentiments = []
        for text, lang in zip(texts, languages):
            model = self.language_models.get(lang, self.multilingual_model)
            result = model(text)[0]
            if 'label' in result:
                if result['label'] == 'POSITIVE':
                    sentiments.append(result['score'])
                elif result['label'] == 'NEGATIVE':
                    sentiments.append(-result['score'])
                else:
                    sentiments.append(0.0)
            else:
                # For multilingual model with star ratings
                star_to_score = {'1 star': -1.0, '2 stars': -0.5, '3 stars': 0.0, '4 stars': 0.5, '5 stars': 1.0}
                sentiments.append(star_to_score.get(result['label'], 0.0))
        return sentiments