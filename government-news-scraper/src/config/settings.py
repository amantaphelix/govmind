# config/settings.py
from dotenv import load_dotenv
import os
from pathlib import Path
load_dotenv()

# Database Configuration
MONGODB_URI = os.getenv('MONGODB_URI')
if not MONGODB_URI:
    raise ValueError("MONGODB_URI is not set in the environment variables.")

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