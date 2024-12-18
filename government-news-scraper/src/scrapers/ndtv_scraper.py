from .base_scraper import BaseScraper
import re
from urllib.parse import urljoin
import logging
import traceback

class NDTVScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.ndtv.com/")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)  # Set to DEBUG for more detailed logs

    def extract_government_news(self, soup):
        """
        Extract government-related news articles from the soup object
        """
        news_items = []
        article_selectors = [
            ('div', 'story-box'),
            ('div', 'news-block'),
            ('article', 'article'),
            ('div', 'news-list'),
            ('div', 'story-list'),
        ]
        
        self.logger.debug(f"Starting to extract government news from NDTV")
        
        all_articles = []
        for tag, class_name in article_selectors:
            try:
                found_articles = soup.find_all(tag, class_=re.compile(class_name))
                all_articles.extend(found_articles)
                self.logger.debug(f"Found {len(found_articles)} articles with selector ({tag}, {class_name})")
            except Exception as e:
                self.logger.error(f"Error finding articles with selector ({tag}, {class_name}): {e}")
                self.logger.debug(traceback.format_exc())
        
        self.logger.info(f"Total articles found before filtering: {len(all_articles)}")
        
        for i, article in enumerate(all_articles, 1):
            try:
                # Try to find title in different header tags
                title_elem = None
                for tag in ['h1', 'h2', 'h3', 'h4', 'h5']:
                    title_elem = article.find(tag)
                    if title_elem:
                        break
                
                # Find link
                link_elem = article.find('a')
                
                if title_elem and link_elem:
                    title_text = title_elem.get_text(strip=True)
                    link_href = link_elem.get('href', '')
                    
                    # Ensure full URL
                    if link_href.startswith('/'):
                        link_href = urljoin(self.base_url, link_href)
                    
                    # Check if it's a government news item
                    is_gov_news = self._is_government_news(title_text)
                    
                    self.logger.debug(f"Article {i}: Title='{title_text}', Link='{link_href}', Is Gov News={is_gov_news}")
                    
                    if is_gov_news and link_href:
                        news_item = {
                            'title': title_text,
                            'url': link_href
                        }
                        news_items.append(news_item)
                        self.logger.info(f"Added government news item: {title_text}")
            except Exception as e:
                self.logger.error(f"Error processing article {i}: {e}")
                self.logger.debug(traceback.format_exc())
        
        self.logger.info(f"Total government news items extracted: {len(news_items)}")
        return news_items

    def process_news_item(self, news_item):
        """
        Process individual news item to extract full content
        """
        self.logger.debug(f"Processing news item: {news_item['title']}")
        
        try:
            soup = self.get_page_content(news_item['url'])
            if not soup:
                self.logger.error(f"Failed to get page content for URL: {news_item['url']}")
                return None
            
            article_body = None
            selectors = [
                ('div', 'wysihtml-content'),
                ('div', 'article-content'),
                ('div', 'story-body'),
                ('div', 'description'),
                ('article', 'content'),
            ]
            
            for tag, class_name in selectors:
                try:
                    article_body = soup.find(tag, class_=re.compile(class_name))
                    if article_body:
                        self.logger.debug(f"Found article body with selector: {tag}, {class_name}")
                        break
                except Exception as e:
                    self.logger.error(f"Error finding article body with selector ({tag}, {class_name}): {e}")
            
            if not article_body:
                self.logger.warning(f"No article body found for: {news_item['title']}")
                return None
            
            # Extract paragraphs, excluding specific classes if needed
            paragraphs = article_body.find_all(['p', 'div'], class_=lambda x: x != 'also-read')
            
            # Filter out empty paragraphs and extract text
            paragraph_texts = [
                p.get_text(strip=True) 
                for p in paragraphs 
                if p.get_text(strip=True)
            ]
            
            # Join paragraphs
            content = ' '.join(paragraph_texts)
            
            if not content:
                self.logger.warning(f"No content extracted for: {news_item['title']}")
                return None
            
            # Add content to news item
            news_item['content'] = content
            
            self.logger.info(f"Successfully processed news item: {news_item['title']}")
            self.logger.debug(f"Content length: {len(content)} characters")
            
            return news_item
        
        except Exception as e:
            self.logger.error(f"Critical error processing news item {news_item['title']}: {e}")
            self.logger.debug(traceback.format_exc())
            return None

    def _is_government_news(self, title):
        """
        Determine if the news is government-related
        """
        government_keywords = [
            'government', 'minister', 'policy', 'parliament', 'cabinet', 
            'legislation', 'bureaucracy', 'official', 'modi', 'ministry', 
            'supreme court', 'high court', 'bjp', 'congress', 'election', 
            'commission', 'bill', 'lok sabha', 'rajya sabha', 'governor', 
            'pm', 'chief minister', 'mla', 'mp', 'president', 'govt'
        ]
        
        title_lower = title.lower()
        match = any(keyword.lower() in title_lower for keyword in government_keywords)
        return match