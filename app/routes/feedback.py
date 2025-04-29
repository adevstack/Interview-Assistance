from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from flask_login import login_required, current_user

from app import db
from app.models.interview import Interview, InterviewSession
from app.models.question import Question
from app.models.answer import Answer

bp = Blueprint('feedback', __name__, url_prefix='/feedback')


@bp.route('/answer/<int:answer_id>')
@login_required
def answer(answer_id):
    answer = Answer.query.get_or_404(answer_id)
    
    # Get the session and interview to check permissions
    session = InterviewSession.query.get(answer.session_id)
    interview = Interview.query.get(session.interview_id)
    
    # Check if interview belongs to current user
    if interview.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('interview.dashboard'))
    
    # Get the question
    question = Question.query.get(answer.question_id)
    
    # Check if there's another question in this session
    next_question = Question.get_current_question(session.id)
    
    return render_template(
        'feedback.html',
        answer=answer,
        question=question,
        session=session,
        interview=interview,
        has_next=next_question is not None
    )


@bp.route('/results/<int:interview_id>')
@login_required
def results(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    
    # Check if interview belongs to current user
    if interview.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('interview.dashboard'))
    
    # Get all sessions with their questions and answers
    sessions = InterviewSession.query.filter_by(interview_id=interview_id).order_by(InterviewSession.stage_order).all()
    
    # Prepare session data with questions and answers
    session_data = []
    for session in sessions:
        questions_with_answers = []
        questions = Question.query.filter_by(session_id=session.id).order_by(Question.order).all()
        
        for question in questions:
            answer = Answer.query.filter_by(question_id=question.id).first()
            questions_with_answers.append({
                'question': question,
                'answer': answer
            })
        
        session_data.append({
            'session': session,
            'questions': questions_with_answers,
            'avg_score': session.get_average_score()
        })
    
    # Calculate overall stats
    total_questions = sum(len(data['questions']) for data in session_data)
    total_answers = sum(sum(1 for qa in data['questions'] if qa['answer'] is not None) for data in session_data)
    
    # Calculate strengths and weaknesses
    answers = Answer.query.join(InterviewSession).filter(InterviewSession.interview_id == interview_id).all()
    
    # Organize scores by category
    category_scores = {}
    for answer in answers:
        if answer.score is not None:
            session = InterviewSession.query.get(answer.session_id)
            if session.category not in category_scores:
                category_scores[session.category] = []
            category_scores[session.category].append(answer.score)
    
    # Calculate average scores by category
    avg_category_scores = {
        category: sum(scores) / len(scores) 
        for category, scores in category_scores.items()
    }
    
    # Identify strengths and weaknesses
    strengths = sorted(avg_category_scores.items(), key=lambda x: x[1], reverse=True)[:2]
    weaknesses = sorted(avg_category_scores.items(), key=lambda x: x[1])[:2]
    
    return render_template(
        'results.html',
        interview=interview,
        session_data=session_data,
        stats={
            'total_questions': total_questions,
            'total_answers': total_answers,
            'completion_rate': (total_answers / total_questions * 100) if total_questions > 0 else 0
        },
        strengths=strengths,
        weaknesses=weaknesses
    )


@bp.route('/api/answer/<int:answer_id>')
@login_required
def api_answer(answer_id):
    """API endpoint to get answer details for AJAX requests."""
    answer = Answer.query.get_or_404(answer_id)
    
    # Get the session and interview to check permissions
    session = InterviewSession.query.get(answer.session_id)
    interview = Interview.query.get(session.interview_id)
    
    # Check if interview belongs to current user
    if interview.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Return answer data
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
        'improvement_suggestions': answer.improvement_suggestions
    })
