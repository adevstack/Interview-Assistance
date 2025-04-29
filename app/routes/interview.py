from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from flask_login import login_required, current_user
from datetime import datetime

from app import db
from app.models.user import User
from app.models.interview import Interview, InterviewSession
from app.models.question import Question
from app.models.answer import Answer
from app.utils.interview_flow import get_interview_stages, generate_interview_title
from app.utils.nlp_eval import evaluate_answer

bp = Blueprint('interview', __name__, url_prefix='/interview')


@bp.route('/dashboard')
@login_required
def dashboard():
    # Get user's interviews
    interviews = Interview.query.filter_by(user_id=current_user.id).order_by(Interview.created_at.desc()).all()
    
    # Calculate statistics
    completed_interviews = sum(1 for i in interviews if i.status == 'completed')
    in_progress_interviews = sum(1 for i in interviews if i.status == 'in_progress')
    
    # Calculate average score
    total_score = sum(i.overall_score for i in interviews if i.overall_score is not None)
    avg_score = total_score / completed_interviews if completed_interviews > 0 else 0
    
    return render_template(
        'dashboard.html',
        interviews=interviews,
        stats={
            'total': len(interviews),
            'completed': completed_interviews,
            'in_progress': in_progress_interviews,
            'avg_score': round(avg_score, 2)
        }
    )


@bp.route('/new', methods=('GET', 'POST'))
@login_required
def new_interview():
    if request.method == 'POST':
        role = request.form['role']
        error = None

        if not role:
            error = 'Role selection is required.'

        if error is None:
            # Generate a title for the interview
            title = generate_interview_title(role)
            
            # Create new interview
            interview = Interview(
                user_id=current_user.id,
                title=title,
                role=role,
                status='in_progress'
            )
            db.session.add(interview)
            db.session.flush()  # To get the interview ID
            
            # Create sessions based on the role
            stages = get_interview_stages(role)
            for i, stage in enumerate(stages):
                session = InterviewSession(
                    interview_id=interview.id,
                    category=stage,
                    stage_order=i,
                    status='pending'
                )
                db.session.add(session)
            
            db.session.commit()
            flash('Interview created successfully!', 'success')
            return redirect(url_for('interview.start', interview_id=interview.id))

        flash(error, 'danger')
        return redirect(url_for('interview.dashboard'))

    # Available roles for interview
    roles = [
        {'id': 'software_engineer', 'name': 'Software Engineer'},
        {'id': 'data_scientist', 'name': 'Data Scientist'},
        {'id': 'product_manager', 'name': 'Product Manager'},
        {'id': 'hr', 'name': 'HR Professional'},
        {'id': 'marketing', 'name': 'Marketing Specialist'},
        {'id': 'sales', 'name': 'Sales Representative'},
        {'id': 'customer_support', 'name': 'Customer Support'},
        {'id': 'manager', 'name': 'Manager'}
    ]
    
    return render_template('new_interview.html', roles=roles)


@bp.route('/<int:interview_id>/start')
@login_required
def start(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    
    # Check if interview belongs to current user
    if interview.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('interview.dashboard'))
    
    # Get the next pending session
    next_session = InterviewSession.query.filter_by(
        interview_id=interview_id,
        status='pending'
    ).order_by(InterviewSession.stage_order).first()
    
    if next_session:
        return redirect(url_for('interview.session', interview_id=interview_id, session_id=next_session.id))
    
    # If no pending sessions, redirect to results
    flash('All interview sessions completed!', 'success')
    
    # Mark the interview as completed if it's not already
    if interview.status != 'completed':
        interview.complete_interview()
    
    return redirect(url_for('feedback.results', interview_id=interview_id))


@bp.route('/<int:interview_id>/session/<int:session_id>', methods=('GET', 'POST'))
@login_required
def session(interview_id, session_id):
    interview = Interview.query.get_or_404(interview_id)
    session = InterviewSession.query.get_or_404(session_id)
    
    # Check if interview belongs to current user
    if interview.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('interview.dashboard'))
    
    # Check if session belongs to the interview
    if session.interview_id != interview_id:
        flash('Invalid session for this interview.', 'danger')
        return redirect(url_for('interview.dashboard'))
    
    # Check if session is still pending, if so mark it as in_progress
    if session.status == 'pending':
        session.start_session()
        
        # Generate questions for this session if they don't exist
        if session.questions.count() == 0:
            from app.utils.interview_flow import generate_questions_for_session
            generate_questions_for_session(session)
    
    # Get current question
    current_question = Question.get_current_question(session_id)
    
    # If no more questions, mark session as completed and move to next session
    if not current_question:
        session.complete_session()
        
        # Find the next session
        next_session = InterviewSession.query.filter_by(
            interview_id=interview_id,
            status='pending'
        ).order_by(InterviewSession.stage_order).first()
        
        if next_session:
            return redirect(url_for('interview.session', interview_id=interview_id, session_id=next_session.id))
        else:
            # If no more sessions, mark interview as completed and show results
            interview.complete_interview()
            return redirect(url_for('feedback.results', interview_id=interview_id))
    
    # Handle form submission
    if request.method == 'POST':
        answer_text = request.form['answer']
        
        if not answer_text.strip():
            flash('Answer cannot be empty.', 'danger')
            return redirect(url_for('interview.session', interview_id=interview_id, session_id=session_id))
        
        # Create and save answer
        answer = Answer(
            session_id=session_id,
            question_id=current_question.id,
            text=answer_text
        )
        db.session.add(answer)
        db.session.commit()
        
        # Evaluate the answer asynchronously (in a real app, this would be a background task)
        # For now, we do it synchronously for simplicity
        evaluate_answer(answer.id)
        
        # Redirect to see instant feedback or continue to next question
        return redirect(url_for('feedback.answer', answer_id=answer.id))
    
    # Get all questions for progress display
    all_questions = Question.query.filter_by(session_id=session_id).order_by(Question.order).all()
    answered_questions = Answer.query.filter_by(session_id=session_id).count()
    progress = (answered_questions / len(all_questions)) * 100 if all_questions else 0
    
    # Get previous sessions for breadcrumb navigation
    previous_sessions = InterviewSession.query.filter_by(
        interview_id=interview_id,
        status='completed'
    ).order_by(InterviewSession.stage_order).all()
    
    return render_template(
        'interview.html',
        interview=interview,
        session=session,
        question=current_question,
        progress=progress,
        total_questions=len(all_questions),
        answered_questions=answered_questions,
        previous_sessions=previous_sessions
    )


@bp.route('/<int:interview_id>/cancel', methods=['POST'])
@login_required
def cancel_interview(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    
    # Check if interview belongs to current user
    if interview.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('interview.dashboard'))
    
    interview.status = 'abandoned'
    db.session.commit()
    
    flash('Interview has been canceled.', 'info')
    return redirect(url_for('interview.dashboard'))


@bp.route('/<int:interview_id>/delete', methods=['POST'])
@login_required
def delete_interview(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    
    # Check if interview belongs to current user
    if interview.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('interview.dashboard'))
    
    db.session.delete(interview)
    db.session.commit()
    
    flash('Interview has been deleted.', 'info')
    return redirect(url_for('interview.dashboard'))
