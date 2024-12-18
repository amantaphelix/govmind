from .base_scraper import BaseScraper
import re
from urllib.parse import urljoin
import logging

class DeccanChronicleScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.deccanchronicle.com/")
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_government_news(self, soup):
        """
        Extract government-related news from Deccan Chronicle using updated HTML structure.
        """
        news_items = []

        # Potential article selectors
        article_selectors = [
            ('div', 'story'),
            ('div', 'list-item'),
            ('div', 'story_content'),
            ('div', 'details-story-wrapper'),
            ('div', 'entry-main-content'),
            ('div', re.compile("content")),  # Generic fallback
            ('article', None),
        ]

        all_articles = []
        for tag, class_name in article_selectors:
            found_articles = soup.find_all(tag, class_=class_name)
            self.logger.info(f"Found {len(found_articles)} articles with selector {tag}.{class_name}")
            all_articles.extend(found_articles)

        if not all_articles:
            self.logger.warning("No articles found. Verify the HTML structure.")

        for article in all_articles:
            # Extract title and link
            title_elem = article.find('a')
            link_elem = article.find('a', href=True)

            if title_elem and link_elem:
                title_text = title_elem.get_text(strip=True)
                link_href = link_elem['href']

                # Ensure full URL
                if link_href.startswith('/'):
                    link_href = urljoin(self.base_url, link_href)

                # Check if URL can be fetched (robots.txt)
                if not self.can_fetch(link_href):
                    self.logger.warning(f"Skipping disallowed URL: {link_href}")
                    continue

                # Check if it's government news
                if self._is_government_news(title_text):
                    news_items.append({
                        "title": title_text,
                        "url": link_href  # Use 'url' key instead of 'link'
                    })
                    self.logger.info(f"Added government news: Title: {title_text}, Link: {link_href}")
                else:
                    self.logger.debug(f"Skipped non-government news: {title_text}")

        self.logger.info(f"Total government-related news items: {len(news_items)}")
        return news_items

    def process_news_item(self, news_item):
        self.logger.info(f"Processing article: {news_item['title']}")

        # Fetch the article page content
        soup = self.get_page_content(news_item['url'])
        if not soup:
            self.logger.warning(f"Could not fetch content for: {news_item['url']}")
            return None

        # Potential selectors for the article body
        selectors = [
            ('div', 'entry-main-content'),
            ('div', 'story_content'),
            ('div', 'article-body'),
            ('div', 'details-story-wrapper'),
            ('div', re.compile('content')),  # Generic fallback for any 'content' class
            ('section', None),  # Some sites may use <section> tags
        ]

        article_body = None
        for tag, class_name in selectors:
            article_body = soup.find(tag, class_=class_name)
            if article_body:
                self.logger.debug(f"Found article body using selector: {tag}.{class_name}")
                break

        if article_body:
            # Extract text from all nested tags
            paragraphs = article_body.find_all(['p', 'div', 'span'])
            content = " ".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

            if content:
                self.logger.info(f"Extracted content ({len(content)} chars) for: {news_item['title']}")
                self.logger.debug(f"Content preview: {content[:500]}...")
                news_item['content'] = content
                return news_item

        self.logger.warning(f"Could not find article body for: {news_item['url']}")
        return None


    def _is_government_news(self, title):
        """
        Check if the article title contains government-related keywords.
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
