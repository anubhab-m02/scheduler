import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nrclex import NRCLex

# Download required NLTK data
nltk.download('vader_lexicon')

def analyze_sentiment(text):
    """
    Analyze the sentiment of the given text using NLTK's VADER.

    Args:
        text (str): The text to analyze.

    Returns:
        dict: A dictionary containing sentiment scores and the overall sentiment category.
    """
    sia = SentimentIntensityAnalyzer()
    sentiment_scores = sia.polarity_scores(text)
    
    # Determine overall sentiment
    compound = sentiment_scores['compound']
    if compound >= 0.05:
        sentiment = 'Positive'
    elif compound <= -0.05:
        sentiment = 'Negative'
    else:
        sentiment = 'Neutral'
    
    return {
        'compound': compound,
        'neg': sentiment_scores['neg'],
        'neu': sentiment_scores['neu'],
        'pos': sentiment_scores['pos'],
        'sentiment': sentiment
    }

def analyze_emotions(text):
    """
    Analyze the emotions present in the given text using NRCLex.

    Args:
        text (str): The text to analyze.

    Returns:
        dict: A dictionary containing emotion counts.
    """
    emotion = NRCLex(text)
    emotions = emotion.raw_emotion_scores
    return emotions
