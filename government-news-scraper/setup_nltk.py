import nltk

def setup_nltk():
    # Download required NLTK data
    print("Downloading required NLTK data...")
    nltk.download('punkt')
    nltk.download('stopwords')
    print("NLTK setup complete!")

if __name__ == "__main__":
    setup_nltk()