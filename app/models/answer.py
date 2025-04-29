from app import db
from datetime import datetime


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_session.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Feedback metrics
    score = db.Column(db.Float, nullable=True)  # Overall score (0-100)
    completeness = db.Column(db.Float, nullable=True)  # Completeness score (0-100)
    relevance = db.Column(db.Float, nullable=True)  # Relevance score (0-100)
    structure = db.Column(db.Float, nullable=True)  # Structure score (0-100)
    grammar_score = db.Column(db.Float, nullable=True)  # Grammar score (0-100)
    sentiment_score = db.Column(db.Float, nullable=True)  # Sentiment score (-1 to 1)
    
    # Feedback text
    feedback = db.Column(db.Text, nullable=True)
    grammar_issues = db.Column(db.Text, nullable=True)
    improvement_suggestions = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Answer {self.id} for Question {self.question_id}>'
    
    def calculate_overall_score(self):
        """Calculate overall score based on individual metrics."""
        if all(metric is not None for metric in [self.completeness, self.relevance, self.structure, self.grammar_score]):
            # Convert sentiment from -1:1 to 0:100 scale for inclusion in overall score
            sentiment_normalized = ((self.sentiment_score + 1) / 2) * 100 if self.sentiment_score is not None else 50
            
            # Weighted average of all metrics
            self.score = (
                (self.completeness * 0.25) +
                (self.relevance * 0.3) +
                (self.structure * 0.2) +
                (self.grammar_score * 0.15) +
                (sentiment_normalized * 0.1)
            )
            db.session.commit()
            return self.score
        return None
