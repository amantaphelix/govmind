from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import logging
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse  

class QuintScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.thequint.com/")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.sitemap_base = "https://www.thequint.com/sitemap"
        
    def fetch_sitemap_urls(self, limit=10):
        """Fetch URLs from both today's and yesterday's sitemaps"""
        urls = []
        sitemaps = [
            f"{self.sitemap_base}/today",
            f"{self.sitemap_base}/yesterday"
        ]
        
        for sitemap_url in sitemaps:
            try:
                soup = self.get_page_content(sitemap_url)
                if not soup:
                    continue

                try:
                    # Parse XML content
                    root = ET.fromstring(str(soup))
                    sitemap_urls = [
                        url.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
                        for url in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url")
                        if url.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc") is not None
                    ]
                    urls.extend(sitemap_urls)
                    self.logger.info(f"Fetched {len(sitemap_urls)} URLs from {sitemap_url}")
                except ET.ParseError as e:
                    self.logger.error(f"Error parsing sitemap {sitemap_url}: {e}")
            
            except Exception as e:
                self.logger.error(f"Error fetching sitemap {sitemap_url}: {e}")
        
        self.logger.info(f"Total URLs fetched: {len(urls)}")
        return urls[:limit]

    def extract_government_news(self, urls_or_soup):
        """Extract government-related news articles"""
        news_items = []
        
        # Handle both URL list and soup input
        if isinstance(urls_or_soup, list):
            urls = urls_or_soup
        else:
            # If soup is provided, extract URLs from it
            urls = self._extract_urls_from_soup(urls_or_soup)

        for url in urls:
            if not self.can_fetch(url):
                self.logger.warning(f"Skipping disallowed URL: {url}")
                continue

            soup = self.get_page_content(url)
            if not soup:
                continue

            title = self._extract_title(soup)
            if not title:
                continue

            if self._is_government_news(title):
                self.logger.info(f"Found government news: {title}")
                news_items.append({
                    'title': title,
                    'url': url,
                    'source': 'The Quint'
                })

        return news_items

    def process_news_item(self, news_item):
        """Process a single news item to extract its full content"""
        soup = self.get_page_content(news_item['url'])
        if not soup:
            return None

        content = self._extract_content(soup)
        if not content:
            return None

        news_item['content'] = content
        
        # Extract metadata
        self._extract_metadata(soup, news_item)
        
        return news_item

    def _extract_title(self, soup):
        """Extract title using multiple selectors"""
        selectors = [
            ("meta", {"property": "og:title"}),
            ("h1", {"class": "story-headline"}),
            ("h1", {"class": "story-title"}),
            ("title", {})
        ]

        for tag, attrs in selectors:
            if tag == "meta":
                element = soup.find(tag, attrs=attrs)
                if element:
                    return element.get("content")
            else:
                element = soup.find(tag, attrs=attrs)
                if element:
                    return element.get_text(strip=True)
        
        return None

    def _extract_content(self, soup):
        """Extract article content"""
        content_selectors = [
            ('div', 'story-element-text'),
            ('div', 'story-content'),
            ('article', 'story-details')
        ]

        content = []
        for tag, class_name in content_selectors:
            elements = soup.find_all(tag, class_=class_name)
            if elements:
                for element in elements:
                    paragraphs = element.find_all('p')
                    content.extend([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        return ' '.join(content) if content else None

    def _extract_metadata(self, soup, news_item):
        """Extract additional metadata from the article"""
        try:
            # Published date
            date_meta = soup.find('meta', property='article:published_time')
            if date_meta:
                news_item['published_date'] = date_meta['content']

            # Author
            author_meta = soup.find('meta', property='author')
            if author_meta:
                news_item['author'] = author_meta['content']

            # Category
            category_meta = soup.find('meta', property='article:section')
            if category_meta:
                news_item['category'] = category_meta['content']

        except Exception as e:
            self.logger.error(f"Error extracting metadata: {e}")

    def _extract_urls_from_soup(self, soup):
        """Extract article URLs from the main page soup"""
        urls = []
        for link in soup.find_all('a', href=True):
            url = link['href']
            if not url.startswith('http'):
                url = urljoin(self.base_url, url)
            if '/news/' in url or '/opinion/' in url:
                urls.append(url)
        return urls

    def _is_government_news(self, title):
        """Check if the news is government-related using keywords"""
        government_keywords = [
            'government', 'minister', 'policy', 'parliament',
            'cabinet', 'legislation', 'bureaucracy', 'official',
            'modi', 'ministry', 'supreme court', 'high court',
            'bjp', 'congress', 'election', 'commission', 'bill',
            'lok sabha', 'rajya sabha', 'governor', 'pm',
            'chief minister', 'mla', 'mp', 'president', 'govt'
        ]
        
        title_lower = title.lower()
        matches = [keyword for keyword in government_keywords if keyword in title_lower]
        if matches:
            self.logger.debug(f"Government keywords found in title: {matches}")
            return True
        return False