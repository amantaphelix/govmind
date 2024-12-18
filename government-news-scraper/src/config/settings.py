# config/settings.py
import os
from pathlib import Path

# Database Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://amantaphelix:amantaphelix@cluster0.mmmiw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')

# Scraper Configuration
BASE_CACHE_DIR = Path('cache')
USER_AGENT = 'NewsScraperBot/1.0'
DEFAULT_CRAWL_DELAY = 5

# News Sources
NEWS_SOURCES = {
    'indiatoday': 'https://www.indiatoday.in/',
    'hindu': 'https://www.thehindu.com/',
    'toi': 'https://timesofindia.indiatimes.com/india',
    'ndtv': 'https://www.ndtv.com/india',
    'indianexpress': 'https://indianexpress.com/section/india/',
    'deccanchronicle': 'https://www.deccanchronicle.com/',
    'hindustantimes': 'https://www.hindustantimes.com/',
    'zee': 'https://zeenews.india.com/',
    'livemint': 'https://www.livemint.com/',
    'firstpost': 'https://www.firstpost.com/',
    'news18': 'https://www.news18.com/'
}

# Logging Configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': 'scraper.log',
            'mode': 'a',
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}