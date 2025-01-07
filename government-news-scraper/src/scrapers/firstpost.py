from .base_scraper import BaseScraper
from urllib.parse import urljoin, urlparse, parse_qs
import logging
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import re
import time
from typing import List, Dict, Set

class FirstPostScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.firstpost.com", user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        self.logger = logging.getLogger(self.__class__.__name__)
        self.sitemap_url = "https://www.firstpost.com/commonfeeds/v1/mfp/sitemap/google-news.xml"
        self.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self._init_keywords()
        # Keep your existing disallowed_patterns

    def _init_keywords(self):
        """Initialize keyword sets for Indian government news detection"""
        self.indian_govt_keywords = {
            'political_bodies': {
                'lok sabha', 'rajya sabha', 'parliament', 'vidhan sabha', 
                'niti aayog', 'rbi', 'supreme court', 'high court'
            },
            'political_roles': {
                'prime minister', 'modi', 'president murmu', 'chief minister',
                'governor', 'cabinet minister', 'home minister', 'amit shah',
                'finance minister', 'nirmala sitharaman', 'minister'
            },
            'indian_parties': {
                'bjp', 'congress', 'aap', 'tmc', 'dmk', 'admk', 'ncp', 
                'shiv sena', 'brs', 'ysr', 'left front', 'communist party'
            },
            'govt_departments': {
                'ministry', 'department', 'commission', 'committee',
                'bureau', 'board', 'authority', 'council'
            },
            'states': {
                'delhi', 'mumbai', 'maharashtra', 'gujarat', 'tamil nadu',
                'karnataka', 'kerala', 'punjab', 'haryana', 'uttar pradesh',
                'bihar', 'bengal', 'odisha', 'assam', 'rajasthan'
            }
        }

        # International keywords to exclude
        self.international_keywords = {
            'biden', 'trump', 'putin', 'china', 'pakistan', 'russia', 'ukraine',
            'united states', 'european union', 'united nations', 'who',
            'bangladesh', 'sri lanka', 'nepal', 'white house'
        }

        # Compile patterns
        self.govt_patterns = {
            category: re.compile('|'.join(r'\b' + re.escape(word) + r'\b' 
                               for word in words), re.IGNORECASE)
            for category, words in self.indian_govt_keywords.items()
        }
        
        self.international_pattern = re.compile(
            '|'.join(r'\b' + re.escape(word) + r'\b' 
            for word in self.international_keywords), 
            re.IGNORECASE
        )

    def _is_government_news(self, title: str, content: str = None) -> bool:
        """
        Determine if the news is related to Indian government.
        
        Args:
            title: Article title
            content: Article content (if available)
            
        Returns:
            bool: True if article is about Indian government
        """
        text_to_check = f"{title} {content if content else ''}"
        text_lower = text_to_check.lower()

        # First check if it's international news
        if self.international_pattern.search(text_lower):
            return False

        # Count matches in different categories
        category_matches = {
            category: bool(pattern.search(text_lower))
            for category, pattern in self.govt_patterns.items()
        }
        
        # Article must match:
        # 1. At least one political body/role/party AND
        # 2. At least one state/location OR govt department
        has_political = (category_matches['political_bodies'] or 
                        category_matches['political_roles'] or 
                        category_matches['indian_parties'])
                        
        has_context = (category_matches['states'] or 
                      category_matches['govt_departments'])
                      
        return has_political and has_context

    def extract_government_news(self, soup):
        """Extract and process Indian government news articles"""
        urls = self.fetch_sitemap_urls(limit=50)
        if not urls:
            self.logger.warning("No URLs fetched from sitemap")
            return []

        news_items = []
        for url in urls:
            try:
                article_soup = self.get_page_content(url)
                if not article_soup:
                    continue

                # Extract title and content for better classification
                title_elem = (
                    article_soup.find("meta", property="og:title") or
                    article_soup.find("h1", class_="article-title") or
                    article_soup.find("h1", class_="story-title")
                )
                
                if not title_elem:
                    continue
                    
                title = title_elem.get("content", "") if title_elem.name == "meta" else title_elem.text.strip()
                
                # Extract initial content for classification
                article_content = article_soup.find('div', class_='article-body')
                initial_content = ''
                if article_content:
                    paragraphs = article_content.find_all('p', limit=3)  # First 3 paragraphs
                    initial_content = ' '.join(p.get_text(strip=True) for p in paragraphs)
                
                if self._is_government_news(title, initial_content):
                    news_item = {
                        'title': title,
                        'url': url
                    }
                    
                    # Extract date
                    date_meta = article_soup.find("meta", property="article:published_time")
                    if date_meta:
                        news_item['published_date'] = date_meta.get("content")
                    
                    # Process the full article immediately
                    processed_item = self.process_news_item(news_item)
                    if processed_item:
                        news_items.append(processed_item)
                        self.logger.info(f"Processed Indian government news: {title}")
            
            except Exception as e:
                self.logger.error(f"Error processing URL {url}: {e}")
                continue
                
        return news_items

    def process_news_item(self, news_item):
        """Process a single news article to extract its content"""
        try:
            soup = self.get_page_content(news_item['url'])
            if not soup:
                return None

            # Extract article content
            article_content = soup.find('div', class_='article-body')
            if article_content:
                # Extract all paragraphs
                paragraphs = article_content.find_all('p')
                content = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                
                if content:
                    news_item['content'] = content
                    
                    # Extract additional metadata if available
                    author = soup.find('meta', property='article:author')
                    if author:
                        news_item['author'] = author.get('content')
                        
                    category = soup.find('meta', property='article:section')
                    if category:
                        news_item['category'] = category.get('content')
                    
                    return news_item

            return None
            
        except Exception as e:
            self.logger.error(f"Error processing article content: {e}")
            return None