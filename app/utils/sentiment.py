from textblob import TextBlob


def analyze_sentiment(text):
    """
    Analyze the sentiment of a text response.
    Returns:
        - sentiment_score: a float between -1 (very negative) and 1 (very positive)
        - sentiment_label: a string label ('positive', 'neutral', or 'negative')
    """
    if not text:
        return 0, 'neutral'
    
    # Create a TextBlob object
    blob = TextBlob(text)
    
    # Get the sentiment polarity (between -1 and 1)
    sentiment_score = blob.sentiment.polarity
    
    # Determine the sentiment label
    if sentiment_score > 0.2:
        sentiment_label = 'positive'
    elif sentiment_score < -0.2:
        sentiment_label = 'negative'
    else:
        sentiment_label = 'neutral'
    
    return sentiment_score, sentiment_label


def get_sentiment_details(text):
    """
    Get detailed sentiment analysis of a text including sentence-by-sentence breakdown.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        dict: Sentiment analysis details
    """
    if not text:
        return {
            'overall_sentiment': 0,
            'overall_label': 'neutral',
            'sentence_analysis': []
        }
    
    blob = TextBlob(text)
    
    # Overall sentiment
    overall_sentiment = blob.sentiment.polarity
    
    # Determine the sentiment label
    if overall_sentiment > 0.2:
        overall_label = 'positive'
    elif overall_sentiment < -0.2:
        overall_label = 'negative'
    else:
        overall_label = 'neutral'
    
    # Sentence-by-sentence analysis
    sentence_analysis = []
    for sentence in blob.sentences:
        sentiment = sentence.sentiment.polarity
        
        # Determine label for each sentence
        if sentiment > 0.2:
            label = 'positive'
        elif sentiment < -0.2:
            label = 'negative'
        else:
            label = 'neutral'
        
        sentence_analysis.append({
            'text': str(sentence),
            'sentiment': sentiment,
            'label': label
        })
    
    return {
        'overall_sentiment': overall_sentiment,
        'overall_label': overall_label,
        'sentence_analysis': sentence_analysis
    }
