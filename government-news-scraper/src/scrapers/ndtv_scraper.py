from datetime import datetime
import json
from bs4 import BeautifulSoup
import requests
from .base_scraper import BaseScraper

class NDTVScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            base_url="https://www.ndtv.com/india",
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )

    def fetch_sitemap_urls(self, limit=None):
        """Compatibility method for main script's sitemap handling."""
        urls = self.fetch_article_urls(limit)
        self.logger.info(f"Fetched {len(urls)} URLs for processing")
        for url in urls:
            self.logger.info(f"Found URL: {url}")
        return urls

    def fetch_article_urls(self, limit=None):
        """Fetch article URLs directly from the India news section."""
        try:
            self.logger.info(f"Fetching articles from {self.base_url}")
            
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            article_links = []
            
            # Method 1: Try the original lisingNews class
            news_list = soup.find('div', {'class': 'lisingNews'})
            
            # Method 2: Try finding all article links with specific patterns
            if not news_list:
                article_links = [
                    a['href'] for a in soup.find_all('a', href=True)
                    if '/india-news/' in a['href'] 
                    or '/india/' in a['href']
                ]
            else:
                links = news_list.find_all('a', href=True)
                article_links = [
                    link['href'] for link in links 
                    if '/india-news/' in link['href'] or '/india/' in link['href']
                ]

            # Method 3: Try finding articles by common NDTV article classes
            if not article_links:
                article_containers = soup.find_all(['div', 'article'], class_=['new_storylising', 'article_list', 'story_lists'])
                for container in article_containers:
                    links = container.find_all('a', href=True)
                    article_links.extend([
                        link['href'] for link in links 
                        if '/india-news/' in link['href'] or '/india/' in link['href']
                    ])

            # Ensure all links are absolute URLs
            article_links = [
                link if link.startswith('http') else f"https://www.ndtv.com{link}"
                for link in article_links
            ]

            # Remove duplicates while preserving order
            article_links = list(dict.fromkeys(article_links))

            if limit:
                article_links = article_links[:limit]

            self.logger.info(f"Found {len(article_links)} article links")
            if article_links:
                for url in article_links[:3]:
                    self.logger.info(f"Sample URL: {url}")

            return article_links

        except Exception as e:
            self.logger.error(f"Error fetching article links: {e}")
            return []

    def extract_government_news(self, urls=None):
        """Extract government news from the India news section."""
        if urls is None or not urls:
            self.logger.info("No URLs provided, fetching latest 10 articles")
            urls = self.fetch_article_urls(limit=10)
        
        if not urls:
            self.logger.warning("No URLs to process")
            return []
            
        news_items = []
        self.logger.info(f"Starting to process {len(urls)} URLs for government news")
        
        for idx, url in enumerate(urls, 1):
            self.logger.info(f"Processing URL {idx}/{len(urls)}: {url}")
            
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract and log each field separately
                title = self._extract_title(soup)
                self.logger.info(f"Title extracted: {title}")
                
                if not title:
                    self.logger.warning(f"No title found for {url}")
                    continue
                    
                if not self._is_government_news(title):
                    self.logger.info(f"Not government news: {title}")
                    continue

                self.logger.info(f"Found government news: {title}")
                
                content = self._extract_content(soup)
                self.logger.info(f"Content extracted: {'Yes' if content else 'No'} - Length: {len(content) if content else 0}")
                
                timestamp = self._extract_timestamp(soup)
                self.logger.info(f"Timestamp extracted: {timestamp}")

                # Create news item and check each field
                news_item = {
                    'url': url,
                    'title': title,
                    'content': content,
                    'timestamp': timestamp,
                    'source': 'NDTV'
                }

                # Log any missing fields
                missing_fields = [field for field, value in news_item.items() if not value]
                if missing_fields:
                    self.logger.warning(f"Missing fields: {', '.join(missing_fields)}")
                else:
                    news_items.append(news_item)
                    self.logger.info(f"Successfully extracted article: {title}")

            except Exception as e:
                self.logger.error(f"Error processing URL {url}: {e}")
                continue

        self.logger.info(f"Completed processing. Found {len(news_items)} government news articles")
        return news_items

    def process_news_item(self, news_item):
        """Process a single news item."""
        if not news_item:
            return None

        return {
            'title': news_item['title'],
            'content': news_item['content'],
            'url': news_item['url'],
            'source': news_item['source'],
            'timestamp': news_item['timestamp'],
            'extracted_at': datetime.now().isoformat()
        }

    def _extract_title(self, soup):
        """Extract the title from the article page."""
        try:
            title_selectors = [
                ('h1', {'class': 'sp-ttl', 'itemprop': 'headline'}),
                ('h1', {'class': 'article__headline'}),
                ('h1', {'class': 'heading-txt'}),
                ('h1', {'class': 'entry-title'}),
                ('meta', {'property': 'og:title'}),
                ('meta', {'name': 'twitter:title'})
            ]
            
            for selector in title_selectors:
                title_tag = soup.find(selector[0], selector[1])
                if title_tag:
                    if title_tag.name == 'meta':
                        return title_tag.get('content', '').strip()
                    return title_tag.get_text(strip=True)
                    
            # Fallback: Try finding any h1
            h1 = soup.find('h1')
            if h1:
                return h1.get_text(strip=True)
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting title: {e}")
            return None

    def _extract_content(self, soup):
        """Enhanced content extraction with additional selectors and better error handling."""
        try:
            content_selectors = [
                ('div', {'class': 'sp-cn ins_storybody'}),
                ('div', {'class': 'story__content'}),
                ('div', {'class': 'Art-exp_wr', 'id': 'ignorediv'}),
                ('div', {'class': 'content_text'}),
                ('div', {'class': 'story-detail'}),
                ('article', {'class': 'story_body'}),
                ('div', {'itemprop': 'articleBody'}),
                ('div', {'class': 'article__content'})
            ]
            
            for selector in content_selectors:
                content_div = soup.find(selector[0], selector[1])
                if content_div:
                    # Remove unwanted elements
                    for unwanted in content_div.find_all(['script', 'style', 'div', 'figure']):
                        unwanted.decompose()
                    
                    # Try different methods to extract text
                    # Method 1: Get all paragraphs
                    paragraphs = [p.get_text(strip=True) for p in content_div.find_all('p')]
                    if paragraphs:
                        return ' '.join(p for p in paragraphs if p)
                    
                    # Method 2: Get direct text content
                    text = content_div.get_text(strip=True)
                    if text:
                        return text
            
            # Fallback: Try meta description
            meta_desc = soup.find('meta', {'property': 'og:description'}) or \
                       soup.find('meta', {'name': 'description'})
            if meta_desc:
                return meta_desc.get('content', '')

            self.logger.warning("No content found using any selector")
            return None

        except Exception as e:
            self.logger.error(f"Error extracting content: {e}")
            return None

    def _extract_timestamp(self, soup):
        """Enhanced timestamp extraction with additional selectors."""
        try:
            time_selectors = [
                ('time', {'itemprop': 'dateModified'}),
                ('span', {'class': 'sp-date'}),
                ('meta', {'itemprop': 'datePublished'}),
                ('span', {'class': 'posted-on'}),
                ('div', {'class': 'date_time'}),
                ('meta', {'property': 'article:published_time'}),
                ('script', {'type': 'application/ld+json'}),
                ('time', {}),
                ('meta', {'property': 'article:modified_time'})
            ]
            
            for selector in time_selectors:
                time_tag = soup.find(selector[0], selector[1])
                if time_tag:
                    if selector[0] == 'script':
                        # Parse JSON-LD for datePublished
                        try:
                            data = json.loads(time_tag.string)
                            if isinstance(data, dict):
                                return data.get('datePublished') or data.get('dateModified')
                        except:
                            continue
                    
                    if time_tag.get('datetime'):
                        return time_tag['datetime']
                    if time_tag.get('content'):
                        return time_tag['content']
                    return time_tag.get_text(strip=True)
            
            # Fallback: Look for any element with date-related attributes
            date_attrs = ['datetime', 'datePublished', 'dateModified']
            for attr in date_attrs:
                element = soup.find(attrs={attr: True})
                if element:
                    return element[attr]
                    
            self.logger.warning("No timestamp found using any method")
            return None

        except Exception as e:
            self.logger.error(f"Error extracting timestamp: {e}")
            return None

    def _is_government_news(self, title):
        """Check if the title indicates government-related news."""
        keywords = [
            'government', 'minister', 'policy', 'parliament',
            'cabinet', 'legislation', 'bureaucracy', 'official',
            'modi', 'ministry', 'supreme court', 'high court',
            'bjp', 'congress', 'election', 'commission', 'bill',
            'lok sabha', 'rajya sabha', 'governor', 'pm',
            'chief minister', 'mla', 'mp', 'president', 'govt'
        ]
        return any(keyword.lower() in title.lower() for keyword in keywords)