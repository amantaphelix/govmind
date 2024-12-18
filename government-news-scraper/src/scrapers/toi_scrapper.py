from .base_scraper import BaseScraper
import re
from urllib.parse import urljoin
import logging

class TOIScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://timesofindia.indiatimes.com/india")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)

    def extract_government_news(self, soup):
        self.logger.debug("Starting news extraction")
        self.logger.debug(f"Page title: {soup.title.string if soup.title else 'No title found'}")
        
        news_items = []
        article_selectors = [
            ('div', 'list5'),
            ('div', '_3CC0m'),
            ('div', 'Bw78m'),
        ]

        all_articles = []
        for tag, class_name in article_selectors:
            found_articles = soup.find_all(tag, class_=re.compile(class_name))
            self.logger.debug(f"Selector {tag}.{class_name} found {len(found_articles)} articles")
            all_articles.extend(found_articles)

        self.logger.debug(f"Total articles found: {len(all_articles)}")

        for article in all_articles:
            title_text = None
            link_href = None
            self.logger.debug(f"Article HTML: {str(article)}")  # Log entire article HTML for debugging
            
            # Extracting title from different possible locations
            headline = article.find(['h3', 'span'], class_=re.compile('_3PGrR|headline'))
            if headline:
                title_text = headline.get_text(strip=True)
            
            if not title_text:
                link = article.find('a')
                if link:
                    title_text = link.get_text(strip=True)

            if not title_text:
                img_elem = article.find('img')
                if img_elem and img_elem.get('alt'):
                    title_text = img_elem.get('alt').strip()
            
            # Extract the link
            link_elem = article.find('a')
            if link_elem and link_elem.get('href'):
                link_href = link_elem.get('href')
                if link_href.startswith('/'):
                    link_href = urljoin(self.base_url, link_href)

            # Skip video content
            if link_href and '/videos/' in link_href:
                self.logger.debug(f"Skipping video content: {link_href}")
                continue

            if title_text and link_href:
                self.logger.debug(f"Found article - Title: {title_text}")
                self.logger.debug(f"URL: {link_href}")

                if not self.can_fetch(link_href):
                    self.logger.warning(f"URL not allowed by robots.txt: {link_href}")
                    continue

                self.logger.debug(f"Checking if article is government-related: {title_text}")

                if self._is_government_news(title_text):
                    news_item = {
                        'title': title_text,
                        'url': link_href
                    }
                    news_items.append(news_item)
                    self.logger.info(f"Added government news item: {news_item}")
                else:
                    self.logger.info(f"Non-government news item skipped: {title_text}")

        self.logger.info(f"Total government news items found: {len(news_items)}")
        return news_items

    def _is_government_news(self, title):
        """
        Determine if the news is government-related.
        """
        government_keywords = [
            'government', 'minister', 'policy', 'parliament', 
            'cabinet', 'legislation', 'bureaucracy', 'official',
            'modi', 'ministry', 'supreme court', 'high court',
            'bjp', 'congress', 'election', 'commission', 'bill',
            'lok sabha', 'rajya sabha', 'governor', 'pm',
            'chief minister', 'mla', 'mp', 'president', 'govt',
            'nirmala', 'assembly', 'budget', 'policy', 'court',
            'probe', 'ministerial'
        ]

        title_lower = title.lower()
        found_keywords = [kw for kw in government_keywords if kw in title_lower]
        matches = bool(found_keywords)

        if matches:
            self.logger.debug(f"Government news found - Title: {title}")
            self.logger.debug(f"Matching keywords: {found_keywords}")
        else:
            self.logger.debug(f"Non-government news - Title: {title}")

        return matches

    def __init__(self):
        super().__init__("https://timesofindia.indiatimes.com/india")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)

    def extract_government_news(self, soup):
        """
        Extract government-related news articles from Times of India.
        Skips video content.
        """
        self.logger.debug("Starting news extraction")
        self.logger.debug(f"Page title: {soup.title.string if soup.title else 'No title found'}")
        
        news_items = []
        article_selectors = [
            ('div', 'list5'),   # Regular article list
            ('div', '_3CC0m'),  # Article container
            ('div', 'Bw78m'),   # Article container alternative
        ]

        all_articles = []
        for tag, class_name in article_selectors:
            found_articles = soup.find_all(tag, class_=re.compile(class_name))
            self.logger.debug(f"Selector {tag}.{class_name} found {len(found_articles)} articles")
            all_articles.extend(found_articles)

        self.logger.debug(f"Total articles found: {len(all_articles)}")

        for article in all_articles:
            title_text = None
            link_href = None
            self.logger.debug(f"Article HTML: {str(article)}")  # Log entire article HTML for debugging
            
            # Try multiple ways to get the title
            # 1. From headline class
            headline = article.find(['h3', 'span'], class_=re.compile('_3PGrR|headline'))
            if headline:
                title_text = headline.get_text(strip=True)
            
            # 2. From link text
            if not title_text:
                link = article.find('a')
                if link:
                    title_text = link.get_text(strip=True)

            # 3. From img alt attribute as last resort
            if not title_text:
                img_elem = article.find('img')
                if img_elem and img_elem.get('alt'):
                    title_text = img_elem.get('alt').strip()
            
            # Find the link
            link_elem = article.find('a')
            if link_elem and link_elem.get('href'):
                link_href = link_elem.get('href')
                if link_href.startswith('/'):
                    link_href = urljoin(self.base_url, link_href)

            # Skip if it's a video
            if link_href and '/videos/' in link_href:
                self.logger.debug(f"Skipping video content: {link_href}")
                continue

            if title_text and link_href:
                self.logger.debug(f"Found article - Title: {title_text}")
                self.logger.debug(f"URL: {link_href}")

                if not self.can_fetch(link_href):
                    self.logger.warning(f"URL not allowed by robots.txt: {link_href}")
                    continue

                self.logger.debug(f"Checking if article is government-related: {title_text}")

                if self._is_government_news(title_text):
                    news_item = {
                        'title': title_text,
                        'url': link_href
                    }
                    news_items.append(news_item)
                    self.logger.info(f"Added government news item: {news_item}")
                else:
                    self.logger.info(f"Non-government news item skipped: {title_text}")

        self.logger.info(f"Total government news items found: {len(news_items)}")
        return news_items

    def process_news_item(self, news_item):
        """
        Process and extract full article details.
        """
        self.logger.debug(f"Starting to process article: {news_item}")
        
        try:
            # Skip video content
            if '/videos/' in news_item['url']:
                self.logger.debug(f"Skipping video content: {news_item['url']}")
                return None

            self._respect_rate_limits()
            soup = self.get_page_content(news_item['url'])
            
            if not soup:
                self.logger.error(f"Failed to get page content for: {news_item['url']}")
                return None

            # Article content selectors
            selectors = [
                ('div', '_3YYSt'),
                ('div', 'ga-article'),
                ('div', '_3WlLe'),
                ('div', 'article-body'),
                ('div', '_3WlLe clearfix'),
                ('div', 'Normal')  # Common content class in TOI
            ]

            for tag, class_name in selectors:
                article_body = soup.find(tag, class_=class_name)
                if article_body:
                    # Get all text elements, excluding unwanted sections
                    paragraphs = article_body.find_all(
                        ['p', 'div'],
                        class_=lambda x: x and not any(exclude in str(x) 
                            for exclude in ['also-read', 'related-news', 'ads'])
                    )
                    
                    content = ' '.join(p.get_text(strip=True) 
                                     for p in paragraphs 
                                     if p.get_text(strip=True))
                    
                    if content:
                        news_item['content'] = content
                        self.logger.info(f"Successfully processed article: {news_item['title']}")
                        return news_item

            self.logger.error(f"No article content found for: {news_item['url']}")
            return None

        except Exception as e:
            self.logger.error(f"Error processing article: {str(e)}", exc_info=True)
            return None

    def _is_government_news(self, title):
        """
        Determine if the news is government-related.
        """
        government_keywords = [
            'government', 'minister', 'policy', 'parliament', 
            'cabinet', 'legislation', 'bureaucracy', 'official',
            'modi', 'ministry', 'supreme court', 'high court',
            'bjp', 'congress', 'election', 'commission', 'bill',
            'lok sabha', 'rajya sabha', 'governor', 'pm',
            'chief minister', 'mla', 'mp', 'president', 'govt',
            'nirmala', 'assembly'
        ]

        title_lower = title.lower()
        found_keywords = [kw for kw in government_keywords if kw in title_lower]
        matches = bool(found_keywords)

        if matches:
            self.logger.debug(f"Government news found - Title: {title}")
            self.logger.debug(f"Matching keywords: {found_keywords}")
        else:
            self.logger.debug(f"Non-government news - Title: {title}")

        return matches
