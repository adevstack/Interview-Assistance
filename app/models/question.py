from app import db
from datetime import datetime


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_session.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # warmup, technical, behavioral, situational
    difficulty = db.Column(db.String(20), nullable=False, default='medium')  # easy, medium, hard
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order = db.Column(db.Integer, nullable=False)  # Question order in the session
    
    # Relationships
    answer = db.relationship('Answer', backref='question', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Question {self.id}: {self.text[:30]}...>'

    @staticmethod
    def get_questions_for_session(session_id, limit=5):
        """Get a specified number of questions for a session."""
        return Question.query.filter_by(session_id=session_id).order_by(Question.order).limit(limit).all()
    
    @staticmethod
    def get_current_question(session_id):
        """Get the current unanswered question for a session."""
        from app.models.answer import Answer
        
        # Find questions that don't have answers yet
        subquery = db.session.query(Answer.question_id).filter(Answer.session_id == session_id)
        question = Question.query.filter(
            Question.session_id == session_id,
            ~Question.id.in_(subquery)
        ).order_by(Question.order).first()
        
        return question
