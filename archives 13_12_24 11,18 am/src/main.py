import logging
from datetime import datetime
import json
import os

from scrapers.india_today_scraper import IndiaTodayScraper
from utils.data_cleaner import DataCleaner
from database.db_manager import DatabaseManager

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scraper.log'),
            logging.StreamHandler()
        ]
    )

def save_news_data(news_items, source):
    """Save scraped news data to file"""
    # Create data directory if not exists
    os.makedirs('data/raw', exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'data/raw/{source}_{timestamp}.json'
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(news_items, f, ensure_ascii=False, indent=4)
    
    return filename

def main():
    setup_logging()
    logger = logging.getLogger('MainScraper')
    
    # Initialize scrapers and cleaner
    scrapers = [
        IndiaTodayScraper(),
        # Add other scrapers here
    ]
    cleaner = DataCleaner()
    
    all_news = []
    
    for scraper in scrapers:
        try:
            # Fetch news page
            soup = scraper.get_page_content(scraper.base_url)
            
            if not soup:
                logger.error(f"Failed to fetch content from {scraper.base_url}")
                continue
            
            # Extract government news
            news_items = scraper.extract_government_news(soup)
            
            # Process each news item
            processed_items = []
            for item in news_items:
                processed_item = scraper.process_news_item(item)
                if processed_item:
                    processed_items.append(processed_item)
            
            # Clean data
            unique_items = cleaner.remove_duplicates(processed_items)
            
            # Clean text in each item
            for item in unique_items:
                if 'content' in item:
                    item['cleaned_content'] = cleaner.clean_text(item['content'])
            
            # Save source-specific news
            save_filename = save_news_data(unique_items, 
                                           scraper.__class__.__name__.replace('Scraper', '').lower())
            
            logger.info(f"Saved {len(unique_items)} news items from {scraper.__class__.__name__}")
            
            all_news.extend(unique_items)
        
        except Exception as e:
            logger.error(f"Error scraping {scraper.__class__.__name__}: {e}")
    
    # Optional: Save combined news data
    if all_news:
        save_news_data(all_news, 'combined')

if __name__ == "__main__":
    main()