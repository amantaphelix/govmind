import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

class DataCleaner:
    def __init__(self):
        # Try to download NLTK resources if not already present
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
            
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
            
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            print("Warning: Stopwords not available. Proceeding without stopword removal.")
            self.stop_words = set()

    def clean_text(self, text):
        """
        Clean and normalize text
        """
        if not text:
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        try:
            # Tokenize
            tokens = word_tokenize(text)
            
            # Remove stopwords
            tokens = [token for token in tokens if token not in self.stop_words]
            
            return ' '.join(tokens)
        except Exception as e:
            print(f"Warning: Error in text processing: {e}")
            # Fallback to basic cleaning if NLTK processing fails
            return ' '.join(text.split())

    def remove_duplicates(self, news_items):
        """
        Remove duplicate news items based on title
        """
        seen_titles = set()
        unique_items = []
        
        for item in news_items:
            title = item.get('title', '')
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_items.append(item)
        
        return unique_items