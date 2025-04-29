import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from app import db
from app.utils.sentiment import analyze_sentiment
from app.utils.grammar import check_grammar

# Download necessary NLTK data on first run
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


def evaluate_answer(answer_id):
    """Evaluate an answer using NLP techniques."""
    from app.models.answer import Answer
    from app.models.question import Question
    from app.utils.openai_integration import generate_question_feedback as openai_generate_feedback, is_openai_available
    from app.utils.gemini_integration import generate_question_feedback as gemini_generate_feedback, is_gemini_available
    
    answer = Answer.query.get(answer_id)
    if not answer:
        return False
    
    question = Question.query.get(answer.question_id)
    
    # Get the answer text
    text = answer.text.strip()
    
    # Basic validations
    if not text:
        set_minimal_feedback(answer, "Your answer is empty. Please provide a response.")
        return False
    
    # Try using AI for comprehensive evaluation, preferring OpenAI if available, then Gemini
    ai_failed = True
    
    # Try OpenAI first
    if is_openai_available():
        try:
            # Get AI-generated feedback from OpenAI
            ai_feedback = openai_generate_feedback(
                text,
                question.text,
                question.category
            )
            
            # Check if feedback contains error message from the fallback
            if "An error occurred while generating AI feedback" in ai_feedback.get('feedback', ''):
                # This means OpenAI failed, raise exception to try Gemini
                raise Exception("OpenAI fallback was triggered")
            
            # Use AI-generated scores and feedback
            completeness_score = ai_feedback.get('completeness', 70)
            relevance_score = ai_feedback.get('relevance', 70)
            structure_score = ai_feedback.get('structure', 70)
            grammar_score = ai_feedback.get('grammar_score', 80)
            feedback = ai_feedback.get('feedback', "Thank you for your answer.")
            suggestions = ai_feedback.get('improvement_suggestions', "")
            
            # Mark AI as successful
            ai_failed = False
            print("Successfully used OpenAI for feedback")
            
        except Exception as e:
            print(f"Error using OpenAI for feedback: {e}")
            # Will fall back to Gemini or basic NLP evaluation
    
    # If OpenAI failed or isn't available, try Gemini
    if ai_failed and is_gemini_available():
        try:
            # Get AI-generated feedback from Gemini
            ai_feedback = gemini_generate_feedback(
                text,
                question.text,
                question.category
            )
            
            # Use AI-generated scores and feedback
            completeness_score = ai_feedback.get('completeness', 70)
            relevance_score = ai_feedback.get('relevance', 70)
            structure_score = ai_feedback.get('structure', 70)
            grammar_score = ai_feedback.get('grammar_score', 80)
            feedback = ai_feedback.get('feedback', "Thank you for your answer.")
            suggestions = ai_feedback.get('improvement_suggestions', "")
            
            # Mark AI as successful
            ai_failed = False
            print("Successfully used Gemini for feedback")
            
        except Exception as e:
            print(f"Error using Gemini for feedback: {e}")
            # Will fall back to basic NLP evaluation
    
    # Run grammar check and sentiment analysis regardless of AI provider
    if not ai_failed:
        # Still run grammar check to get specific issues
        grammar_issues, _ = check_grammar(text)
        
        # Analyze sentiment
        sentiment_score, sentiment_label = analyze_sentiment(text)
    
    # Fall back to basic NLP evaluation if both AI services fail or aren't available
    if ai_failed:
        # Perform evaluations using basic NLP
        completeness_score = evaluate_completeness(text, question.text)
        relevance_score = evaluate_relevance(text, question.text)
        structure_score = evaluate_structure(text, question.category)
        
        # Check grammar
        grammar_issues, grammar_score = check_grammar(text)
        
        # Analyze sentiment
        sentiment_score, sentiment_label = analyze_sentiment(text)
        
        # Generate feedback
        feedback = generate_feedback(
            text, 
            question.text, 
            question.category,
            completeness_score, 
            relevance_score, 
            structure_score,
            grammar_score,
            sentiment_score
        )
        
        # Generate improvement suggestions
        suggestions = generate_improvement_suggestions(
            text,
            question.category,
            completeness_score,
            relevance_score,
            structure_score,
            grammar_score
        )
    
    # Save results
    answer.completeness = completeness_score
    answer.relevance = relevance_score
    answer.structure = structure_score
    answer.grammar_score = grammar_score
    answer.sentiment_score = sentiment_score
    answer.feedback = feedback
    answer.grammar_issues = grammar_issues
    answer.improvement_suggestions = suggestions
    
    # Calculate overall score
    answer.calculate_overall_score()
    
    db.session.commit()
    return True


def set_minimal_feedback(answer, feedback):
    """Set minimal feedback for invalid answers."""
    answer.completeness = 0
    answer.relevance = 0
    answer.structure = 0
    answer.grammar_score = 0
    answer.sentiment_score = 0
    answer.feedback = feedback
    answer.grammar_issues = "N/A"
    answer.improvement_suggestions = "Please provide a valid answer."
    answer.score = 0
    db.session.commit()


def evaluate_completeness(text, question):
    """Evaluate how complete the answer is."""
    # Basic metrics for completeness
    word_count = len(word_tokenize(text))
    sentence_count = len(sent_tokenize(text))
    
    # Check if the answer is too short
    if word_count < 10:
        return 20.0
    elif word_count < 25:
        return 40.0
    elif word_count < 50:
        return 60.0
    elif word_count < 100:
        return 80.0
    else:
        return 95.0


def evaluate_relevance(text, question):
    """Evaluate how relevant the answer is to the question."""
    # Simple keyword matching for relevance
    question_words = set(word.lower() for word in word_tokenize(question) 
                         if word.lower() not in stopwords.words('english'))
    answer_words = set(word.lower() for word in word_tokenize(text) 
                       if word.lower() not in stopwords.words('english'))
    
    # Calculate overlap
    if not question_words:
        return 70.0  # Default if no meaningful words in question
    
    overlap = question_words.intersection(answer_words)
    overlap_ratio = len(overlap) / len(question_words)
    
    # Scale to 0-100
    relevance_score = min(overlap_ratio * 100 + 50, 100)
    return relevance_score


def evaluate_structure(text, category):
    """Evaluate the structure of the answer based on category."""
    sentences = sent_tokenize(text)
    
    # Too few sentences indicates poor structure
    if len(sentences) < 2:
        return 30.0
    
    # Check for STAR format in behavioral questions
    if category == 'behavioral':
        # Look for situation, task, action, result components
        star_components = 0
        
        # Simple keyword matching for STAR components
        situation_keywords = ['situation', 'context', 'background', 'when', 'where']
        task_keywords = ['task', 'goal', 'objective', 'responsibility', 'needed to']
        action_keywords = ['action', 'did', 'steps', 'approach', 'implemented', 'managed']
        result_keywords = ['result', 'outcome', 'achieved', 'learned', 'impact', 'benefit']
        
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in situation_keywords):
            star_components += 1
        if any(keyword in text_lower for keyword in task_keywords):
            star_components += 1
        if any(keyword in text_lower for keyword in action_keywords):
            star_components += 1
        if any(keyword in text_lower for keyword in result_keywords):
            star_components += 1
        
        # Scale the score based on STAR components
        return min(star_components * 25, 100)
    
    # For technical questions, check for explanation and examples
    elif category == 'technical':
        has_explanation = len(sentences) >= 3
        has_example = 'example' in text.lower() or 'instance' in text.lower() or 'case' in text.lower()
        
        if has_explanation and has_example:
            return 90.0
        elif has_explanation:
            return 70.0
        else:
            return 50.0
    
    # Default evaluation for other categories
    else:
        # Basic structure check - intro, body, conclusion
        if len(sentences) >= 5:
            return 80.0
        elif len(sentences) >= 3:
            return 60.0
        else:
            return 40.0


def generate_feedback(text, question, category, completeness, relevance, structure, grammar, sentiment):
    """Generate feedback text based on evaluation scores."""
    feedback_parts = []
    
    # Overall assessment
    average_score = (completeness + relevance + structure + grammar) / 4
    if average_score >= 80:
        feedback_parts.append("Excellent answer! You've addressed the question thoroughly.")
    elif average_score >= 60:
        feedback_parts.append("Good answer overall. There are some areas for improvement.")
    else:
        feedback_parts.append("Your answer needs significant improvement.")
    
    # Completeness feedback
    if completeness >= 80:
        feedback_parts.append("Your answer is comprehensive and well-detailed.")
    elif completeness >= 60:
        feedback_parts.append("Your answer covers the basics but could use more detail.")
    else:
        feedback_parts.append("Your answer is too brief. Consider expanding with more details.")
    
    # Relevance feedback
    if relevance >= 80:
        feedback_parts.append("Your response is highly relevant to the question asked.")
    elif relevance >= 60:
        feedback_parts.append("Your answer is somewhat relevant but could focus more on the question.")
    else:
        feedback_parts.append("Your answer doesn't seem to address the question directly.")
    
    # Structure feedback
    if category == 'behavioral':
        if structure >= 80:
            feedback_parts.append("You've effectively used the STAR format (Situation, Task, Action, Result).")
        elif structure >= 40:
            feedback_parts.append("Try to more clearly structure your answer using the STAR format.")
        else:
            feedback_parts.append("Your answer lacks a clear structure. Use the STAR format for behavioral questions.")
    elif structure >= 80:
        feedback_parts.append("Your answer has a clear and logical structure.")
    elif structure >= 60:
        feedback_parts.append("Your answer has a reasonable structure but could be organized better.")
    else:
        feedback_parts.append("Your answer lacks a clear structure. Consider organizing your thoughts better.")
    
    # Grammar feedback
    if grammar >= 90:
        feedback_parts.append("Your grammar and language use are excellent.")
    elif grammar >= 70:
        feedback_parts.append("Your grammar is good with minor issues.")
    else:
        feedback_parts.append("There are several grammar issues that should be addressed.")
    
    # Sentiment feedback
    if sentiment > 0.3:
        feedback_parts.append("Your tone is positive and confident, which is excellent.")
    elif sentiment > -0.3:
        feedback_parts.append("Your tone is neutral. Consider adding more enthusiasm when appropriate.")
    else:
        feedback_parts.append("Your tone seems negative. Try to maintain a more positive or neutral tone.")
    
    return " ".join(feedback_parts)


def generate_improvement_suggestions(text, category, completeness, relevance, structure, grammar):
    """Generate specific suggestions for improvement."""
    suggestions = []
    
    # Completeness suggestions
    if completeness < 60:
        suggestions.append("Add more details and examples to make your answer more comprehensive.")
    
    # Relevance suggestions
    if relevance < 70:
        suggestions.append("Focus more directly on addressing the specific question asked.")
    
    # Structure suggestions
    if category == 'behavioral' and structure < 80:
        suggestions.append("Structure your answer using the STAR format: Situation, Task, Action, Result.")
    elif structure < 60:
        suggestions.append("Organize your answer with a clear introduction, body points, and conclusion.")
    
    # Grammar suggestions
    if grammar < 70:
        suggestions.append("Review your grammar and sentence structure for clarity.")
    
    # Word choice suggestions
    if category == 'technical' and completeness < 80:
        suggestions.append("Use more technical terminology relevant to the topic.")
    
    # Default suggestion if everything looks good
    if not suggestions:
        suggestions.append("Your answer is strong. To improve further, consider adding more specific examples or data points to support your statements.")
    
    return "\n".join(suggestions)
