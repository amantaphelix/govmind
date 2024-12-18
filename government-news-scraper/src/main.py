import logging
from scrapers.india_today_scraper import IndiaTodayScraper
from scrapers.hindu_scraper import HinduScraper
from scrapers.deccan_chronicle import DeccanChronicleScraper
from scrapers.toi_scrapper import TOIScraper
from scrapers.ndtv_scraper import NDTVScraper
from scrapers.hindustan_scraper import HindustanTimesScraper 
from scrapers.livemint_scraper import LiveMintScraper
from scrapers.zee_scraper import ZeeNewsScraper
from scrapers.deccan_chronicle import DeccanChronicleScraper
from scrapers.indianexpress import IndianExpressScraper
from utils.data_cleaner import DataCleaner
from database.db_manager import DatabaseManager
from config.settings import MONGODB_URI

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("scraper.log"),
            logging.StreamHandler()
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger("MainScraper")
    db_manager = DatabaseManager(uri=MONGODB_URI)
    cleaner = DataCleaner()

    scrapers = [
        #IndiaTodayScraper(),   #settayi
        #HinduScraper()
        TOIScraper()
        #DeccanChronicleScraper(),
        #NDTVScraper(),
        #HindustanTimesScraper() # Robots.txt disallows
        #ZeeNewsScraper(),
        #LiveMintScraper(),        # Robots.txt disallows
        #IndianExpressScraper(),     # setayiii   Sitemap-based scraper
        #DeccanChronicleScraper()  #settaayi
    ]

    for scraper in scrapers:
        try:
            if isinstance(scraper, IndianExpressScraper):
                # Special handling for sitemap-based scraper
                logger.info(f"Starting sitemap scraping with {scraper.__class__.__name__}")
                urls = scraper.fetch_sitemap_urls(limit=5)
                if not urls:
                    logger.warning("No URLs fetched from sitemap. Skipping scraper.")
                    continue

                news_items = scraper.extract_government_news(urls)
            else:
                # Standard scrapers
                soup = scraper.get_page_content(scraper.base_url)
                if not soup:
                    logger.error(f"Failed to fetch content from {scraper.base_url}")
                    continue

                news_items = scraper.extract_government_news(soup)

            for item in news_items:
                processed_item = scraper.process_news_item(item)
                if processed_item:
                    processed_item["cleaned_content"] = cleaner.clean_text(processed_item.get("content", ""))
                    if db_manager.save_article(processed_item):
                        logger.info(f"Article saved: {processed_item['title']}")
                    else:
                        logger.warning(f"Duplicate or error saving: {processed_item['title']}")

        except Exception as e:
            logger.error(f"Error scraping {scraper.__class__.__name__}: {e}")

if __name__ == "__main__":
    main()