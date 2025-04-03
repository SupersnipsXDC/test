# twscrape_scraper.py
import os
from twscrape import API, gather
import logging
from dotenv import load_dotenv
import asyncio
import time

# Load environment variables from .env file
load_dotenv()

# Twitter credentials for twscrape
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")
TWITTER_EMAIL = os.getenv("TWITTER_EMAIL")

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Initialize the API pool once (reused across multiple scrapes)
api = API()

# Delay between requests (in seconds)
REQUEST_DELAY = 10  # Adjust this value based on observations

async def scrape_x_data(keywords, limit=100, tweet_type="latest"):
    """Scrape tweets using twscrape with error handling and rate limit management."""
    if not all([TWITTER_USERNAME, TWITTER_PASSWORD, TWITTER_EMAIL]):
        raise ValueError("Twitter credentials for twscrape are missing in .env file.")

    try:
        # Attempt to add the account; handle case where it already exists
        try:
            await api.pool.add_account(TWITTER_USERNAME, TWITTER_PASSWORD, TWITTER_EMAIL, TWITTER_PASSWORD)
            logging.info(f"Account {TWITTER_USERNAME} added successfully.")
        except Exception as e:
            if "already exists" in str(e).lower():
                logging.info(f"Account {TWITTER_USERNAME} already exists in the pool.")
            else:
                logging.error(f"Failed to add account {TWITTER_USERNAME}: {e}")
                raise

        # Log in to all accounts (refreshes sessions if needed)
        await api.pool.login_all()
        logging.info("Logged in to all accounts successfully.")

        # Construct query: keywords OR-ed, German language, no retweets
        query = " OR ".join(keywords) + " lang:de -is:retweet"
        logging.info(f"Scraping tweets with query: {query}, limit: {limit}")

        # Scrape tweets with a delay between requests
        tweets = []
        batch_size = 10  # Number of tweets per request
        for _ in range((limit + batch_size - 1) // batch_size):  # Ceiling division
            batch = await gather(api.search(query, limit=batch_size))
            tweets.extend(batch)
            if len(tweets) >= limit:
                break
            time.sleep(REQUEST_DELAY)  # Delay between requests

        # Process tweets into the expected dictionary format
        tweet_list = []
        for tweet in tweets[:limit]:
            tweet_data = {
                "tweet_id": str(tweet.id),
                "text": tweet.rawContent,
                "user": tweet.user.username,
                "followers": tweet.user.followersCount,
                "retweets": tweet.retweetCount,
                "likes": tweet.likeCount,
                "date": tweet.date.isoformat(),
                "keywords": ",".join([kw for kw in keywords if kw.lower() in tweet.rawContent.lower()])
            }
            tweet_list.append(tweet_data)

        logging.info(f"Scraped {len(tweet_list)} tweets successfully.")
        return tweet_list
    except Exception as e:
        logging.error(f"Error during twscrape scraping: {e}")
        return []