from .base_scraper import BaseScraper
import re
from urllib.parse import urljoin
import logging

class HinduScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.thehindu.com/")
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_government_news(self, soup):
        import logging

class HinduScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.thehindu.com/")
        self.logger = logging.getLogger(self.__class__.__name__)
        logging.basicConfig(level=logging.DEBUG)  # Set log level to DEBUG

    def extract_government_news(self, soup):
        news_items = []

        # Refined article selectors
        article_selectors = [
            ('div', 'story'),
            ('div', 'section-story'),
            ('div', 'content'),  # General news content
            ('article', 'story'),  # More specific
        ]

        all_articles = []
        for tag, class_name in article_selectors:
            found_articles = soup.find_all(tag, class_=re.compile(class_name))
            self.logger.info(f"Found {len(found_articles)} articles with selector {tag}.{class_name}")
            all_articles.extend(found_articles)

        # Debugging: Explicitly print the titles of the found articles
        self.logger.debug(f"Total found articles: {len(all_articles)}")
        for article in all_articles:
            title_elem = None
            for tag in ['h1', 'h2', 'h3']:
                title_elem = article.find(tag)
                if title_elem:
                    break

            if title_elem:
                title_text = title_elem.get_text(strip=True)
                self.logger.debug(f"Article Title: {title_text}")
            else:
                self.logger.debug("No title found for an article.")

        for article in all_articles:
            # Extract title and link
            title_elem = None
            for tag in ['h1', 'h2', 'h3']:
                title_elem = article.find(tag)
                if title_elem:
                    break

            link_elem = article.find('a', href=True)

            if title_elem and link_elem:
                title_text = title_elem.get_text(strip=True)
                link_href = link_elem['href']

                # Log title and link before checking
                self.logger.debug(f"Title found: {title_text}, URL: {link_href}")

                # Ignore irrelevant titles
                if any(keyword in title_text.lower() for keyword in ['featured', 'infographic', 'advert']):
                    self.logger.debug(f"Skipping irrelevant title: {title_text}")
                    continue

                # Ensure full URL
                if link_href.startswith('/'):
                    link_href = urljoin(self.base_url, link_href)

                # Validate news URLs
                if not re.search(r'/news/|/article/|/topic/', link_href):
                    self.logger.debug(f"Skipping non-news URL: {link_href}")
                    continue

                # Check if it's government-related news
                if self._is_government_news(title_text):
                    news_items.append({
                        'title': title_text,
                        'url': link_href
                    })
                    self.logger.info(f"Added government news: Title: {title_text}, Link: {link_href}")
                else:
                    self.logger.debug(f"Skipped non-government news: {title_text}")

        self.logger.info(f"Total government-related news items: {len(news_items)}")
        return news_items



    def process_news_item(self, news_item):
        """
        Process and extract full article details.
        """
        self.logger.info(f"Processing article: {news_item['title']}")

        soup = self.get_page_content(news_item['url'])
        if not soup:
            self.logger.warning(f"Could not fetch content for: {news_item['url']}")
            return None

        # Refined selectors for article body
        selectors = [
            ('div', 'article-body'),
            ('div', 'story-content'),
            ('div', 'content'),
            ('section', None),
        ]

        article_body = None
        for tag, class_name in selectors:
            article_body = soup.find(tag, class_=class_name)
            if article_body:
                self.logger.debug(f"Found article body using selector: {tag}.{class_name}")
                break

        # Debugging: If the body is found, log its structure
        if article_body:
            self.logger.debug(f"Article body found: {article_body.prettify()}")

        if article_body:
            paragraphs = article_body.find_all(['p', 'div'])
            content = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

            if content:
                news_item['content'] = content
                self.logger.info(f"Extracted content ({len(content)} chars) for: {news_item['title']}")
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

        # Log title and the matching result
        self.logger.debug(f"Checking title: {title}, Match found: {match}")
        return match
