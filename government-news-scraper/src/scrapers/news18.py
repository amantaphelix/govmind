from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import logging
import requests
import re

class News18Scraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.news18.com/")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.sitemap_url = "https://www.news18.com/commonfeeds/v1/eng/sitemap/google-news.xml"
        
        # Patterns for URLs to skip
        self.disallowed_patterns = [
            re.compile(pattern) for pattern in [
                r'/cricketnext/series/',
                r'/assembly-elections-\d+/',
                r'/photogallery/page-',
                r'/videos/',
                r'/amp/',
                r'/rss/',
                r'/sitemap/',
                r'/tag/',
                r'/topics/'
            ]
        ]

    def fetch_sitemap_urls(self, limit=50):
        """Fetch URLs from News18's sitemap"""
        try:
            self.logger.debug(f"Fetching sitemap from {self.sitemap_url}")
            response = requests.get(self.sitemap_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            urls = []
            
            # Handle multiple possible XML namespaces
            namespaces = {
                'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                'news': 'http://www.google.com/schemas/sitemap-news/0.9'
            }
            
            # Try with explicit namespaces first
            locations = root.findall(".//sitemap:url/sitemap:loc", namespaces)
            if not locations:
                # Fallback to searching without namespace
                locations = root.findall(".//loc")
            
            for loc in locations[:limit]:
                url = loc.text
                if url and not any(pattern.search(url) for pattern in self.disallowed_patterns):
                    urls.append(url)
            
            self.logger.info(f"Fetched {len(urls)} URLs from the sitemap")
            return urls
            
        except Exception as e:
            self.logger.error(f"Error fetching sitemap: {e}")
            return []

    def extract_government_news(self, urls):
        """Extract government-related news from the provided URLs"""
        news_items = []
        
        for url in urls:
            if not self.can_fetch(url):
                self.logger.warning(f"Skipping disallowed URL: {url}")
                continue
                
            soup = self.get_page_content(url)
            if not soup:
                self.logger.warning(f"Could not fetch content for: {url}")
                continue

            title = self._extract_title(soup)
            if not title:
                self.logger.warning(f"Could not extract title for: {url}")
                continue

            if self._is_government_news(title):
                self.logger.info(f"Found government news: {title}")
                news_items.append({
                    'title': title,
                    'url': url
                })

        return news_items

    def _extract_title(self, soup):
        """Extract title using multiple selectors"""
        title_selectors = [
            lambda s: s.find("meta", property="og:title"),
            lambda s: s.find("h1", class_="article_heading"),
            lambda s: s.find("h1", class_="story_title"),
            lambda s: s.find("h1", class_="article-title"),
            lambda s: s.find("title")
        ]
        
        for selector in title_selectors:
            element = selector(soup)
            if element:
                title = element.get("content") if element.get("content") else element.get_text()
                if title:
                    return title.replace(" - News18", "").strip()
        return None

    def _extract_article_content(self, soup):
        """
        Extract article content from News18 article page
        Returns a dictionary containing article components
        """
        article = {}
        
        # Extract title
        title_element = soup.find('h1', class_='attl')
        if title_element:
            article['title'] = title_element.get_text(strip=True)
        
        # Extract subtitle/description
        subtitle = soup.find('h2', class_='asubttl-schema')
        if subtitle:
            article['subtitle'] = subtitle.get_text(strip=True)
        
        # Extract author information
        author_section = soup.find('div', class_='rptby')
        if author_section:
            authors = author_section.find_all('a', class_='cp_author_byline')
            article['authors'] = [author.get_text(strip=True) for author in authors]
        
        # Extract publication date
        date_element = soup.find('time')
        if date_element:
            article['published_date'] = date_element.get_text(strip=True)
        
        # Extract main content
        content = []
        
        # Find all paragraphs with story_para class
        paragraphs = soup.find_all('p', class_=lambda x: x and x.startswith('story_para_'))
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text:  # Only add non-empty paragraphs
                content.append(text)
        
        article['content'] = '\n\n'.join(content)
        
        # Extract tags
        tags_section = soup.find('div', class_='atbtlink tags')
        if tags_section:
            tags = tags_section.find_all('a', class_='link')
            article['tags'] = [tag.get_text(strip=True) for tag in tags]
        
        # Extract location
        location_section = soup.find('ul', class_='Location')
        if location_section:
            location = location_section.find('span', class_=False)  # Get span without class
            if location:
                article['location'] = location.get_text(strip=True)
        
        # Extract breadcrumb for categories
        breadcrumb = soup.find('div', class_='brdcrmb')
        if breadcrumb:
            categories = [a.get_text(strip=True) for a in breadcrumb.find_all('a')]
            article['categories'] = categories
        
        return article

    def process_news_item(self, news_item):
        """
        Process a single news item by extracting its content using the enhanced extractor
        """
        self.logger.info(f"Processing article: {news_item['url']}")
        
        soup = self.get_page_content(news_item['url'])
        if not soup:
            self.logger.warning(f"Could not fetch content for: {news_item['url']}")
            return None
        
        try:
            # Extract detailed article content using the class method
            article_content = self._extract_article_content(soup)
            
            # Merge the extracted content with the existing news item
            news_item.update(article_content)
            
            self.logger.info(f"Successfully extracted content for article: {news_item['title']}")
            return news_item
            
        except Exception as e:
            self.logger.error(f"Error processing article {news_item['url']}: {str(e)}")
            return None

    def _is_government_news(self, title):
        """Check if the news is government-related"""
        if not title:
            return False
            
        government_keywords = [
            'government', 'minister', 'policy', 'parliament',
            'cabinet', 'legislation', 'bureaucracy', 'official',
            'modi', 'ministry', 'supreme court', 'high court',
            'bjp', 'congress', 'election', 'commission', 'bill',
            'lok sabha', 'rajya sabha', 'governor', 'pm',
            'chief minister', 'cm', 'mla', 'mp', 'president',
            'govt'
        ]
        
        title_lower = title.lower()
        return any(keyword in title_lower for keyword in government_keywords)