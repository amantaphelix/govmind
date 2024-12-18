from .base_scraper import BaseScraper
import re
from urllib.parse import urljoin
import logging

class ZeeNewsScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://zeenews.india.com/")
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_government_news(self, soup):
        """
        Extract government-related news articles from the soup object

        Args:
            soup (BeautifulSoup): Parsed HTML content

        Returns:
            list: List of government news items with title and URL
        """
        news_items = []

        # Selectors for finding articles
        article_selectors = [
            ('div', 'newsList'),  # Adjust this if needed based on the site structure
            ('div', 'other-article'),
            ('div', 'top-news-list'),
        ]

        all_articles = []
        for tag, class_name in article_selectors:
            found_articles = soup.find_all(tag, class_=re.compile(class_name))
            self.logger.info(f"Found {len(found_articles)} articles with selector {tag}.{class_name}")
            all_articles.extend(found_articles)

        self.logger.info(f"Total articles found: {len(all_articles)}")

        for article in all_articles:
            # Extract title and link
            title_elem = article.find('a')
            link_elem = article.find('a')

            if title_elem and link_elem:
                title_text = title_elem.get_text(strip=True)
                link_href = link_elem.get('href', '')

                # Ensure full URL
                if link_href.startswith('/'):
                    link_href = urljoin(self.base_url, link_href)

                if not self.can_fetch(link_href):
                    self.logger.warning(f"Skipping disallowed URL: {link_href}")
                    continue

                if self._is_government_news(title_text):
                    news_items.append({
                        'title': title_text,
                        'link': link_href
                    })
                    self.logger.info(f"Found government news: Title: {title_text}, Link: {link_href}")
                else:
                    self.logger.info(f"Skipped non-government news: Title: {title_text}, Link: {link_href}")

        return news_items

    def process_news_item(self, news_item):
        """
        Process a single news item by fetching its full content

        Args:
            news_item (dict): News item with title and URL

        Returns:
            dict or None: Processed news item with content, or None if processing fails
        """
        self.logger.info(f"Processing article: {news_item['title']}")

        # Respect rate limits and fetch the page
        self._respect_rate_limits()
        soup = self.get_page_content(news_item['link'])

        if not soup:
            self.logger.warning(f"Could not fetch content for: {news_item['link']}")
            return None

        # Selectors for article content
        selectors = [
            ('div', 'article'),
            ('div', 'content'),
            ('div', 'newsText'),
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
        Determine if the news is government-related

        Args:
            title (str): Title of the news article

        Returns:
            bool: True if the title contains government-related keywords, False otherwise
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
