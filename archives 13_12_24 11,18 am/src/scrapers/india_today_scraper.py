from .base_scraper import BaseScraper
import re
from urllib.parse import urljoin
import logging

class IndiaTodayScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.indiatoday.in/")
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_government_news(self, soup):
        """
        Extract government-related news from India Today
        """
        news_items = []
        
        # Debug: Print the full HTML to see what we're working with
        print("Debugging HTML structure:")
        print(soup.prettify()[:1000])  # Print first 1000 chars for inspection
        
        # Try multiple selectors for articles
        article_selectors = [
            ('div', 'story'),
            ('div', 'story-list'),
            ('div', 'B_homepage_article'),
            ('div', 'view-content'),
            ('div', 'widget-content'),
            # Add specific class names you see in the HTML
        ]
        
        all_articles = []
        for tag, class_name in article_selectors:
            found_articles = soup.find_all(tag, class_=re.compile(class_name))
            print(f"Found {len(found_articles)} articles with selector {tag}.{class_name}")
            all_articles.extend(found_articles)
        
        print(f"Total articles found: {len(all_articles)}")
        
        for article in all_articles:
            # Debug: Print article HTML
            print("\nArticle HTML:")
            print(article.prettify()[:500])  # Print first 500 chars
            
            # Try multiple selectors for title
            title_elem = None
            for tag in ['h1', 'h2', 'h3', 'h4']:
                title_elem = article.find(tag)
                if title_elem:
                    break
            
            # Try multiple selectors for link
            link_elem = article.find('a')
            
            if title_elem and link_elem:
                title_text = title_elem.get_text(strip=True)
                link_href = link_elem.get('href', '')
                
                print(f"\nFound article:")
                print(f"Title: {title_text}")
                print(f"Link: {link_href}")
                
                # Ensure full URL
                if link_href.startswith('/'):
                    link_href = urljoin(self.base_url, link_href)
                
                if self._is_government_news(title_text):
                    news_items.append({
                        'title': title_text,
                        'link': link_href
                    })
                    print(f"Added as government news: {title_text}")
        
        print(f"\nFound {len(news_items)} potential government news items")
        return news_items

    def process_news_item(self, news_item):
        """
        Process and extract full article details
        """
        print(f"\nProcessing article: {news_item['title']}")
        soup = self.get_page_content(news_item['link'])
        
        if not soup:
            print(f"Could not fetch content for: {news_item['link']}")
            return None
        
        # Try multiple possible selectors for article content
        article_body = None
        selectors = [
            ('div', 'description'),
            ('div', 'story-right'),
            ('div', 'content-area'),
            ('div', 'story-details'),
            ('div', 'article-body'),
        ]
        
        for tag, class_name in selectors:
            print(f"Trying selector: {tag}.{class_name}")
            article_body = soup.find(tag, class_=class_name)
            if article_body:
                print(f"Found content with selector: {tag}.{class_name}")
                break
        
        if article_body:
            # Clean the content
            paragraphs = article_body.find_all(['p', 'div'], class_=lambda x: x != 'also-read')
            content = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            
            if content:
                news_item['content'] = content
                print(f"Successfully extracted content ({len(content)} chars)")
                return news_item
            
        print(f"Could not find article body for: {news_item['link']}")
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
        print(f"Title: {title}")
        print(f"Is government news: {match}")
        return match