from .base_scraper import BaseScraper
from urllib.parse import urljoin
import logging
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import re
from datetime import datetime

class TimesNowScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            base_url="https://www.timesnownews.com/",
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self.sitemap_url = "https://www.timesnownews.com/google-news-sitemap-en.xml"
        self.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })

    def fetch_sitemap_urls(self, limit=100):
        try:
            response = requests.get(self.sitemap_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            namespaces = {
                'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                'news': 'http://www.google.com/schemas/sitemap-news/0.9'
            }
            
            urls = []
            for url in root.findall('.//ns:url', namespaces):
                loc = url.find('ns:loc', namespaces)
                if loc is not None and loc.text and '/videos/' not in loc.text:  # Skip video URLs
                    urls.append(loc.text)
            
            return urls[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching sitemap: {e}")
            return []

    def extract_government_news(self, urls):
        news_items = []
        
        for url in urls:
            try:
                soup = self.get_page_content(url)
                if not soup:
                    continue

                # Try multiple methods to find title
                title = None
                title_selectors = [
                    ('h1', {'class': ['article-heading', '_1Y-96', 'story-headline', 'story_title', '_38KuG']}),
                    ('meta', {'property': 'og:title'}),
                    ('h1', {'class': 'story_title'})
                ]

                for tag, attrs in title_selectors:
                    element = soup.find(tag, attrs)
                    if element:
                        title = element.get('content') if tag == 'meta' else element.get_text(strip=True)
                        break

                if not title or not self._is_government_news(title):
                    continue

                timestamp = self._extract_timestamp(soup)
                
                news_items.append({
                    'title': title,
                    'url': url,
                    'timestamp': timestamp,
                    'source': 'TimesNow'
                })
                
            except Exception as e:
                self.logger.error(f"Error processing URL {url}: {e}")
                continue

        return news_items

    def process_news_item(self, news_item):
        if not news_item or not news_item.get('url'):
            return None

        try:
            soup = self.get_page_content(news_item['url'])
            if not soup:
                return None

            content = None
            
            # Method 1: Article body with specific class
            article_selectors = [
                ('div', {'class': ['article-body', 'story-article', '_3YYSt', 'story__content', 'article__content']}),
                ('div', {'itemprop': 'articleBody'}),
                ('div', {'class': 'story_details'}),
                ('div', {'class': 'article-content'})
            ]

            for tag, attrs in article_selectors:
                article_div = soup.find(tag, attrs)
                if article_div:
                    # Remove unwanted elements
                    for unwanted in article_div.find_all(['script', 'style', 'iframe', 'figure', 'div'], 
                                                       class_=['related-news', 'social-share', '_1_AcW', '_3gqGT']):
                        unwanted.decompose()
                    
                    paragraphs = article_div.find_all(['p', 'div'], recursive=False)
                    if paragraphs:
                        content = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                        break

            if content and len(content) > 100:  # Ensure meaningful content
                # Clean the content
                content = re.sub(r'\s+', ' ', content)
                content = content.strip()
                
                news_item['content'] = content
                news_item['extracted_at'] = datetime.now().isoformat()
                return news_item

        except Exception as e:
            self.logger.error(f"Error processing article {news_item['url']}: {e}")
        
        return None

    def _extract_timestamp(self, soup):
        try:
            timestamp_selectors = [
                ('meta', {'property': 'article:published_time'}),
                ('time', {'class': ['date-time', 'article__date']}),
                ('meta', {'itemprop': 'datePublished'}),
                ('span', {'class': ['article-time', 'date']}),
                ('div', {'class': 'timestamp'})
            ]
            
            for tag, attrs in timestamp_selectors:
                element = soup.find(tag, attrs)
                if element:
                    if element.get('content'):
                        return element['content']
                    return element.get_text(strip=True)
                    
        except Exception as e:
            self.logger.error(f"Error extracting timestamp: {e}")
        
        return None

    def _is_government_news(self, title):
        government_keywords = [
            'government', 'minister', 'policy', 'parliament', 'cabinet',
            'legislation', 'modi', 'ministry', 'supreme court', 'high court',
            'bjp', 'congress', 'election', 'commission', 'bill',
            'lok sabha', 'rajya sabha', 'governor', 'pm', 'chief minister',
            'mla', 'mp', 'president', 'govt'
        ]
        
        title_lower = title.lower()
        return any(keyword in title_lower for keyword in government_keywords)