from app import db
from datetime import datetime
from sqlalchemy import func


class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed, abandoned
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    overall_score = db.Column(db.Float, nullable=True)
    
    # Relationships
    sessions = db.relationship('InterviewSession', backref='interview', lazy='dynamic', cascade='all, delete-orphan')
    
    def calculate_overall_score(self):
        """Calculate the overall score based on session scores."""
        from app.models.answer import Answer
        
        answers = Answer.query.join(InterviewSession).filter(InterviewSession.interview_id == self.id).all()
        if not answers:
            return None
        
        total_score = sum(answer.score for answer in answers if answer.score is not None)
        return total_score / len(answers) if answers else None
    
    def complete_interview(self):
        """Mark the interview as completed and calculate final score."""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.overall_score = self.calculate_overall_score()
        db.session.commit()
    
    def get_progress(self):
        """Calculate the interview progress as a percentage."""
        total_sessions = self.sessions.count()
        if total_sessions == 0:
            return 0
        
        completed_sessions = self.sessions.filter_by(status='completed').count()
        return (completed_sessions / total_sessions) * 100
    
    def __repr__(self):
        return f'<Interview {self.title} for {self.role}>'


class InterviewSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interview.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # warmup, technical, behavioral, situational
    stage_order = db.Column(db.Integer, nullable=False)  # Order of the session in the interview
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    questions = db.relationship('Question', backref='session', lazy='dynamic', cascade='all, delete-orphan')
    answers = db.relationship('Answer', backref='session', lazy='dynamic', cascade='all, delete-orphan')
    
    def start_session(self):
        """Mark the session as in progress."""
        self.status = 'in_progress'
        self.started_at = datetime.utcnow()
        db.session.commit()
    
    def complete_session(self):
        """Mark the session as completed."""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        db.session.commit()
    
    def get_average_score(self):
        """Calculate the average score for this session."""
        avg_score = db.session.query(func.avg(Answer.score)).filter(Answer.session_id == self.id).scalar()
        return avg_score if avg_score is not None else 0
    
    def __repr__(self):
        return f'<Session {self.category} (Order: {self.stage_order})>'
