import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nrclex import NRCLex
from textblob import download_corpora
import streamlit as st
import os

NLTK_DATA_PATH = os.path.join(os.path.dirname(__file__), 'nltk_data')

os.makedirs(NLTK_DATA_PATH, exist_ok=True)

nltk.data.path.append(NLTK_DATA_PATH)

def download_nltk_data():
    """
    Download required NLTK data. Cached to prevent repeated downloads.
    """
    nltk.download('vader_lexicon', download_dir=NLTK_DATA_PATH)
    nltk.download('punkt', download_dir=NLTK_DATA_PATH)

def download_textblob_corpora():
    """
    Download TextBlob corpora. Cached to prevent repeated downloads.
    """
    download_corpora.download_all()

download_nltk_data()
download_textblob_corpora()

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
