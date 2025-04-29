import re
import language_tool_python


# Initialize language tool for grammar checking
# Use a singleton pattern to avoid initializing multiple instances
class LanguageToolSingleton:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            try:
                cls._instance = language_tool_python.LanguageTool('en-US')
            except Exception as e:
                print(f"Error initializing LanguageTool: {e}")
                # Fallback to dummy checker if there's an error
                cls._instance = DummyChecker()
        return cls._instance


class DummyChecker:
    """Fallback checker when LanguageTool cannot be initialized."""
    def check(self, text):
        return []


def check_grammar(text):
    """
    Check grammar issues in a text and calculate a grammar score.
    
    Args:
        text (str): The text to check
        
    Returns:
        tuple: (grammar_issues_text, grammar_score)
    """
    if not text:
        return "No text provided.", 0
    
    try:
        # Get LanguageTool instance
        tool = LanguageToolSingleton.get_instance()
        
        # Check grammar
        matches = tool.check(text)
        
        # Extract issues
        issues = []
        for match in matches:
            context = match.context
            offset = match.offsetInContext
            length = match.errorLength
            
            # Highlight the error in context
            highlighted = (
                context[:offset] + 
                '**' + context[offset:offset+length] + '**' + 
                context[offset+length:]
            )
            
            issues.append({
                'message': match.message,
                'context': highlighted,
                'replacements': match.replacements[:3] if match.replacements else []
            })
        
        # Format issues as text
        if issues:
            issues_text = "\n".join([
                f"{i+1}. {issue['message']}\n   Context: {issue['context']}\n" +
                (f"   Suggestions: {', '.join(issue['replacements'])}" if issue['replacements'] else "") 
                for i, issue in enumerate(issues)
            ])
        else:
            issues_text = "No grammar issues found."
        
        # Calculate grammar score (0-100)
        word_count = len(re.findall(r'\b\w+\b', text))
        if word_count == 0:
            return "Text is too short for grammar analysis.", 0
        
        # Scale score based on error rate (errors per 100 words)
        error_rate = len(matches) / word_count * 100
        grammar_score = max(0, 100 - (error_rate * 10))  # Each error reduces score
        
        return issues_text, grammar_score
    
    except Exception as e:
        print(f"Error in grammar check: {e}")
        return "Grammar check unavailable.", 70  # Default score when service fails


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
