import os
import joblib
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from filelock import FileLock
import logging
import time

# Configure logging to track model operations
logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class TopicModeler:
    """
    A class to handle topic modeling using BERTopic, with support for multilingual data,
    incremental updates, and thread-safe model versioning for scalability.
    """

    def __init__(self, model_dir='models'):
        """
        Initialize the TopicModeler with a specified model directory.

        Args:
            model_dir (str): Directory where model versions are saved. Defaults to 'models'.
        """
        self.model_dir = model_dir
        self.versions_dir = os.path.join(model_dir, 'versions')
        self.latest_version_file = os.path.join(model_dir, 'latest_version.txt')
        self.lock_file = os.path.join(model_dir, 'model.lock')

        # Ensure directories exist
        os.makedirs(self.versions_dir, exist_ok=True)

        # Use a multilingual embedding model for sentence transformation
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

        # Load the latest model version
        self.topic_model = self._load_latest_model()

    def _get_latest_version(self):
        """
        Retrieve the latest model version from the tracking file.

        Returns:
            str: The version identifier of the latest model, or None if not found.
        """
        if os.path.exists(self.latest_version_file):
            with open(self.latest_version_file, 'r') as f:
                return f.read().strip()
        return None

    def _load_latest_model(self):
        """
        Load the latest model version.

        Returns:
            BERTopic: The loaded BERTopic model, or None if no model exists.
        """
        latest_version = self._get_latest_version()
        if latest_version:
            model_path = os.path.join(self.versions_dir, f'model_{latest_version}.pkl')
            try:
                model = joblib.load(model_path)
                logging.info(f"Loaded model version {latest_version} from {model_path}")
                return model
            except Exception as e:
                logging.error(f"Error loading model version {latest_version}: {e}")
        return None

    def _save_model(self, model, version):
        """
        Save the model with a specific version identifier.

        Args:
            model (BERTopic): The BERTopic model to save.
            version (str): The version identifier.
        """
        model_path = os.path.join(self.versions_dir, f'model_{version}.pkl')
        joblib.dump(model, model_path)
        logging.info(f"Saved model version {version} to {model_path}")

    def _update_latest_version(self, version):
        """
        Update the tracking file with the latest model version.

        Args:
            version (str): The version identifier to set as latest.
        """
        with open(self.latest_version_file, 'w') as f:
            f.write(version)
        logging.info(f"Updated latest model version to {version}")

    def assign_topics(self, texts):
        """
        Assign topics to a list of texts using the current topic model.
        If no model exists, initialize and fit a new one.

        Args:
            texts (list): List of text strings to assign topics to.

        Returns:
            list: Topic IDs assigned to each text.
        """
        if self.topic_model is None:
            # Initialize a new BERTopic model with multilingual support
            self.topic_model = BERTopic(
                embedding_model=self.embedding_model,
                language="multilingual",
                verbose=True
            )
            topics, _ = self.topic_model.fit_transform(texts)
            version = str(int(time.time()))
            with FileLock(self.lock_file):
                self._save_model(self.topic_model, version)
                self._update_latest_version(version)
        else:
            # Use the existing model to assign topics without retraining
            topics, _ = self.topic_model.transform(texts)
        return topics

    def update_model(self, texts):
        """
        Update the topic model incrementally with new texts.

        Args:
            texts (list): List of text strings to update the model with.
        """
        if self.topic_model is None:
            # If no model exists, assign topics (which initializes the model)
            self.assign_topics(texts)
        else:
            # Update the existing model with new data
            self.topic_model.partial_fit(texts)
            version = str(int(time.time()))
            with FileLock(self.lock_file):
                self._save_model(self.topic_model, version)
                self._update_latest_version(version)

    def get_topic(self, topic_id):
        """
        Retrieve information about a specific topic.

        Args:
            topic_id (int): The ID of the topic to retrieve.

        Returns:
            list: Topic representation (e.g., top words) if the model exists, None otherwise.
        """
        if self.topic_model is not None:
            return self.topic_model.get_topic(topic_id)
        return None