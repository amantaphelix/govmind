from .base_scraper import BaseScraper
from urllib.parse import urljoin, urlparse
import logging
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import re


class IndianExpressScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://indianexpress.com/")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.sitemap_url = "https://indianexpress.com/news-sitemap.xml"

    def fetch_sitemap_urls(self, limit=100):
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
        """
        Extract government-related news articles from sitemap URLs.
        """
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
                self.logger.warning(f"Invalid URL skipped: {url}")
                continue

            if not self.can_fetch(url):
                self.logger.warning(f"Skipping disallowed URL: {url}")
                continue

            soup = self.get_page_content(url)
            if not soup:
                self.logger.warning(f"Could not fetch content for: {url}")
                continue

            # Log the HTML content for debugging
            self.logger.debug(f"Fetched HTML for URL: {url}\n{str(soup)[:1000]}\n...")

            # Extract title from meta tags or page content
            title = soup.find("meta", attrs={"property": "og:title"})
            title_text = title["content"] if title else soup.title.get_text(strip=True) if soup.title else None

            if not title_text:
                self.logger.warning(f"Missing title for URL: {url}")
                continue

            self.logger.debug(f"Extracted title: {title_text}")

            if self._is_government_news(title_text):
                self.logger.info(f"Found government news: Title: {title_text}, Link: {url}")
                news_items.append({
                    'title': title_text,
                    'url': url  # Ensure the key matches the database schema
                })

        self.logger.info(f"Total government-related news items: {len(news_items)}")
        return news_items

    def process_news_item(self, news_item):
        """
        Process a single news item by fetching its full content.
        """
        self.logger.info(f"Processing article: {news_item['title']}")

        soup = self.get_page_content(news_item['url'])
        if not soup:
            self.logger.warning(f"Could not fetch content for: {news_item['url']}")
            return None

        # Log the article's fetched HTML for debugging
        self.logger.debug(f"Fetched article HTML for URL: {news_item['url']}\n{str(soup)[:1000]}\n...")

        selectors = [
            ('div', 'full-details'),
            ('div', 'article-content'),
        ]

        article_body = None
        for tag, class_name in selectors:
            article_body = soup.find(tag, class_=class_name)
            if article_body:
                self.logger.debug(f"Found article body with selector: {tag}.{class_name}")
                break

        if article_body:
            paragraphs = article_body.find_all('p')
            content = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

            if content:
                news_item['content'] = content
                self.logger.info(f"Successfully extracted content ({len(content)} chars) for article: {news_item['title']}")
                return news_item

        self.logger.warning(f"Could not find article body for: {news_item['url']}")
        return None

    def _is_government_news(self, title):
        """
        Determine if the news is government-related.
        """
        government_keywords = [
            'government', 'minister', 'policy', 'parliament',
            'cabinet', 'legislation', 'bureaucracy', 'official',
            'modi', 'ministry', 'supreme court', 'high court',
            'bjp', 'congress', 'election', 'commission', 'bill',
            'lok sabha', 'rajya sabha', 'governor', 'pm',
            'chief minister', 'mla', 'mp', 'president', 'govt'
        ]

        title_lower = title.lower()
        match = any(keyword in title_lower for keyword in government_keywords)
        self.logger.debug(f"Title: {title}, Is government news: {match}")
        return match


