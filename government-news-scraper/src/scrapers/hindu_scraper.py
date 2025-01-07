from .base_scraper import BaseScraper
from urllib.parse import urljoin, urlparse
import logging
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import re
import time
from datetime import datetime

class HinduScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.thehindu.com/")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/rss+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        self.rss_feeds = [
            "https://www.thehindu.com/news/national/feeder/default.rss",
            "https://www.thehindu.com/news/feeder/default.rss",
            "https://www.thehindu.com/business/feeder/default.rss",
            "https://www.thehindu.com/news/states/feeder/default.rss"
        ]

    def extract_government_news(self, soup=None):
        """Modified to work with main.py - extracts government news directly"""
        self.logger.info("Starting government news extraction from The Hindu")
        
        # Get articles from RSS feeds
        articles = self.fetch_sitemap_urls(limit=10)
        government_news = []
        
        for article in articles:
            if self._is_government_news(article['title']) or \
               any(self._is_government_news(cat) for cat in article.get('categories', [])):
                government_news.append({
                    'title': article['title'],
                    'url': article['url'],
                    'source': 'The Hindu',
                    'published_date': article.get('published_date'),
                    'author': article.get('author', ''),
                    'summary': article.get('description', '')
                })
                self.logger.info(f"Found government news: {article['title']}")

        return government_news

    def fetch_sitemap_urls(self, limit=100):
        """Fetch URLs from RSS feeds with enhanced metadata"""
        all_articles = []
        processed_urls = set()

        for feed_url in self.rss_feeds:
            try:
                self.logger.info(f"Fetching RSS feed: {feed_url}")
                response = requests.get(feed_url, headers=self.headers, timeout=30)
                response.raise_for_status()

                articles = self._parse_rss_feed(response.content)
                
                for article in articles:
                    if article['url'] not in processed_urls:
                        processed_urls.add(article['url'])
                        all_articles.append(article)

            except Exception as e:
                self.logger.error(f"Error processing RSS feed {feed_url}: {str(e)}")

        all_articles.sort(key=lambda x: x.get('published_date', ''), reverse=True)
        return all_articles[:limit]

    def process_news_item(self, news_item):
        """Process a single news item with enhanced content extraction"""
        try:
            content = self.get_page_content(news_item['url'])
            if not content:
                return None

            article_content = (
                content.find('div', {'id': re.compile(r'content-body-\d+')}) or
                content.find('div', class_='article-text')
            )

            if article_content:
                # Remove unwanted elements
                for unwanted in article_content.find_all(['script', 'style', 'aside', 'div', 'figure']):
                    unwanted.decompose()

                # Extract paragraphs
                paragraphs = article_content.find_all('p')
                text_content = ' '.join(p.get_text(strip=True) for p in paragraphs)

                if text_content:
                    news_item['content'] = text_content
                    return news_item

            return None
        except Exception as e:
            self.logger.error(f"Error processing news item: {str(e)}")
            return None

    def _parse_rss_feed(self, content):
        """Parse RSS feed content"""
        try:
            root = ET.fromstring(content)
            articles = []
            
            namespaces = {
                'content': 'http://purl.org/rss/1.0/modules/content/',
                'dc': 'http://purl.org/dc/elements/1.1/',
                'atom': 'http://www.w3.org/2005/Atom'
            }

            for item in root.findall('.//item'):
                try:
                    title = self._get_text(item.find('title'))
                    url = self._get_text(item.find('link'))
                    description = self._get_text(item.find('description'))
                    pub_date = self._get_text(item.find('pubDate'))
                    category = [self._get_text(cat) for cat in item.findall('category')]
                    author = (self._get_text(item.find('dc:creator', namespaces)) or 
                             self._get_text(item.find('author')))
                    
                    try:
                        date_obj = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
                        formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        formatted_date = pub_date

                    if url and self._is_valid_article_url(url):
                        articles.append({
                            'title': title,
                            'url': url,
                            'description': description,
                            'published_date': formatted_date,
                            'categories': category,
                            'author': author
                        })

                except Exception as e:
                    self.logger.error(f"Error parsing RSS item: {str(e)}")
                    continue

            return articles
        except ET.ParseError as e:
            self.logger.error(f"RSS parsing error: {str(e)}")
            return []

    def _get_text(self, element):
        """Safely extract text from XML element"""
        return element.text.strip() if element is not None and element.text else ''

    def _is_valid_article_url(self, url):
        """Validate article URLs"""
        try:
            parsed = urlparse(url)
            valid_paths = ['/news/', '/business/', '/national/', '/states/']
            unwanted = ['/tag/', '/author/', '/profile/', '/videos/', '/sports/']
            
            return (
                parsed.netloc == 'www.thehindu.com' and
                any(path in parsed.path for path in valid_paths) and
                not any(path in parsed.path for path in unwanted) and
                len(parsed.path.split('/')) > 3
            )
        except Exception:
            return False

    def _is_government_news(self, text):
        """Check if text contains government-related keywords"""
        keywords = [
            'government', 'minister', 'ministry', 'policy', 'parliament',
            'cabinet', 'supreme court', 'high court', 'modi', 'bjp',
            'congress', 'election', 'commission', 'bill', 'lok sabha',
            'rajya sabha', 'governor', 'president', 'govt', 'niti aayog',
            'rbi', 'budget', 'scheme', 'initiative', 'central govt',
            'state govt', 'assembly', 'bureaucrat', 'ias', 'ips',
            'ordinance', 'resolution', 'parliamentary'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)