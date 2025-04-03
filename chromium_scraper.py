import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Twitter (X) credentials from environment variables
X_USERNAME = os.getenv("X_USERNAME")
X_PASSWORD = os.getenv("X_PASSWORD")

def init_driver(headless=True):
    """Initialize the Selenium WebDriver with options to avoid bot detection."""
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    # Get Chromedriver path from environment variable
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
    if not chromedriver_path or not os.path.exists(chromedriver_path):
        raise ValueError(
            "CHROMEDRIVER_PATH not set correctly in .env file or Chromedriver not found at the specified path."
        )

    # Initialize the Chromedriver service
    service = Service(executable_path=chromedriver_path)
    try:
        driver = webdriver.Chrome(service=service, options=options)
        logging.info("Chromium driver initialized successfully.")
        return driver
    except Exception as e:
        logging.error(f"Error initializing Chromium driver: {e}")
        raise

def login_to_x(driver, log_fn=None):
    """Log in to Twitter (X) using credentials from environment variables."""
    if not X_USERNAME or not X_PASSWORD:
        raise ValueError("X_USERNAME and X_PASSWORD must be set in the .env file.")

    driver.get("https://x.com/login")
    try:
        # Wait for username field and enter credentials
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "text")))
        username_field = driver.find_element(By.NAME, "text")
        username_field.send_keys(X_USERNAME)
        username_field.send_keys(Keys.RETURN)
        if log_fn:
            log_fn("Username entered.")

        # Wait for password field and enter password
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password")))
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(X_PASSWORD)
        password_field.send_keys(Keys.RETURN)
        if log_fn:
            log_fn("Password entered.")

        # Wait for successful login
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-testid='tweet']"))
        )
        if log_fn:
            log_fn("Successfully logged in to X.")
    except Exception as e:
        logging.error(f"Login failed: {e}")
        if log_fn:
            log_fn(f"Login failed: {e}")
        raise

def scrape_x_data(keywords, limit=10, tweet_type="latest", log_fn=None, headless=True):
    """Scrape tweets from Twitter (X) after logging in."""
    driver = init_driver(headless=headless)
    try:
        login_to_x(driver, log_fn)
        query = " OR ".join(keywords)
        search_url = (
            f"https://x.com/search?q={query}%20lang%3Ade%20-is%3Aretweet&src=typed_query&f="
            f"{'live' if tweet_type == 'latest' else 'top'}"
        )
        driver.get(search_url)
        if log_fn:
            log_fn(f"Navigating to search URL: {search_url}")

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-testid='tweet']"))
        )

        tweets = []
        scroll_attempts = 0
        max_scrolls = 10
        last_height = driver.execute_script("return document.body.scrollHeight")

        while len(tweets) < limit and scroll_attempts < max_scrolls:
            tweet_elements = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
            if not tweet_elements:
                logging.info("No tweets found on page.")
                break

            for tweet in tweet_elements:
                try:
                    if not tweet.is_displayed():
                        continue
                    text = tweet.find_element(By.CSS_SELECTOR, "div[lang]").text
                    user = tweet.find_element(By.CSS_SELECTOR, "a[role='link']").text
                    timestamp = (
                        tweet.find_element(By.CSS_SELECTOR, "time").get_attribute("datetime")
                        if tweet.find_elements(By.CSS_SELECTOR, "time")
                        else datetime.now().isoformat()
                    )
                    tweet_id = tweet.find_element(
                        By.CSS_SELECTOR, "a[role='link'][href*='/status/']"
                    ).get_attribute("href").split("/")[-1]
                    keywords_found = ",".join([kw for kw in keywords if kw.lower() in text.lower()])

                    tweets.append({
                        "tweet_id": tweet_id,
                        "text": text,
                        "user": user,
                        "followers": 0,  # Not available via Selenium
                        "retweets": 0,
                        "likes": 0,
                        "date": timestamp,
                        "keywords": keywords_found
                    })
                except Exception:
                    continue

                if len(tweets) >= limit:
                    break

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
            last_height = new_height

        logging.info(f"{len(tweets)} tweets successfully scraped with Chromium.")
        if log_fn:
            log_fn(f"{len(tweets)} tweets scraped.")
        return tweets[:limit]
    except Exception as e:
        logging.error(f"Error during Chromium scraping: {e}")
        if log_fn:
            log_fn(f"Error during Chromium scraping: {e}")
        return []
    finally:
        driver.quit()