# database/db_manager.py
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import logging
from typing import Dict, List, Optional
import hashlib

class DatabaseManager:
    def __init__(self, uri: str):
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        self.db = self.client['news_database']
        self.articles = self.db['articles']
        self.setup_indexes()
        self.logger = logging.getLogger(__name__)
        
    def setup_indexes(self):
        """Create necessary indexes for efficient querying"""
        try:
            self.articles.create_index([("article_id", 1)], unique=True)
            self.articles.create_index([("source", 1)])
            self.articles.create_index([("published_date", -1)])
            self.articles.create_index([("title", "text")])
            self.logger.info("Database indexes created successfully")
        except Exception as e:
            self.logger.error(f"Error creating indexes: {str(e)}")

    def generate_article_id(self, url: str, title: str) -> str:
        """Generate a unique ID for an article"""
        content = f"{url}{title}".encode('utf-8')
        return hashlib.sha256(content).hexdigest()

    def save_article(self, article_data: Dict) -> bool:
        """Save or update an article in the database"""
        try:
            article_id = self.generate_article_id(
                article_data['url'], 
                article_data['title']
            )
            article_data['article_id'] = article_id
            article_data['last_updated'] = datetime.utcnow()

            self.articles.update_one(
                {'article_id': article_id},
                {'$set': article_data},
                upsert=True
            )
            return True
        except Exception as e:
            self.logger.error(f"Error saving article: {str(e)}")
            return False

    def get_articles(self, 
                    source: Optional[str] = None,
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    limit: int = 100) -> List[Dict]:
        """Retrieve articles with optional filtering"""
        query = {}
        if source:
            query['source'] = source
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query['$gte'] = start_date
            if end_date:
                date_query['$lte'] = end_date
            if date_query:
                query['published_date'] = date_query

        try:
            return list(self.articles.find(
                query,
                {'_id': 0}
            ).sort('published_date', -1).limit(limit))
        except Exception as e:
            self.logger.error(f"Error retrieving articles: {str(e)}")
            return []

    def close(self):
        """Close the database connection"""
        try:
            self.client.close()
            self.logger.info("Database connection closed")
        except Exception as e:
            self.logger.error(f"Error closing database connection: {str(e)}")