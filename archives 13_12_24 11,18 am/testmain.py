# src/main.py

import logging
from datetime import datetime, timezone
from database.db_manager import DatabaseManager

# Sample article to save
sample_article = {
    'title': 'Government announces new budget for 2025',
    'url': 'https://www.example.com/government-budget-2025',
    'source': 'IndiaToday',
    'published_date': datetime.now(timezone.utc),
    'content': 'The government has announced a new budget to foster economic growth...',
}

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

def main():
    # Setup logging
    setup_logging()
    logger = logging.getLogger('Main')

    # Initialize DatabaseManager with your MongoDB URI
    db_manager = DatabaseManager(uri="mongodb+srv://amantaphelix:amantaphelix@cluster0.mmmiw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

    # Save the sample article to the database
    if db_manager.save_article(sample_article):
        logger.info(f"Article '{sample_article['title']}' saved successfully to the database.")
    else:
        logger.error("Failed to save the article.")

    # Optionally, retrieve and display the saved article
    saved_article = db_manager.get_articles(source="IndiaToday", limit=1)
    if saved_article:
        logger.info(f"Saved article: {saved_article[0]}")
    else:
        logger.error("No articles found.")

    # Close the database connection
    db_manager.close()

if __name__ == "__main__":
    main()
