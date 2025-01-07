from .base_scraper import BaseScraper
from lxml import html
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
import logging
import traceback

class NDTVScraper(BaseScraper):
    def __init__(self):
        super().__init__(base_url="https://www.ndtv.com/")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.driver = self._setup_selenium_driver()

    def _setup_selenium_driver(self):
        """
        Setup Selenium WebDriver for dynamic content rendering.
        """
        options = Options()
        options.add_argument('--headless')  # Run without GUI
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--log-level=3')
        return webdriver.Chrome(options=options)

    def extract_government_news(self):
        """
        Extract government-related news articles using Selenium and XPath.
        """
        news_items = []
        try:
            self.logger.info(f"Fetching {self.base_url}")
            self.driver.get(self.base_url)
            html_content = self.driver.page_source

            # Parse the rendered HTML with lxml
            tree = html.fromstring(html_content)

            # Updated XPath for locating article containers
            article_xpath = "//div[contains(@class,'sp-cn')]"
            articles = tree.xpath(article_xpath)
            self.logger.debug(f"Found {len(articles)} article containers")

            for i, article in enumerate(articles, 1):
                try:
                    # Extract title and link
                    title_xpath = ".//h1[@class='sp-ttl']/text()"
                    link_xpath = ".//h1[@class='sp-ttl']/ancestor::a/@href"

                    title = article.xpath(title_xpath)
                    link = article.xpath(link_xpath)

                    if not title or not link:
                        self.logger.debug(f"Skipping article {i} due to missing title or link")
                        continue

                    title_text = title[0].strip()
                    link_href = urljoin(self.base_url, link[0].strip())

                    # Check if it's a government news item
                    is_gov_news = self._is_government_news(title_text)

                    self.logger.debug(f"Article {i}: Title='{title_text}', Link='{link_href}', Is Gov News={is_gov_news}")

                    if is_gov_news:
                        news_items.append({
                            'title': title_text,
                            'url': link_href
                        })
                        self.logger.info(f"Added government news item: {title_text}")
                except Exception as e:
                    self.logger.error(f"Error processing article {i}: {e}")
                    self.logger.debug(traceback.format_exc())

        except Exception as e:
            self.logger.error(f"Error during extraction: {e}")
            self.logger.debug(traceback.format_exc())

        finally:
            self.driver.quit()

        self.logger.info(f"Total government news items extracted: {len(news_items)}")
        return news_items

    def process_news_item(self, news_item):
        """
        Process individual news item to extract full content.
        """
        self.logger.debug(f"Processing news item: {news_item['title']}")

        try:
            self.driver.get(news_item['url'])
            html_content = self.driver.page_source

            # Parse the rendered HTML with lxml
            tree = html.fromstring(html_content)

            # XPath for article body
            body_xpath = "//div[contains(@class,'sp_txt')]"
            article_body = tree.xpath(body_xpath)

            if not article_body:
                self.logger.warning(f"No article body found for: {news_item['title']}")
                return None

            # Extract paragraphs
            paragraphs = article_body[0].xpath(".//p/text() | .//div[@class='para']/text()")
            content = ' '.join(p.strip() for p in paragraphs if p.strip())

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
        Determine if the news is government-related.
        """
        government_keywords = [
            'government', 'minister', 'policy', 'parliament', 'cabinet',
            'legislation', 'bureaucracy', 'official', 'modi', 'ministry',
            'supreme court', 'high court', 'bjp', 'congress', 'election',
            'commission', 'bill', 'lok sabha', 'rajya sabha', 'governor',
            'pm', 'chief minister', 'mla', 'mp', 'president', 'govt'
        ]

        title_lower = title.lower()
        return any(keyword in title_lower for keyword in government_keywords)
