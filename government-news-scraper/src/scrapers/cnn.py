import logging
import re
from urllib.parse import urljoin
from .base_scraper import BaseScraper

class CNNNews18Scraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.cnnnews18.com/")
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_government_news(self, soup):
        """
        Extract government-related news from CNN-News18.
        """
        news_items = []

        # Potential article selectors (you may need to inspect the page to get the exact tags and classes)
        article_selectors = [
            ('div', 'top-story__headline'),  # Example class name for article headline
            ('section', 'news-block'),  # Example section tag
            ('article', 'story'),  # A generic fallback if others don't work
        ]

        all_articles = []
        for tag, class_name in article_selectors:
            found_articles = soup.find_all(tag, class_=class_name)
            self.logger.info(f"Found {len(found_articles)} articles with selector {tag}.{class_name}")
            all_articles.extend(found_articles)

        if not all_articles:
            self.logger.warning("No articles found. Verify the HTML structure.")

        for article in all_articles:
            title_elem = article.find('a')
            link_elem = article.find('a', href=True)

            if title_elem and link_elem:
                title_text = title_elem.get_text(strip=True)
                link_href = link_elem['href']

                if link_href.startswith('/'):
                    link_href = urljoin(self.base_url, link_href)

                if not self.can_fetch(link_href):
                    self.logger.warning(f"Skipping disallowed URL: {link_href}")
                    continue

                if self._is_government_news(title_text):
                    news_items.append({
                        "title": title_text,
                        "url": link_href
                    })
                    self.logger.info(f"Added government news: Title: {title_text}, Link: {link_href}")
                else:
                    self.logger.debug(f"Skipped non-government news: {title_text}")

        self.logger.info(f"Total government-related news items: {len(news_items)}")
        return news_items

    def process_news_item(self, news_item):
        self.logger.info(f"Processing article: {news_item['title']}")

        soup = self.get_page_content(news_item['url'])
        if not soup:
            self.logger.warning(f"Could not fetch content for: {news_item['url']}")
            return None

        selectors = [
            ('div', 'article-body'),  # Example class name for article body, replace with correct one
            ('section', 'content-wrapper'),  # Another potential selector
        ]

        article_body = None
        for tag, class_name in selectors:
            article_body = soup.find(tag, class_=class_name)
            if article_body:
                self.logger.debug(f"Found article body using selector: {tag}.{class_name}")
                break

        if article_body:
            paragraphs = article_body.find_all(['p', 'div', 'span'])
            content = " ".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

            if content:
                self.logger.info(f"Extracted content for: {news_item['title']}")
                news_item['content'] = content
                return news_item

        self.logger.warning(f"Could not find article body for: {news_item['url']}")
        return None

    def _is_government_news(self, title):
        government_keywords = [
            'government', 'minister', 'policy', 'parliament',
            'cabinet', 'legislation', 'bureaucracy', 'official',
            'modi', 'ministry', 'supreme court', 'high court',
            'bjp', 'congress', 'election', 'commission', 'bill',
            'lok sabha', 'rajya sabha', 'governor', 'pm',
            'chief minister', 'mla', 'mp', 'president', 'govt'
        ]

        title_lower = title.lower()
        return any(keyword in title_lower for keyword in government_keywords)
