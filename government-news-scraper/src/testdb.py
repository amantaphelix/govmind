# src/test_db.py
from database.db_manager import DatabaseManager
from config.settings import MONGODB_URI

db = DatabaseManager(MONGODB_URI)
print("Database connected:", db.articles.name)
db.close()
