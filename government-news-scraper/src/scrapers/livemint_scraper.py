from .base_scraper import BaseScraper
from urllib.parse import urljoin
import logging
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

class LiveMintScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.livemint.com/")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.sitemap_url = "https://www.livemint.com/sitemap/today.xml"

    def fetch_sitemap_urls(self):
        """
        Fetch URLs from the sitemap to ensure adherence to robots.txt.

        Returns:
            list: List of article URLs from the sitemap.
        """
        try:
            response = requests.get(self.sitemap_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            urls = [url.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text for url in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url")]
            self.logger.info(f"Fetched {len(urls)} URLs from the sitemap.")
            return urls
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching sitemap: {e}")
            return []

    def extract_government_news(self, urls):
        """
        Extract government-related news articles from sitemap URLs.

        Args:
            urls (list): List of URLs to process.

        Returns:
            list: List of government news items with title and URL.
        """
        news_items = []

        for url in urls:
            try:
                soup = self.get_page_content(url)
                if not soup:
                    continue

                title = soup.find("meta", attrs={"property": "og:title"})
                title_text = title["content"] if title else soup.title.get_text(strip=True) if soup.title else None

                if title_text and self._is_government_news(title_text):
                    self.logger.info(f"Found government news: Title: {title_text}, Link: {url}")
                    news_items.append({
                        'title': title_text,
                        'link': url
                    })

            except Exception as e:
                self.logger.warning(f"Error processing URL {url}: {e}")

        self.logger.info(f"Total government-related news items: {len(news_items)}")
        return news_items


    def process_news_item(self, news_item):
        """
        Process a single news item by fetching its full content.

        Args:
            news_item (dict): News item with title and URL.

        Returns:
            dict or None: Processed news item with content, or None if processing fails.
        """
        self.logger.info(f"Processing article: {news_item['title']}")

        soup = self.get_page_content(news_item['link'])
        if not soup:
            self.logger.warning(f"Could not fetch content for: {news_item['link']}")
            return None

        # Selectors for article content
        selectors = [
            ('div', 'content'),
            ('div', 'articleParagraph'),
        ]

        article_body = None
        for tag, class_name in selectors:
            article_body = soup.find(tag, class_=re.compile(class_name))
            if article_body:
                self.logger.info(f"Found content with selector: {tag}.{class_name}")
                break

        if article_body:
            paragraphs = article_body.find_all('p')
            content = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

            if content:
                news_item['content'] = content
                self.logger.info(f"Successfully extracted content ({len(content)} chars) for article: {news_item['title']}")
                return news_item

        self.logger.warning(f"Could not find article body for: {news_item['link']}")
        return None

    def _is_government_news(self, title):
        """
        Determine if the news is government-related.

        Args:
            title (str): Title of the news article.

        Returns:
            bool: True if the title contains government-related keywords, False otherwise.
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
        self.logger.info(f"Title: {title}, Is government news: {match}")
        return match
