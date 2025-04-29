"""
Integration with Google's Gemini AI for generating interview questions and feedback.
"""
import json
import os
from typing import Dict, List, Optional, Union

import google.generativeai as genai

# Check if Gemini API key is available
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize Gemini if API key is available
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Always use gemini-1.5-flash as it's free
    default_model = "gemini-1.5-flash"
    try:
        # Just log the available models but always use flash
        available_models = [model.name for model in genai.list_models() 
                          if "generateContent" in model.supported_generation_methods]
        print(f"Available Gemini models: {available_models}")
        
        # Force usage of gemini-1.5-flash regardless of what's available
        default_model = "gemini-1.5-flash"
    except Exception as e:
        print(f"Error listing Gemini models: {e}")
        # Keep using gemini-1.5-flash even if we couldn't list models
else:
    default_model = None


def is_gemini_available() -> bool:
    """Check if Gemini integration is available."""
    return GEMINI_API_KEY is not None and default_model is not None


def generate_question_feedback(answer_text: str, question_text: str, category: str) -> Dict:
    """
    Generate feedback for an interview answer using Gemini.
    
    Args:
        answer_text: The user's answer
        question_text: The question that was asked
        category: The category of question (warmup, technical, behavioral, situational)
        
    Returns:
        dict with feedback, scores, and improvement suggestions
    """
    if not is_gemini_available():
        return {
            "feedback": "AI-powered feedback is not available. Please check your answer for completeness and relevance.",
            "completeness": 70,
            "relevance": 70, 
            "structure": 70,
            "grammar_score": 80,
            "improvement_suggestions": "• Make sure your answer addresses the question directly\n• Include specific examples when possible\n• Check for clarity and conciseness"
        }
    
    # Guidance for different question categories
    category_guidance = "Focus on how well the answer addresses the general question."
    if category == "technical":
        category_guidance = "Check if the answer demonstrates technical knowledge, problem-solving skills, and accuracy."
    elif category == "behavioral":
        category_guidance = "Check if the answer follows the STAR method (Situation, Task, Action, Result) and demonstrates relevant experience."
    elif category == "situational":
        category_guidance = "Check if the answer demonstrates problem-solving, decision-making, and professional judgment."
    
    try:
        model = genai.GenerativeModel(default_model)
        
        # Create the prompt
        prompt = f"""You are an expert interview coach analyzing a candidate's response to an interview question.
        
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
        
        Question: {question_text}
        
        Answer: {answer_text}
        
        Return only valid JSON in your response with no additional text.
        """
        
        response = model.generate_content(prompt)
        
        # Extract JSON from the response
        try:
            # Try different ways to extract JSON
            if hasattr(response, 'text'):
                text_response = response.text
            else:
                text_response = str(response)
            
            # Try to find JSON in the response
            if '{' in text_response and '}' in text_response:
                json_start = text_response.find('{')
                json_end = text_response.rfind('}') + 1
                json_str = text_response[json_start:json_end]
                result = json.loads(json_str)
            else:
                # If no JSON found, create a simple structure
                raise ValueError("No JSON found in response")
                
            # Ensure all required fields are present
            required_fields = ["feedback", "completeness", "relevance", "structure", "grammar_score", "improvement_suggestions"]
            for field in required_fields:
                if field not in result:
                    if field == "improvement_suggestions":
                        result[field] = "• Make sure your answer addresses the question directly\n• Include specific examples when possible\n• Check for clarity and conciseness"
                    elif "score" in field:
                        result[field] = 70
                    else:
                        result[field] = "Not evaluated"
                        
            # Format improvement suggestions as a bulleted list if it's a string
            if isinstance(result.get('improvement_suggestions'), str):
                suggestions = result['improvement_suggestions']
                # Keep as is if it already has bullet points
                if not suggestions.strip().startswith('-') and not suggestions.strip().startswith('•'):
                    result['improvement_suggestions'] = "• " + suggestions.replace('\n', '\n• ')
                    
            # Validate scores are within range
            for score_field in ["completeness", "relevance", "structure", "grammar_score"]:
                if score_field in result:
                    try:
                        result[score_field] = max(0, min(100, int(result[score_field])))
                    except (ValueError, TypeError):
                        result[score_field] = 70
                        
            return result
        
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing Gemini JSON response: {e}")
            return {
                "feedback": "The AI provided feedback, but it couldn't be properly formatted. Please review your answer for completeness and relevance.",
                "completeness": 70,
                "relevance": 70,
                "structure": 70,
                "grammar_score": 80,
                "improvement_suggestions": "• Make sure your answer addresses the question directly\n• Include specific examples when possible\n• Check for clarity and conciseness"
            }
            
    except Exception as e:
        print(f"Error generating feedback with Gemini: {e}")
        return {
            "feedback": "An error occurred while generating AI feedback. Please review your answer for completeness and relevance.",
            "completeness": 70,
            "relevance": 70,
            "structure": 70,
            "grammar_score": 80,
            "improvement_suggestions": "• Make sure your answer addresses the question directly\n• Include specific examples when possible\n• Check for clarity and conciseness"
        }


def generate_interview_questions(role: str, category: str, num_questions: int = 5) -> List[str]:
    """
    Generate custom interview questions for a specific role and category using Gemini.
    
    Args:
        role: The job role
        category: Question category (warmup, technical, behavioral, situational)
        num_questions: Number of questions to generate
        
    Returns:
        list of question strings
    """
    if not is_gemini_available():
        return []
    
    # Guidance for different question categories
    category_descriptions = {
        "warmup": "introductory questions that help establish rapport and ease into the interview",
        "technical": "questions that assess technical knowledge, skills, and problem-solving abilities specific to the role",
        "behavioral": "questions that ask about past experiences to predict future behavior (should prompt STAR method responses)",
        "situational": "hypothetical scenario questions that assess judgment and approach to job-related situations"
    }
    
    category_desc = category_descriptions.get(category, "interview questions")
    
    try:
        model = genai.GenerativeModel(default_model)
        
        prompt = f"""You are an expert interviewer creating questions for job candidates.
        Generate {num_questions} {category} {category_desc} for a {role} position.
        
        Return the questions in a JSON array format with just the question text strings.
        Make each question unique, challenging but fair, and specific to the {role} role.
        
        Return only a valid JSON array of strings, with no additional text.
        """
        
        response = model.generate_content(prompt)
        
        # Try to extract questions from the response
        try:
            # Get text response
            if hasattr(response, 'text'):
                text_response = response.text
            else:
                text_response = str(response)
                
            # Try to find JSON in the response
            if '[' in text_response and ']' in text_response:
                json_start = text_response.find('[')
                json_end = text_response.rfind(']') + 1
                json_str = text_response[json_start:json_end]
                questions = json.loads(json_str)
                return questions[:num_questions]
            else:
                # If no JSON array found, try to extract line by line
                lines = [line.strip() for line in text_response.split('\n') if line.strip()]
                
                # Extract questions (looking for numbered items or quotes)
                questions = []
                for line in lines:
                    # Remove numbering and quotes
                    cleaned_line = line
                    # Remove numbering like "1." or "1)"
                    if cleaned_line and cleaned_line[0].isdigit() and len(cleaned_line) > 2:
                        if cleaned_line[1] in ['.', ')', ':'] and cleaned_line[2] == ' ':
                            cleaned_line = cleaned_line[3:].strip()
                    # Remove quotes
                    if cleaned_line.startswith('"') and cleaned_line.endswith('"'):
                        cleaned_line = cleaned_line[1:-1].strip()
                    if cleaned_line.startswith("'") and cleaned_line.endswith("'"):
                        cleaned_line = cleaned_line[1:-1].strip()
                    
                    # Add if it looks like a question
                    if cleaned_line and '?' in cleaned_line:
                        questions.append(cleaned_line)
                        
                return questions[:num_questions]
                
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract questions line by line
            text = response.text if hasattr(response, 'text') else str(response)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Look for lines that look like questions
            questions = [line for line in lines if '?' in line]
            return questions[:num_questions]
            
    except Exception as e:
        print(f"Error generating questions with Gemini: {e}")
        return []