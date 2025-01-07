import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import re

class PioneerScraper:
    def __init__(self):
        self.base_url = 'https://www.dailypioneer.com/'
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.sections = [
            'https://www.dailypioneer.com/',
            'https://www.dailypioneer.com/india',
            'https://www.dailypioneer.com/state',
            'https://www.dailypioneer.com/nation'
        ]

    def get_page_content(self, url=None):
        try:
            target_url = url if url else self.base_url
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
            
            self.logger.info(f"Attempting to fetch content from: {target_url}")
            response = requests.get(target_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.logger.info(f"Successfully fetched content from {target_url}")
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Debug print of all article titles found
                print("\nDebug: All articles found on page:")
                print("-" * 50)
                for article in soup.find_all(['article', 'div', 'li']):
                    title = article.find(['h1', 'h2', 'h3', 'h4', 'a'])
                    if title:
                        print(f"Title: {title.get_text(strip=True)}")
                        content = article.find('p')
                        if content:
                            print(f"Content: {content.get_text(strip=True)[:200]}...")
                        print("-" * 30)
                
                return soup
            else:
                self.logger.error(f"Failed to retrieve content. Status code: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching page content: {e}")
            return None

    def extract_government_news(self, soup):
        news_items = []
        government_keywords = [
            'government', 'minister', 'ministry', 'policy', 'parliament',
            'cabinet', 'BJP', 'Congress', 'election', 'PM Modi', 'bill',
            'governance', 'scheme', 'initiative', 'India', 'Modi', 
            'Prime Minister', 'MP', 'MLA', 'Chief Minister'
        ]
        
        try:
            # Debug print the main content structure
            print("\nDebug: Main content structure:")
            print("-" * 50)
            main_content = soup.find('div', class_='main-content')
            if main_content:
                print("Found main-content div")
                
                # Print all div classes found
                print("\nDebug: All div classes found:")
                for div in main_content.find_all('div', class_=True):
                    print(f"Class found: {div.get('class')}")
            
            # Look for news articles in different sections
            article_sections = [
                soup.find_all('div', class_='news-post'),
                soup.find_all('div', class_='top-news-section'),
                soup.find_all('div', class_='news-listing'),
                soup.find_all('div', class_='latest-news-section'),
                soup.find_all('article'),  # Added generic article tag
                soup.find_all('div', class_='news-item')  # Added generic news item class
            ]

            print("\nDebug: Processing articles:")
            print("-" * 50)
            
            for section in article_sections:
                for article in section:
                    try:
                        # Find title from heading or link
                        title_elem = article.find(['h1', 'h2', 'h3', 'h4']) or article.find('a')
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        
                        # Get content
                        content = ""
                        content_elem = article.find('p') or article.find('div', class_='content')
                        if content_elem:
                            content = content_elem.get_text(strip=True)
                        
                        print(f"\nFound article:")
                        print(f"Title: {title}")
                        print(f"Content preview: {content[:200]}...")

                        # Check if government related
                        if any(keyword.lower() in (content + title).lower() for keyword in government_keywords):
                            print("-> Government related: YES")
                            news_items.append({
                                "title": title,
                                "content": content,
                                "source": "Daily Pioneer"
                            })
                        else:
                            print("-> Government related: NO")

                    except Exception as e:
                        self.logger.error(f"Error processing article: {e}")
                        continue

            self.logger.info(f"Successfully extracted {len(news_items)} government-related articles")
            
        except Exception as e:
            self.logger.error(f"Error in extract_government_news: {e}")
        
        return news_items

    def process_news_item(self, item):
        try:
            if not item or not item.get('title'):
                return None
            
            # Clean the text content
            title = self.clean_text(item['title'])
            content = self.clean_text(item.get('content', ''))
            
            processed_item = {
                "title": title,
                "content": content,
                "published_date": datetime.now().strftime('%Y-%m-%d'),
                "source": "Daily Pioneer",
                "scraped_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "type": "news"
            }
            
            return processed_item
            
        except Exception as e:
            self.logger.error(f"Error processing news item: {e}")
            return None

    def clean_text(self, text):
        try:
            if not text:
                return ""
            text = ' '.join(text.split())
            text = re.sub(r'[^\w\s.,!?-]', '', text)
            text = re.sub(r'([.,!?])\1+', r'\1', text)
            text = ' '.join(text.split())
            return text.strip()
        except Exception as e:
            self.logger.error(f"Error cleaning text: {e}")
            return text

    def scrape_all_sections(self):
        all_news_items = []
        for section_url in self.sections:
            self.logger.info(f"Scraping section: {section_url}")
            soup = self.get_page_content(section_url)
            if soup:
                news_items = self.extract_government_news(soup)
                all_news_items.extend(news_items)
        return all_news_items

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test the scraper
    scraper = PioneerScraper()
    news_items = scraper.scrape_all_sections()
    
    print("\nFinal Results:")
    print("-" * 50)
    print(f"Total articles found: {len(news_items)}")
    for item in news_items:
        processed_item = scraper.process_news_item(item)
        if processed_item:
            print("\nProcessed Article:")
            print(f"Title: {processed_item['title']}")
            print(f"Content: {processed_item['content'][:200]}...")
            print("-" * 50)