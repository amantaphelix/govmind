from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import time
import random
import logging

class TOIScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://timesofindia.indiatimes.com/india")
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)

    def get_page_content(self, url):
        """
        Fetch the page content for a given URL using requests.
        """
        try:
            time.sleep(random.uniform(1, 3))  # Respect rate limits
            self.logger.info(f"Fetching content from: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching page content from {url}: {e}")
            return None

    def extract_government_news(self, soup, max_articles=10):
        """
        Extract government-related news articles from the TOI India page with a limit on the number of articles.
        
        :param soup: BeautifulSoup object of the page.
        :param max_articles: Maximum number of articles to scrape (default is 10).
        :return: List of extracted government news articles.
        """
        self.logger.debug("Starting extraction of government news articles")
        news_items = []
        article_selectors = [
            ('div', 'list5'),  # Primary news container
            ('li', 'top-story'),  # Secondary container
            ('div', 'iN5CR'),  # Additional container for TOI articles
        ]

        all_articles = []
        for tag, class_name in article_selectors:
            found_articles = soup.find_all(tag, class_=class_name)
            self.logger.debug(f"Selector {tag}.{class_name} found {len(found_articles)} articles")
            all_articles.extend(found_articles)

        self.logger.debug(f"Total articles found: {len(all_articles)}")

        for idx, article in enumerate(all_articles):
            if len(news_items) >= max_articles:
                self.logger.info(f"Reached the maximum limit of {max_articles} articles. Stopping extraction.")
                break

            try:
                # Extract the title
                title_elem = article.find('a')
                title_text = title_elem.get_text(strip=True) if title_elem else None

                # Extract the URL
                link_href = title_elem.get('href') if title_elem else None
                if link_href and link_href.startswith('/'):
                    link_href = f"https://timesofindia.indiatimes.com{link_href}"

                # Skip invalid articles
                if not title_text or not link_href:
                    continue

                # Check if the article is government-related
                if self._is_government_news(title_text):
                    news_items.append({
                        'title': title_text,
                        'url': link_href
                    })
                    self.logger.info(f"Added government news item: {title_text}")
                else:
                    self.logger.debug(f"Skipping non-government article: {title_text}")

            except Exception as e:
                self.logger.error(f"Error processing article: {e}", exc_info=True)

        self.logger.info(f"Total government news items found: {len(news_items)}")
        return news_items


    def process_news_item(self, news_item):
        """
        Process a single news item by fetching and extracting its content.
        """
        self.logger.debug(f"Processing news item: {news_item['title']}")
        try:
            soup = self.get_page_content(news_item['url'])
            if not soup:
                self.logger.error(f"Failed to fetch content for: {news_item['url']}")
                return None

            # Extract content
            content = self.extract_content(soup)
            if not content:
                self.logger.warning(f"No content extracted for: {news_item['title']}")
                return None

            # Add content and metadata
            processed_item = {
                'title': news_item['title'],
                'url': news_item['url'],
                'content': content,
                'source': self.__class__.__name__,
                'timestamp': datetime.now().isoformat()
            }

            self.logger.info(f"Successfully processed article: {news_item['title']}")
            return processed_item

        except Exception as e:
            self.logger.error(f"Error processing news item {news_item['title']}: {e}", exc_info=True)
            return None

    def extract_content(self, soup):
        """Extract the content from the article page."""
        try:
            # Possible classes where content might reside
            potential_classes = ['M1rHh vkpDP', '_s30J clearfix', '_3YYSt clearfix']

            content = None
            for cls in potential_classes:
                content_div = soup.find('div', class_=cls)
                if content_div:
                    content = content_div.get_text(strip=True)
                    break  # Stop once content is found

            if content:
                self.logger.info("Successfully extracted content")
                return content

            self.logger.warning("No content found in the article")
            return None

        except Exception as e:
            self.logger.error(f"Error extracting content: {e}")
            return None

        except Exception as e:
            self.logger.error(f"Error extracting content: {e}", exc_info=True)
            return None


    def _is_government_news(self, title):
        """
        Determine if the news is government-related.
        """
        keywords = [
            'government', 'minister', 'policy', 'parliament',
            'cabinet', 'legislation', 'bureaucracy', 'official',
            'modi', 'ministry', 'supreme court', 'high court',
            'bjp', 'congress', 'election', 'commission', 'bill',
            'lok sabha', 'rajya sabha', 'governor', 'pm',
            'chief minister', 'mla', 'mp', 'president', 'govt'
        ]
        title_lower = title.lower()
        return any(keyword in title_lower for keyword in keywords)
