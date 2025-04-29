import random
from datetime import datetime
from app import db
from app.models.question import Question
from app.utils.web_scraper import scrape_interview_questions

# Define interview stages for different roles
INTERVIEW_STAGES = {
    'software_engineer': ['warmup', 'technical', 'behavioral'],
    'data_scientist': ['warmup', 'technical', 'behavioral'],
    'product_manager': ['warmup', 'behavioral', 'situational'],
    'hr': ['warmup', 'behavioral', 'situational'],
    'marketing': ['warmup', 'behavioral', 'situational'],
    'sales': ['warmup', 'behavioral', 'situational'],
    'customer_support': ['warmup', 'behavioral', 'situational'],
    'manager': ['warmup', 'behavioral', 'situational'],
    # Default for any other role
    'default': ['warmup', 'technical', 'behavioral', 'situational']
}

# Sample questions for each category and role
QUESTIONS = {
    'warmup': {
        'common': [
            "Tell me a little about yourself and your background.",
            "What interests you about this role?",
            "What are your career goals for the next 3-5 years?",
            "Why are you looking to leave your current position?",
            "How did you hear about this opportunity?"
        ]
    },
    'technical': {
        'software_engineer': [
            "What programming languages are you most comfortable with and why?",
            "Explain the concept of object-oriented programming.",
            "How would you optimize a slow SQL query?",
            "Describe the difference between a stack and a queue.",
            "What is the time complexity of binary search?",
            "Explain the concept of RESTful APIs.",
            "How do you handle error cases in your code?",
            "Describe a challenging technical problem you solved recently."
        ],
        'data_scientist': [
            "Explain the difference between supervised and unsupervised learning.",
            "How would you handle missing data in a dataset?",
            "Describe overfitting and how to prevent it.",
            "What evaluation metrics do you use for classification problems?",
            "Explain the concept of feature engineering.",
            "How would you approach a time series forecasting problem?",
            "Describe the trade-off between bias and variance.",
            "What is the difference between correlation and causation?"
        ],
        'default': [
            "What technical skills do you have that are relevant to this role?",
            "Describe your experience with industry-specific tools or platforms.",
            "How do you stay updated with the latest technologies in your field?",
            "What technical challenges have you faced in your previous roles?",
            "How do you approach learning new technical skills?"
        ]
    },
    'behavioral': {
        'common': [
            "Describe a situation where you had to work under pressure to meet a deadline.",
            "Tell me about a time when you had to resolve a conflict with a colleague.",
            "Describe a project that you're particularly proud of.",
            "Tell me about a time when you faced a significant challenge at work.",
            "Describe a situation where you had to adapt to a significant change.",
            "Tell me about a time when you failed. How did you handle it?",
            "Describe a situation where you had to persuade others to your point of view.",
            "Tell me about a time when you went above and beyond what was expected."
        ],
        'manager': [
            "Describe your management style.",
            "Tell me about a time when you had to give difficult feedback to a team member.",
            "How do you motivate your team during challenging periods?",
            "Describe a situation where you had to resolve a conflict between team members.",
            "How do you prioritize and allocate resources in your team?",
            "Tell me about a time when you had to make a difficult decision that affected your team."
        ]
    },
    'situational': {
        'common': [
            "How would you handle a situation where you're given multiple urgent tasks with conflicting deadlines?",
            "What would you do if you strongly disagreed with your manager's decision?",
            "How would you approach working with a difficult team member?",
            "What would you do if you noticed a colleague was struggling with their workload?",
            "How would you handle receiving critical feedback from a peer?",
            "What would you do if you made a significant mistake that impacted your team?",
            "How would you approach a new project with unclear requirements?",
            "How would you handle a situation where you need to deliver bad news to a client or stakeholder?"
        ]
    }
}


def get_interview_stages(role):
    """Get the interview stages for a specific role."""
    return INTERVIEW_STAGES.get(role, INTERVIEW_STAGES['default'])


def generate_interview_title(role):
    """Generate a title for a new interview."""
    date_str = datetime.now().strftime("%b %d, %Y")
    return f"{role.replace('_', ' ').title()} Interview - {date_str}"


def get_questions_for_category(category, role, num_questions=5):
    """Get a set of questions for a specific category and role."""
    # Check if this is a custom role (not in predefined list)
    if role not in INTERVIEW_STAGES:
        # First try using OpenAI to generate role-specific questions
        from app.utils.openai_integration import generate_interview_questions as openai_generate_questions, is_openai_available
        from app.utils.gemini_integration import generate_interview_questions as gemini_generate_questions, is_gemini_available
        
        # Try OpenAI first
        if is_openai_available():
            ai_questions = openai_generate_questions(role, category, num_questions)
            if ai_questions and len(ai_questions) >= 3:  # Ensure we have at least 3 questions
                print(f"Using OpenAI-generated questions for {role}")
                return ai_questions
        
        # If OpenAI fails or unavailable, try Gemini
        if is_gemini_available():
            ai_questions = gemini_generate_questions(role, category, num_questions)
            if ai_questions and len(ai_questions) >= 3:  # Ensure we have at least 3 questions
                print(f"Using Gemini-generated questions for {role}")
                return ai_questions
        
        try:
            # If AI not available, try to scrape questions for this custom role
            scraped_questions = scrape_interview_questions(role, category, num_questions)
            if scraped_questions and len(scraped_questions) >= 3:  # Ensure we have at least 3 questions
                print(f"Using web-scraped questions for {role}")
                return scraped_questions
        except Exception as e:
            print(f"Error scraping questions for {role}: {e}")
            # Fall back to default questions
            pass
    
    # Get role-specific questions if they exist
    role_questions = QUESTIONS.get(category, {}).get(role, [])
    
    # Get common questions for the category
    common_questions = QUESTIONS.get(category, {}).get('common', [])
    
    # If no role-specific questions, try default
    if not role_questions and category in QUESTIONS:
        role_questions = QUESTIONS[category].get('default', [])
    
    # Combine questions
    all_questions = role_questions + common_questions
    
    # Ensure we don't request more questions than available
    num_to_select = min(num_questions, len(all_questions))
    
    # Randomly select questions
    selected_questions = random.sample(all_questions, num_to_select)
    
    return selected_questions


def generate_questions_for_session(session, num_questions=5):
    """Generate questions for an interview session."""
    from app.models.interview import Interview
    
    # Get the interview for this session
    interview = Interview.query.get(session.interview_id)
    
    # Get questions for this category and role
    question_texts = get_questions_for_category(session.category, interview.role, num_questions)
    
    # Create Question objects
    for i, text in enumerate(question_texts):
        question = Question(
            session_id=session.id,
            text=text,
            category=session.category,
            difficulty='medium',  # Default difficulty
            order=i
        )
        db.session.add(question)
    
    db.session.commit()
    
    return len(question_texts)
