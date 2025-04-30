"""
API routes for the application, including speech recognition with Gemini
"""
import base64
import io
import os
import tempfile
import logging
from flask import Blueprint, request, jsonify, current_app
import google.generativeai as genai

# Configure the Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# Create a blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')

def is_gemini_available():
    """Check if Gemini API is available."""
    return GEMINI_API_KEY is not None


@api_bp.route('/speech_recognition', methods=['POST'])
def speech_recognition():
    """
    Process audio with Gemini for speech recognition
    Expects a JSON object with:
    - audio_data: Base64 encoded audio data
    - audio_format: MIME type of the audio (e.g., 'audio/webm')
    """
    if not is_gemini_available():
        return jsonify({
            'error': 'Gemini API not configured',
            'transcript': None
        }), 500
    
    try:
        data = request.get_json()
        
        if not data or 'audio_data' not in data:
            return jsonify({
                'error': 'Missing audio data',
                'transcript': None
            }), 400
        
        # Get the base64 encoded audio
        audio_base64 = data.get('audio_data')
        audio_format = data.get('audio_format', 'audio/webm')
        
        # Decode the base64 audio
        audio_bytes = base64.b64decode(audio_base64)
        
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name
        
        try:
            # Use Gemini to transcribe the audio
            transcript = transcribe_audio_with_gemini(temp_path)
            
            return jsonify({
                'transcript': transcript
            })
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                current_app.logger.error(f"Error deleting temporary file: {e}")
                
    except Exception as e:
        current_app.logger.error(f"Error in speech recognition: {e}")
        return jsonify({
            'error': str(e),
            'transcript': None
        }), 500


def transcribe_audio_with_gemini(audio_file_path):
    """
    Transcribe audio using Gemini API
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        str: Transcribed text
    """
    try:
        # Check file size - Gemini has limits
        file_size = os.path.getsize(audio_file_path)
        if file_size > 20 * 1024 * 1024:  # 20MB limit
            raise ValueError(f"Audio file too large: {file_size / (1024 * 1024):.2f}MB")
        
        # Load the model - Gemini 1.5 Pro has the best audio transcription capabilities
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Prepare the audio data
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()
        
        # Create a prompt that asks for transcription, including handling of specialized terms
        prompt = """
        Please transcribe this audio accurately. Pay special attention to:
        
        1. Technical terms, especially in cybersecurity context (e.g., "phishing", "scammed")
        2. Names and specialized vocabulary
        3. Maintain punctuation and sentence structure
        
        Transcribe exactly what is said, without filtering, censoring or summarizing.
        """
        
        # Create the multipart message with audio data
        response = model.generate_content([
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"inline_data": {
                        "mime_type": "audio/webm",
                        "data": base64.b64encode(audio_data).decode('utf-8')
                    }}
                ]
            }
        ])
        
        # Extract and return the transcription
        transcription = response.text.strip()
        return transcription
        
    except Exception as e:
        current_app.logger.error(f"Error transcribing with Gemini: {e}")
        # In case of error, return a message that lets the user know what happened
        return f"Transcription error. Please try again or use browser speech recognition instead."


@api_bp.route('/answer/<int:answer_id>', methods=['GET'])
def api_answer(answer_id):
    """API endpoint to get answer details for AJAX requests."""
    from app.models.answer import Answer
    from app.utils.nlp_eval import evaluate_answer
    
    answer = Answer.query.get_or_404(answer_id)
    
    # If the answer doesn't have feedback yet, generate it now
    if not answer.feedback:
        current_app.logger.info(f"Auto-generating feedback for answer {answer_id}")
        try:
            evaluate_answer(answer.id)
            # Refresh the answer object after evaluation
            answer = Answer.query.get_or_404(answer_id)
        except Exception as e:
            current_app.logger.error(f"Error generating feedback: {e}")
    
    return jsonify({
        'id': answer.id,
        'text': answer.text,
        'score': answer.score,
        'completeness': answer.completeness,
        'relevance': answer.relevance,
        'structure': answer.structure,
        'grammar_score': answer.grammar_score,
        'sentiment_score': answer.sentiment_score,
        'feedback': answer.feedback,
        'grammar_issues': answer.grammar_issues,
        'improvement_suggestions': answer.improvement_suggestions,
        'created_at': answer.created_at.isoformat()
    })


@api_bp.route('/process_answer/<int:answer_id>', methods=['POST'])
def process_answer(answer_id):
    """API endpoint to trigger answer evaluation and get feedback."""
    from app.models.answer import Answer
    from app.utils.nlp_eval import evaluate_answer
    
    answer = Answer.query.get_or_404(answer_id)
    
    # Generate feedback
    try:
        evaluate_answer(answer.id)
        # Refresh the answer object after evaluation
        answer = Answer.query.get(answer_id)
        
        return jsonify({
            'success': True,
            'answer_id': answer.id,
            'feedback': answer.feedback,
            'score': answer.score,
            'has_feedback': answer.feedback is not None
        })
    except Exception as e:
        current_app.logger.error(f"Error processing answer: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500