import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urljoin
import re
from pathlib import Path
import json

class BaseScraper:
    def __init__(self, base_url, user_agent='NewsScraperBot/1.0'):
        # Initialize basic attributes first
        self.base_url = base_url
        self.logger = logging.getLogger(self.__class__.__name__)
        self.user_agent = user_agent
        self.headers = {
            'User-Agent': self.user_agent
        }
        
        # Initialize cache directory
        self.cache_dir = Path('cache')
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize timestamps and delays
        self.last_request_time = 0
        self.crawl_delay = 5  # Default delay
        
        # Initialize robot parser after cache directory is set up
        self.robot_parser = self._setup_robot_parser()
        
        # Update crawl delay from robots.txt
        self.crawl_delay = self._get_crawl_delay()

    def _setup_robot_parser(self):
        """Set up and cache robot parser for the base URL"""
        rp = RobotFileParser()
        domain = urlparse(self.base_url).netloc
        cache_file = self.cache_dir / f'robots_{domain}.json'
        
        try:
            # Try to load cached robots.txt data
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    if time.time() - cached_data['timestamp'] < 86400:  # 24 hour cache
                        rp.parse(cached_data['rules'])
                        self.logger.info(f"Loaded cached robots.txt for {domain}")
                        return rp

            # Fetch and parse robots.txt
            robot_url = f"{urlparse(self.base_url).scheme}://{domain}/robots.txt"
            response = requests.get(robot_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Cache the robots.txt content
            cache_data = {
                'timestamp': time.time(),
                'rules': response.text.split('\n')
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)

            rp.parse(response.text.split('\n'))
            self.logger.info(f"Successfully fetched and parsed robots.txt for {domain}")
            
        except Exception as e:
            self.logger.error(f"Error parsing robots.txt: {e}")
            # Use conservative defaults if robots.txt is unavailable
            rp.crawl_delay = 10
            
        return rp

    def _get_crawl_delay(self):
        """Get crawl delay from robots.txt or use conservative default"""
        try:
            delay = self.robot_parser.crawl_delay('*')
            return delay if delay is not None else 5  # 5 seconds default if not specified
        except Exception:
            return 5  # Conservative default

    def _respect_rate_limits(self):
        """Ensure we respect crawl delay between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.crawl_delay:
            sleep_time = self.crawl_delay - elapsed
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        # Add small random delay for politeness
        time.sleep(random.uniform(0.5, 1.5))
        self.last_request_time = time.time()

    def can_fetch(self, url):
        """Check if URL can be fetched according to robots.txt"""
        try:
            allowed = self.robot_parser.can_fetch(self.user_agent, url)
            if not allowed:
                self.logger.warning(f"robots.txt disallows fetching: {url}")
            return allowed
        except Exception as e:
            self.logger.warning(f"Robot parser check failed: {e}")
            return False  # Conservative approach: if check fails, don't fetch

    def get_page_content(self, url):
        """Fetch page content with proper rate limiting and robots.txt compliance"""
        if not self.can_fetch(url):
            self.logger.warning(f"Skipping {url} as per robots.txt")
            return None

        try:
            # Respect rate limits
            self._respect_rate_limits()
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Log successful fetch
            self.logger.debug(f"Successfully fetched {url}")
            
            return BeautifulSoup(response.content, 'lxml')
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def extract_government_news(self, soup):
        """Abstract method to be implemented by specific scrapers"""
        raise NotImplementedError("Subclasses must implement this method")

    def process_news_item(self, news_item):
        """Abstract method to be implemented by specific scrapers"""
        raise NotImplementedError("Subclasses must implement this method")