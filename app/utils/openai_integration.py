import os
import json
from openai import OpenAI

# Initialize the OpenAI client with API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = None

if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)


def is_openai_available():
    """Check if OpenAI integration is available."""
    return openai_client is not None


def generate_question_feedback(answer_text, question_text, category, max_tokens=1000):
    """
    Generate feedback for an interview answer using OpenAI.
    
    Args:
        answer_text: The user's answer
        question_text: The question that was asked
        category: The category of question (warmup, technical, behavioral, situational)
        max_tokens: Maximum tokens to generate
        
    Returns:
        dict with feedback, scores, and improvement suggestions
    """
    if not is_openai_available():
        return {
            "feedback": "Detailed AI feedback is not available. Please check your answer for completeness and relevance to the question.",
            "completeness": 70,
            "relevance": 70,
            "structure": 70,
            "grammar_score": 80,
            "improvement_suggestions": "To improve your answer, make sure to address all parts of the question directly and provide specific examples."
        }
    
    # Prepare prompt based on question category
    category_guidance = ""
    if category == "technical":
        category_guidance = "Focus on technical accuracy, clarity of explanation, and demonstration of knowledge."
    elif category == "behavioral":
        category_guidance = "Evaluate if the answer follows the STAR method (Situation, Task, Action, Result) and provides specific examples."
    elif category == "situational":
        category_guidance = "Check if the answer demonstrates problem-solving, decision-making, and professional judgment."
    
    # The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    # do not change this unless explicitly requested by the user
    try:
        # Check if we've encountered quota issues before
        if hasattr(openai_client, '_quota_exceeded') and openai_client._quota_exceeded:
            print("Skipping OpenAI API call due to previous quota exceeded error")
            raise Exception("Quota exceeded")
            
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an expert interview coach analyzing a candidate's response to an interview question.
                    
                    Question category: {category}
                    {category_guidance}
                    
                    Evaluate the answer on the following criteria:
                    1. Completeness (0-100): How thoroughly the answer addresses all aspects of the question
                    2. Relevance (0-100): How relevant and on-topic the answer is
                    3. Structure (0-100): How well organized and coherent the answer is
                    4. Grammar and clarity (0-100): Quality of language, grammar, and clarity
                    
                    Provide your analysis in JSON format with the following fields:
                    - feedback: Constructive feedback about the answer (300-500 characters)
                    - completeness: Score from 0-100 
                    - relevance: Score from 0-100
                    - structure: Score from 0-100
                    - grammar_score: Score from 0-100
                    - improvement_suggestions: 3-5 specific, actionable suggestions for improvement (bulleted list)
                    """
                },
                {
                    "role": "user",
                    "content": f"Question: {question_text}\n\nAnswer: {answer_text}"
                }
            ],
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        result = json.loads(response.choices[0].message.content)
        
        # Format improvement suggestions as a bulleted list if it's a string
        if isinstance(result.get('improvement_suggestions'), str):
            suggestions = result['improvement_suggestions']
            # Keep as is if it already has bullet points
            if not suggestions.strip().startswith('-') and not suggestions.strip().startswith('•'):
                result['improvement_suggestions'] = "• " + suggestions.replace('\n', '\n• ')
        
        return result
    except Exception as e:
        print(f"Error generating feedback with OpenAI: {e}")
        # Mark the client as having quota issues if that's the error
        if 'quota' in str(e).lower() or 'insufficient_quota' in str(e).lower():
            openai_client._quota_exceeded = True
            
        return {
            "feedback": "An error occurred while generating AI feedback. Please review your answer for completeness and relevance.",
            "completeness": 70,
            "relevance": 70,
            "structure": 70,
            "grammar_score": 80,
            "improvement_suggestions": "• Make sure your answer addresses the question directly\n• Include specific examples when possible\n• Check for clarity and conciseness"
        }


def generate_interview_questions(role, category, num_questions=5):
    """
    Generate custom interview questions for a specific role and category using OpenAI.
    
    Args:
        role: The job role
        category: Question category (warmup, technical, behavioral, situational)
        num_questions: Number of questions to generate
        
    Returns:
        list of question strings
    """
    if not is_openai_available():
        return []
    
    # Guidance for different question categories
    category_descriptions = {
        "warmup": "introductory questions that help establish rapport and ease into the interview",
        "technical": "questions that assess technical knowledge, skills, and problem-solving abilities specific to the role",
        "behavioral": "questions that ask about past experiences to predict future behavior (should prompt STAR method responses)",
        "situational": "hypothetical scenario questions that assess judgment and approach to job-related situations"
    }
    
    category_desc = category_descriptions.get(category, "interview questions")
    
    # The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    # do not change this unless explicitly requested by the user
    try:
        # Check if we've encountered quota issues before
        if hasattr(openai_client, '_quota_exceeded') and openai_client._quota_exceeded:
            print("Skipping OpenAI API call due to previous quota exceeded error")
            raise Exception("Quota exceeded")
            
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an expert interviewer creating questions for job candidates.
                    Generate {num_questions} {category} {category_desc} for a {role} position.
                    
                    Return the questions in a JSON array format with just the question text strings.
                    Make each question unique, challenging but fair, and specific to the {role} role.
                    Do not include anything except the JSON array of questions.
                    """
                }
            ],
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        try:
            result = json.loads(response.choices[0].message.content)
            if isinstance(result, dict) and "questions" in result:
                return result["questions"]
            elif isinstance(result, list):
                return result
            else:
                # Try to find any array in the response
                for key, value in result.items():
                    if isinstance(value, list):
                        return value
                return []
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract questions line by line
            text = response.choices[0].message.content
            questions = [line.strip() for line in text.split('\n') if line.strip()]
            return questions[:num_questions]
            
    except Exception as e:
        print(f"Error generating questions with OpenAI: {e}")
        # Mark the client as having quota issues if that's the error
        if 'quota' in str(e).lower() or 'insufficient_quota' in str(e).lower():
            openai_client._quota_exceeded = True
        return []