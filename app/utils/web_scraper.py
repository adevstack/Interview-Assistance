import trafilatura
import random
import re

# Default search URLs for job interviews
SEARCH_TEMPLATES = [
    "https://www.glassdoor.com/Interview/index.htm?filterType=INTERVIEW_ROLE&filterValue={role}",
    "https://www.interviewbit.com/search/?q={role}+interview+questions",
    "https://www.indeed.com/career-advice/interviewing/common-{role}-interview-questions",
]

# Fallback questions for when scraping fails
FALLBACK_QUESTIONS = {
    'technical': [
        "What are the key technical skills required for a {role} position?",
        "What tools or software are commonly used by professionals in the {role} field?",
        "What technical challenges do {role}s typically face in their daily work?",
        "How do you stay updated with the latest technologies and trends in the {role} field?",
        "Describe a technical project you worked on that's relevant to the {role} position."
    ],
    'behavioral': [
        "Describe a situation where you had to use skills relevant to a {role} position under pressure.",
        "Tell me about a time when you had to solve a complex problem related to {role} responsibilities.",
        "How have you handled conflict or disagreement in previous {role}-related projects?",
        "Describe a successful project you completed that demonstrates your abilities as a {role}.",
        "Tell me about a time when you had to adapt to changes in a {role}-related task or project."
    ],
    'situational': [
        "How would you handle a situation where you're given multiple urgent tasks as a {role}?",
        "What would you do if you disagreed with a colleague's approach to a {role}-related problem?",
        "How would you prioritize tasks if you had limited resources as a {role}?",
        "What would you do if a project deadline was moved up unexpectedly in your {role}?",
        "How would you handle receiving critical feedback about your work as a {role}?"
    ]
}


def clean_text(text):
    """Clean scraped text by removing extra whitespace, etc."""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters
    text = re.sub(r'[^\w\s.,?!-]', '', text)
    return text.strip()


def extract_questions(text, min_length=20, max_length=200):
    """Extract possible interview questions from scraped text."""
    if not text:
        return []
    
    # Split text into sentences
    sentences = re.split(r'[.!?]+', text)
    
    # Filter for potential questions
    questions = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        # Skip short or empty sentences
        if len(sentence) < min_length or len(sentence) > max_length:
            continue
            
        # Identify questions by keywords or question marks
        if (sentence.endswith('?') or 
            re.search(r'\b(describe|explain|tell me|how would you|what would you|how do you)\b', 
                     sentence.lower())):
            questions.append(sentence + ('?' if not sentence.endswith('?') else ''))
    
    return questions


def get_website_text_content(url):
    """
    This function takes a url and returns the main text content of the website.
    The text content is extracted using trafilatura.
    """
    try:
        # Send a request to the website
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        return text
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def scrape_interview_questions(role, category, num_questions=5):
    """
    Scrape interview questions for a specific role and category.
    
    Args:
        role (str): The job role to search for
        category (str): The category of questions (technical, behavioral, situational)
        num_questions (int): Number of questions to return
        
    Returns:
        list: List of questions for the role
    """
    # Format the role for URL
    formatted_role = role.lower().replace(' ', '-')
    
    all_questions = []
    
    # Try each search template
    for template in SEARCH_TEMPLATES:
        try:
            url = template.format(role=formatted_role)
            content = get_website_text_content(url)
            
            if content:
                # Extract possible questions from content
                questions = extract_questions(content)
                all_questions.extend(questions)
                
                # If we have enough questions, break
                if len(all_questions) >= num_questions * 2:  # Get extra for filtering
                    break
        except Exception as e:
            print(f"Error with template {template}: {e}")
            continue
    
    # Filter questions to make sure they're relevant to the category
    filtered_questions = []
    
    # Keywords for each category
    category_keywords = {
        'technical': ['how', 'what is', 'explain', 'describe', 'technical', 'skill', 'tool', 'technology', 'implement', 'develop'],
        'behavioral': ['time when', 'situation', 'example', 'challenge', 'conflict', 'team', 'leadership', 'problem', 'handled', 'managed'],
        'situational': ['would you', 'if you', 'scenario', 'hypothetical', 'how would', 'approach', 'faced with', 'strategy']
    }
    
    # Get keywords for the requested category
    keywords = category_keywords.get(category, [])
    
    for question in all_questions:
        # Check if the question contains any keywords for the category
        if any(keyword in question.lower() for keyword in keywords):
            filtered_questions.append(question)
    
    # If we don't have enough questions, use fallback
    if len(filtered_questions) < num_questions:
        fallback = FALLBACK_QUESTIONS.get(category, [])
        # Format the fallback questions with the role
        formatted_fallbacks = [q.format(role=role) for q in fallback]
        filtered_questions.extend(formatted_fallbacks)
    
    # Ensure we don't return more than requested
    if len(filtered_questions) > num_questions:
        filtered_questions = random.sample(filtered_questions, num_questions)
    
    return filtered_questions