from .base_scraper import BaseScraper
from urllib.parse import urlparse
import requests
import logging
import xml.etree.ElementTree as ET

class ZeeNewsScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://zeenews.india.com/")
        self.sitemap_url = "https://zeenews.india.com/sitemap.xml"
        self.logger = logging.getLogger(self.__class__.__name__)

    def fetch_sitemap_urls(self, limit=100):
        """Fetch URLs from the sitemap."""
        try:
            self.logger.debug(f"Fetching sitemap from {self.sitemap_url}")
            response = requests.get(self.sitemap_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            urls = [
                url.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
                for url in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url")
            ]
            self.logger.info(f"Fetched {len(urls)} URLs from the sitemap.")
            return urls[:limit]  # Return only the first `limit` URLs
        except Exception as e:
            self.logger.error(f"Error fetching sitemap: {e}")
            return []

    def extract_government_news(self, urls):
        """Extract government-related news articles from sitemap URLs."""
        def is_valid_url(url):
            parsed = urlparse(url)
            is_valid = bool(parsed.netloc) and bool(parsed.scheme)
            if not is_valid:
                self.logger.warning(f"Invalid URL: {url}")
            return is_valid

        news_items = []
        for idx, url in enumerate(urls):
            self.logger.debug(f"Processing URL {idx + 1}/{len(urls)}: {url}")
            if not is_valid_url(url):
                continue

            if not self.can_fetch(url):
                self.logger.warning(f"Skipping disallowed URL: {url}")
                continue

            soup = self.get_page_content(url)
            if not soup:
                self.logger.warning(f"Could not fetch content for: {url}")
                continue

            # Extract title
            title_tag = soup.find("meta", attrs={"property": "og:title"})
            title_text = title_tag["content"] if title_tag else soup.title.get_text(strip=True) if soup.title else None

            if not title_text:
                self.logger.warning(f"Missing title for URL: {url}")
                continue

            if self._is_government_news(title_text):
                self.logger.info(f"Government news found: {title_text} ({url})")
                news_items.append({'title': title_text, 'url': url})

        self.logger.info(f"Total government-related news items: {len(news_items)}")
        return news_items

    def process_news_item(self, news_item):
        """Process a single news item."""
        self.logger.info(f"Processing news item: {news_item['title']}")

        soup = self.get_page_content(news_item['url'])
        if not soup:
            return None

        # Extract article content
        content_div = soup.find("div", class_="article_content")
        if not content_div:
            self.logger.warning(f"Could not find content for: {news_item['url']}")
            return None

        # Extract all text content dynamically
        content = ' '.join(element.get_text(strip=True) for element in content_div.find_all(recursive=True) if element.get_text(strip=True))
        
        if content:
            news_item["content"] = content
            self.logger.info(f"Extracted content ({len(content)} chars) for article: {news_item['title']}")
            return news_item

        self.logger.warning(f"Failed to extract content for: {news_item['url']}")
        return None


    def _is_government_news(self, title):
        """Check if the title contains government-related keywords."""
        keywords = [
            'government', 'minister', 'policy', 'parliament', 'cabinet', 'modi',
            'congress', 'bjp', 'election', 'supreme court', 'lok sabha', 'rajya sabha'
        ]
        return any(keyword in title.lower() for keyword in keywords)
