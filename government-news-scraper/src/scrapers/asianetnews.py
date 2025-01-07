from .base_scraper import BaseScraper
import logging
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

class AsianetNewsScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://newsable.asianetnews.com/")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.main_urls = [
            "https://newsable.asianetnews.com/india",
            "https://newsable.asianetnews.com/politics"
        ]
        self.disallowed_paths = ['/related-articles', '/related-gallery', '/ad-tags-testing/', '/topic/']

    def extract_government_news(self, soup=None):
        """Modified to match the workflow pattern of other scrapers"""
        news_items = []
        
        # First get URLs from main sections
        urls = self.fetch_sitemap_urls(limit=5)  # Limiting to 5 to match other scrapers
        
        for url in urls:
            try:
                article_soup = self.get_page_content(url)
                if not article_soup:
                    continue
                
                title = self._get_title(article_soup)
                if title and self._is_government_news(title):
                    self.logger.info(f"Found government article: {title}")
                    news_items.append({
                        'title': title,
                        'url': url
                    })
                    
            except Exception as e:
                self.logger.error(f"Error extracting from {url}: {e}")
                
        return news_items

    def fetch_sitemap_urls(self, limit=None):
        urls = []
        for main_url in self.main_urls:
            try:
                soup = self.get_page_content(main_url)
                if not soup:
                    continue

                article_links = soup.find_all('a', href=re.compile(r'/india/|/politics/'))
                for link in article_links:
                    url = link.get('href')
                    if url and not any(path in url for path in self.disallowed_paths):
                        if not url.startswith('http'):
                            url = f"https://newsable.asianetnews.com{url}"
                        if url not in urls:  # Avoid duplicates
                            urls.append(url)
                self.logger.info(f"Found {len(urls)} URLs from {main_url}")

            except Exception as e:
                self.logger.error(f"Error fetching URLs from {main_url}: {e}")

        return urls[:limit] if limit and urls else urls

    def process_news_item(self, news_item):
        try:
            soup = self.get_page_content(news_item['url'])
            if not soup:
                return None

            content = self._get_content(soup)
            if not content:
                return None

            processed_item = {
                'title': news_item['title'],
                'url': news_item['url'],
                'content': content,
                'author': self._get_author(soup),
                'published_date': self._get_date(soup),
                'source': 'Asianet News',
                'scraped_at': datetime.now().isoformat()
            }
            self.logger.info(f"Processed article: {news_item['title']}")
            return processed_item

        except Exception as e:
            self.logger.error(f"Error processing {news_item['url']}: {e}")
            return None

    def _get_title(self, soup):
        selectors = [
            ('h1', 'story-title'),
            ('h1', 'article-title'),
            ('h1', None)
        ]
        
        for tag, class_name in selectors:
            title_elem = soup.find(tag, class_=class_name) if class_name else soup.find(tag)
            if title_elem:
                return title_elem.get_text(strip=True)
        return None

    def _get_content(self, soup):
        selectors = [
            ('div', 'story-content'),
            ('div', 'article-content'),
            ('div', 'story-body')
        ]
        
        for tag, class_name in selectors:
            article = soup.find(tag, class_=class_name)
            if article:
                paragraphs = article.find_all('p')
                content = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                if content:
                    return content
        return None

    def _get_author(self, soup):
        author = soup.find(['span', 'div'], class_=re.compile('author|byline'))
        return author.get_text(strip=True) if author else "Staff Reporter"

    def _get_date(self, soup):
        date = soup.find(['time', 'span'], class_=re.compile('date|time|published'))
        return date.get_text(strip=True) if date else None

    def _is_government_news(self, title):
        keywords = ['government', 'minister', 'policy', 'parliament', 'cabinet', 'legislation', 
                   'modi', 'ministry', 'supreme court', 'high court', 'bjp', 'congress', 
                   'election', 'commission', 'bill', 'lok sabha', 'rajya sabha', 'governor', 
                   'pm', 'chief minister', 'mla', 'mp', 'president', 'govt']
        return any(keyword.lower() in title.lower() for keyword in keywords)