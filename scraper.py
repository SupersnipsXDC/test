import tweepy
from config import TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class TwitterAPIClient:
    def __init__(self):
        self.client = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Twitter API v2."""
        try:
            self.client = tweepy.Client(
                consumer_key=TWITTER_CONSUMER_KEY,
                consumer_secret=TWITTER_CONSUMER_SECRET,
                access_token=TWITTER_ACCESS_TOKEN,
                access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
            )
            logging.info("Twitter API v2 authenticated successfully.")
        except Exception as e:
            logging.error(f"Failed to authenticate Twitter API: {e}")
            raise

    def scrape_x_data(self, keywords, limit=100, tweet_type="recent", retries=3):
        """Scrape tweets using Twitter API v2 with error handling."""
        query = " OR ".join(keywords) + " -is:retweet lang:de"
        logging.info(f"Starting tweet search with query: {query}, limit: {limit}, type: {tweet_type}")

        attempt = 0
        while attempt < retries:
            try:
                tweets = self.client.search_recent_tweets(
                    query=query,
                    max_results=min(limit, 100),  # API max is 100 per request
                    tweet_fields=["created_at", "public_metrics", "author_id"],
                    user_fields=["username", "public_metrics"],
                    expansions=["author_id"]
                )
                if not tweets.data:
                    logging.warning(f"No tweets found for query '{query}'. Attempt {attempt + 1}/{retries}.")
                    if attempt + 1 < retries:
                        time.sleep(5)
                    attempt += 1
                    continue

                tweet_list = []
                users = {user.id: user for user in tweets.includes.get("users", [])}
                for tweet in tweets.data:
                    user = users.get(tweet.author_id)
                    tweet_data = {
                        "tweet_id": str(tweet.id),
                        "text": tweet.text,
                        "user": user.username if user else "unknown",
                        "followers": user.public_metrics["followers_count"] if user else 0,
                        "retweets": tweet.public_metrics["retweet_count"],
                        "likes": tweet.public_metrics["like_count"],
                        "date": tweet.created_at.isoformat(),
                        "keywords": ",".join([kw for kw in keywords if kw.lower() in tweet.text.lower()])
                    }
                    tweet_list.append(tweet_data)

                logging.info(f"{len(tweet_list)} tweets successfully scraped.")
                return tweet_list[:limit]
            except tweepy.TweepyException as e:
                if "rate limit" in str(e).lower():
                    logging.error(f"Rate limit reached: {e}. Waiting 15 minutes...")
                    time.sleep(900)  # 15 minutes
                else:
                    logging.error(f"Twitter API error: {e}")
                attempt += 1
                time.sleep(5)
            except Exception as e:
                logging.error(f"Unexpected error during scraping: {e}")
                attempt += 1
                time.sleep(5)

        logging.error(f"All {retries} attempts failed. No tweets found.")
        return []

# Initialize the client
twitter_client = TwitterAPIClient()