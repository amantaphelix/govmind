from .base_scraper import BaseScraper
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
import time

class MathrubhumiScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://english.mathrubhumi.com/")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.news_sections = [
            "https://english.mathrubhumi.com/news/kerala",
            "https://english.mathrubhumi.com/news/india"
        ]

    def extract_government_news(self, soup=None):
        """
        Extract government-related news from the page.
        Updated with new selectors and additional error handling.
        """
        news_items = []
        
        for section_url in self.news_sections:
            try:
                # Add a small delay between requests to avoid overwhelming the server
                time.sleep(2)
                
                section_soup = self.get_page_content(section_url)
                if not section_soup:
                    self.logger.error(f"Failed to get content from {section_url}")
                    continue
                
                # Updated selectors based on current website structure
                news_cards = []
                selectors = [
                    ('article', 'article-list'),  # New primary selector
                    ('div', 'article-box'),       # Alternate selector
                    ('div', 'list-article'),      # Backup selector
                    ('div', 'top-news'),          # For featured news
                    ('div', 'latest-news')        # For latest news section
                ]

                for tag, class_name in selectors:
                    cards = section_soup.find_all(tag, class_=class_name)
                    if cards:
                        news_cards.extend(cards)
                        self.logger.debug(f"Found {len(cards)} cards with selector {tag}.{class_name}")
                
                # If still no cards found, try finding all article tags
                if not news_cards:
                    news_cards = section_soup.find_all('article')
                    self.logger.debug(f"Fallback: Found {len(news_cards)} article tags")
                
                self.logger.info(f"Found {len(news_cards)} news containers in {section_url}")
                
                for card in news_cards:
                    try:
                        # Updated link and title selectors
                        link = card.find('a', href=True) or card.find('h2').find('a', href=True)
                        if not link:
                            continue

                        # Updated title selectors
                        title = None
                        title_selectors = [
                            ('h1', None),
                            ('h2', None),
                            ('h3', None),
                            ('div', 'article-title'),
                            ('span', 'title')
                        ]

                        for tag, class_name in title_selectors:
                            title_elem = card.find(tag, class_=class_name)
                            if title_elem:
                                title = title_elem
                                break

                        if not title:
                            continue
                            
                        title_text = title.text.strip()
                        
                        if not self._is_government_news(title_text):
                            continue
                            
                        url = link.get('href')
                        if not url:
                            continue
                            
                        full_url = urljoin(self.base_url, url)
                        
                        if any(item['url'] == full_url for item in news_items):
                            continue

                        news_items.append({
                            'title': title_text,
                            'url': full_url
                        })
                        self.logger.info(f"Found government news: {title_text}")
                        
                    except Exception as e:
                        self.logger.error(f"Error processing news card: {str(e)}")
                        continue
                        
            except Exception as e:
                self.logger.error(f"Error processing section {section_url}: {str(e)}")
                continue

        self.logger.info(f"Total government news items found: {len(news_items)}")
        return news_items[:5]

    def process_news_item(self, news_item):
        """Process a single news item by fetching its content."""
        try:
            self.logger.info(f"Processing news item: {news_item['title']}")
            
            soup = self.get_page_content(news_item['url'])
            if not soup:
                return None

            content = self._extract_content(soup)
            if not content:
                return None

            processed_item = {
                'title': news_item['title'],
                'url': news_item['url'],
                'content': content,
                'author': self._get_author(soup),
                'published_date': self._get_date(soup),
                'source': 'Mathrubhumi News',
                'scraped_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Successfully processed: {news_item['title']}")
            return processed_item

        except Exception as e:
            self.logger.error(f"Error processing news item {news_item['title']}: {e}")
            return None

    def _extract_content(self, soup):
        """Extract the content from the article page."""
        try:
            content_parts = []
            
            # Try multiple content selectors
            content_selectors = [
                ('div', 'mpp-story-content-details-main'),
                ('div', 'mpp-story-content'),
                ('div', 'mpp-article-content'),
                ('article', 'mpp-story')
            ]
            
            for tag, class_name in content_selectors:
                content_divs = soup.find_all(tag, class_=class_name)
                if content_divs:
                    for div in content_divs:
                        paragraphs = div.find_all('p')
                        for p in paragraphs:
                            text = p.text.strip()
                            if text and not text.startswith('Also Read'):
                                content_parts.append(text)
                    break
                    
            if content_parts:
                return ' '.join(content_parts)
                
            self.logger.warning("No content found in the article")
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting content: {e}")
            return None

    def _get_author(self, soup):
        """Extract the author information."""
        try:
            author_selectors = [
                ('div', 'mpp-story-author'),
                ('span', 'mpp-author'),
                ('div', 'mpp-author-name')
            ]
            
            for tag, class_name in author_selectors:
                author_elem = soup.find(tag, class_=class_name)
                if author_elem:
                    return author_elem.text.strip()
            
            return "Staff Reporter"
        except Exception:
            return "Staff Reporter"

    def _get_date(self, soup):
        """Extract the publication date."""
        try:
            date_selectors = [
                ('div', 'mpp-story-date'),
                ('span', 'mpp-date'),
                ('time', 'mpp-timeago'),
                ('div', 'mpp-publish-date')
            ]
            
            for tag, class_name in date_selectors:
                date_elem = soup.find(tag, class_=class_name)
                if date_elem:
                    return date_elem.text.strip()
            return None
        except Exception:
            return None

    def _is_government_news(self, title):
        """Check if the title indicates government-related news."""
        keywords = [
            'parliament', 'congress', 'bjp', 'government', 'minister',
            'policy', 'election', 'scheme', 'parliament', 'modi',
            'ministry', 'cabinet', 'lok sabha', 'rajya sabha',
            'supreme court', 'high court', 'central', 'state govt',
            'PM ', 'PMO', 'chief minister', 'CM ', 'govt', 'MLA',
            'MP ', 'UDF', 'LDF', 'assembly', 'pinarayi', 'governor',
            'legislative', 'secretariat', 'ruling', 'opposition'  # Added more Kerala-specific keywords
        ]
        return any(keyword.lower() in title.lower() for keyword in keywords)