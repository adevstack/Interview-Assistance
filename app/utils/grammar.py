import re
from collections import Counter
import string


def check_grammar(text):
    """
    A simple grammar checking function that looks for common writing issues.
    
    This is a lightweight alternative to language_tool_python, which can cause
    connection errors or timeouts. This implementation focuses on basic grammar
    and writing quality checks without requiring external services.
    
    Args:
        text (str): The text to check
        
    Returns:
        tuple: (grammar_issues_text, grammar_score)
    """
    if not text or not text.strip():
        return "No text provided.", 0
    
    # Limit text length to prevent performance issues
    MAX_TEXT_LENGTH = 5000
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH] + "..."
        print(f"Grammar check: Text truncated to {MAX_TEXT_LENGTH} characters")
    
    try:
        # Basic grammar and writing quality analysis
        issues = []
        
        # Check for short sentences (less than 3 words)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        for i, sentence in enumerate(sentences):
            words = re.findall(r'\b\w+\b', sentence)
            
            # Very short sentences (might be incomplete)
            if 0 < len(words) < 3:
                issues.append({
                    'message': "Very short sentence that may be incomplete",
                    'context': sentence,
                    'replacements': ["Consider elaborating or combining with another sentence"]
                })
            
            # Check for duplicate words
            word_positions = {}
            duplicate_words = set()
            
            for j, word in enumerate(words):
                word_lower = word.lower()
                if word_lower in word_positions:
                    # Only count duplicates that are close to each other (within 3 words)
                    if j - word_positions[word_lower] <= 3:
                        duplicate_words.add(word_lower)
                word_positions[word_lower] = j
            
            if duplicate_words and len(words) > 3:
                duplicates = ", ".join(duplicate_words)
                issues.append({
                    'message': f"Repeated word(s): {duplicates}",
                    'context': sentence,
                    'replacements': ["Consider using synonyms or restructuring"]
                })
                
            # Check for long sentences (over 40 words)
            if len(words) > 40:
                issues.append({
                    'message': "Very long sentence that may be hard to follow",
                    'context': sentence[:75] + "..." if len(sentence) > 75 else sentence,
                    'replacements': ["Consider breaking into multiple sentences for clarity"]
                })
        
        # Check for excessive punctuation
        punctuation_count = Counter(c for c in text if c in string.punctuation)
        for punct, count in punctuation_count.items():
            if punct in "!?." and count > 3:
                # Find a context with excessive punctuation
                pattern = r'[^!?.]{0,20}[!?.]{3,}[^!?.]{0,20}'
                match = re.search(pattern, text)
                context = match.group(0) if match else f"...{punct}{punct}{punct}..."
                
                issues.append({
                    'message': f"Excessive punctuation: '{punct}'",
                    'context': context,
                    'replacements': ["Use punctuation more sparingly"]
                })
                
        # Check for passive voice indicators (simple detection)
        passive_markers = [
            r'\b(?:am|is|are|was|were|be|been|being)\s+\w+ed\b',  # "is completed"
            r'\b(?:has|have|had)\s+been\s+\w+ed\b',              # "has been completed"
        ]
        
        for pattern in passive_markers:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get some context around the match
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                context = text[start:end]
                
                issues.append({
                    'message': "Possible passive voice",
                    'context': f"...{context}..." if start > 0 or end < len(text) else context,
                    'replacements': ["Consider using active voice for stronger impact"]
                })
        
        # Check for common filler words and phrases
        filler_phrases = [
            r'\bin my opinion\b', r'\bi think\b', r'\bi believe\b', r'\bi feel\b',
            r'\bbasically\b', r'\bliterally\b', r'\bactually\b', r'\bvery\b', 
            r'\breally\b', r'\bquite\b', r'\bin order to\b', r'\bat the end of the day\b',
            r'\bfor all intents and purposes\b'
        ]
        
        for pattern in filler_phrases:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get some context around the match
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                context = text[start:end]
                phrase = match.group(0)
                
                issues.append({
                    'message': f"Filler phrase: '{phrase}'",
                    'context': f"...{context}..." if start > 0 or end < len(text) else context,
                    'replacements': ["Consider removing or replacing with more precise language"]
                })
        
        # Limit the number of issues reported
        MAX_ISSUES = 5
        issues = issues[:MAX_ISSUES] if len(issues) > MAX_ISSUES else issues
        
        # Format issues as text
        if issues:
            issues_text = "\n".join([
                f"{i+1}. {issue['message']}\n   Context: {issue['context']}\n" +
                (f"   Suggestion: {issue['replacements'][0]}" if issue['replacements'] else "")
                for i, issue in enumerate(issues)
            ])
        else:
            issues_text = "No significant grammar issues found."
        
        # Calculate a grammar score (0-100)
        # Base score starts at 85 (good), and each issue reduces it
        base_score = 85
        issue_penalty = min(50, len(issues) * 5)  # Cap the penalty at 50 points
        grammar_score = max(0, min(100, base_score - issue_penalty))
        
        return issues_text, grammar_score
    
    except Exception as e:
        print(f"Error in grammar check: {e}")
        return "Grammar check encountered an error.", 75  # Default score when service fails


def get_readability_metrics(text):
    """
    Calculate readability metrics for the text.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        dict: Various readability metrics
    """
    if not text:
        return {
            'avg_word_length': 0,
            'avg_sentence_length': 0,
            'complex_word_percentage': 0
        }
    
    # Split into words and sentences
    words = re.findall(r'\b\w+\b', text.lower())
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    
    if not words or not sentences:
        return {
            'avg_word_length': 0,
            'avg_sentence_length': 0,
            'complex_word_percentage': 0
        }
    
    # Calculate metrics
    avg_word_length = sum(len(word) for word in words) / len(words)
    avg_sentence_length = len(words) / len(sentences)
    
    # Count complex words (3+ syllables)
    complex_words = sum(1 for word in words if count_syllables(word) >= 3)
    complex_word_percentage = (complex_words / len(words)) * 100
    
    return {
        'avg_word_length': avg_word_length,
        'avg_sentence_length': avg_sentence_length,
        'complex_word_percentage': complex_word_percentage
    }


def count_syllables(word):
    """Simple function to estimate syllable count."""
    word = word.lower()
    if len(word) <= 3:
        return 1
    
    # Remove ending silent 'e'
    if word.endswith('e'):
        word = word[:-1]
    
    # Count vowel groups
    vowels = "aeiouy"
    count = 0
    prev_is_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel
    
    # Ensure at least one syllable
    return max(count, 1)
