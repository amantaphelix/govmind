from .base_scraper import BaseScraper
import re
from urllib.parse import urljoin
import logging

class IndiaTodayScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.indiatoday.in/")
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_government_news(self, soup):
        news_items = []

        article_selectors = [
            ('div', 'story'),
            ('div', 'story-list'),
            ('div', 'B_homepage_article'),
            ('div', 'view-content'),
            ('div', 'widget-content'),
        ]

        all_articles = []
        for tag, class_name in article_selectors:
            found_articles = soup.find_all(tag, class_=re.compile(class_name))
            all_articles.extend(found_articles)

        for article in all_articles:
            title_elem = None
            for tag in ['h1', 'h2', 'h3', 'h4']:
                title_elem = article.find(tag)
                if title_elem:
                    break

            link_elem = article.find('a')

            if title_elem and link_elem:
                title_text = title_elem.get_text(strip=True)
                link_href = link_elem.get('href', '')

                if link_href.startswith('/'):
                    link_href = urljoin(self.base_url, link_href)

                self.logger.info(f"Found article: {title_text}, Link: {link_href}")

                if self._is_government_news(title_text) and link_href:
                    news_items.append({
                        'title': title_text,
                        'url': link_href  # Changed from 'link'
                    })

        return news_items

    def process_news_item(self, news_item):
        soup = self.get_page_content(news_item['url'])

        if not soup:
            return None

        article_body = None
        selectors = [
            ('div', 'description'),
            ('div', 'story-right'),
            ('div', 'content-area'),
            ('div', 'story-details'),
            ('div', 'article-body'),
        ]

        for tag, class_name in selectors:
            article_body = soup.find(tag, class_=class_name)
            if article_body:
                break

        if article_body:
            paragraphs = article_body.find_all(['p', 'div'], class_=lambda x: x != 'also-read')
            content = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

            if content:
                news_item['content'] = content
                return news_item

        return None



    def _is_government_news(self, title):
        """
        Determine if the news is government-related
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
        match = any(keyword.lower() in title_lower for keyword in government_keywords)
        return match
