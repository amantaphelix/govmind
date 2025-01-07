from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
from .base_scraper import BaseScraper

class HindustanTimesScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.hindustantimes.com/")
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_government_news(self, soup=None):
        """
        Extract government-related news articles using Selenium and BeautifulSoup.

        Returns:
            list: List of government news items with title and URL.
        """
        news_items = []

        # Selenium setup
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--log-level=3')  # Suppresses unwanted browser logs
        driver = webdriver.Chrome(options=options)

        try:
            self.logger.info(f"Fetching URL: {self.base_url}")
            driver.get(self.base_url)

            # Wait for key elements to load
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'cartHolder')))

            # Extract page content
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Article selectors
            sections = [
                ('div', 'cartHolder bigCart track timeAgo'),
                ('div', 'cartHolder listView track timeAgo')
            ]

            for tag, class_name in sections:
                articles = soup.find_all(tag, class_=class_name)
                self.logger.info(f"Found {len(articles)} articles in section {class_name}")

                for article in articles:
                    title_elem = article.find('h3', class_='hdg3')
                    link_elem = title_elem.find('a') if title_elem else None

                    if title_elem and link_elem:
                        title_text = title_elem.get_text(strip=True)
                        link_href = link_elem['href']

                        # Ensure full URL
                        if link_href.startswith('/'):
                            link_href = urljoin(self.base_url, link_href)

                        # Check if it's government-related news
                        if self._is_government_news(title_text):
                            news_items.append({
                                'title': title_text,
                                'url': link_href
                            })
                            self.logger.info(f"Added government news: Title: {title_text}, Link: {link_href}")
                        else:
                            self.logger.debug(f"Skipped non-government news: Title: {title_text}")
                    else:
                        self.logger.warning(f"Missing title or link in article: {article}")

        except Exception as e:
            self.logger.error(f"Error during extraction: {e}", exc_info=True)

        finally:
            driver.quit()

        self.logger.info(f"Total government-related news items: {len(news_items)}")
        return news_items

    def process_news_item(self, news_item):
        """
        Process the news item by fetching its content.

        Args:
            news_item (dict): A dictionary containing the title and URL of a news item.

        Returns:
            dict: A dictionary containing the full content of the article or None if extraction fails.
        """
        self.logger.info(f"Processing article: {news_item['title']}")

        # Fetch the article page content
        soup = self.get_page_content(news_item['url'])
        if not soup:
            self.logger.warning(f"Could not fetch content for: {news_item['url']}")
            return None

        # Extract the article body
        article_body = soup.find('div', class_='article-body')  # Adjust the class name as needed
        if article_body:
            paragraphs = article_body.find_all(['p', 'div', 'span'])
            content = " ".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            news_item['content'] = content
            return news_item

        self.logger.warning(f"Could not find article body for: {news_item['url']}")
        return None

    def _is_government_news(self, title):
        """
        Check if the article title contains government-related keywords.

        Args:
            title (str): Title of the news article.

        Returns:
            bool: True if the title contains government-related keywords, False otherwise.
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
        match = any(keyword in title_lower for keyword in government_keywords)
        self.logger.debug(f"Checking title: {title}, Government-related match found: {match}")
        return match
