demo- https://interview-assistance.onrender.com 
# AI Interview Preparation Platform

An AI-powered interview preparation platform that provides personalized, role-specific interview training through advanced natural language processing and machine learning technologies.

## Features

- Role-specific interview questions and feedback
- Conversational chat interface
- Voice input with speech recognition
- Text-to-speech for interview questions
- Comprehensive answer evaluation and feedback
- Gemini AI integration for advanced analysis
- Web scraping for relevant interview questions
- Performance tracking and analytics

## Deployment to Cloudflare

### Environment Setup

To deploy this application to Cloudflare, you'll need to set these environment variables:

```
DATABASE_URL=<your-database-connection-string>
GEMINI_API_KEY=<your-gemini-api-key>
SESSION_SECRET=<your-session-secret>
FLASK_ENV=production
```

### Cloudflare Workers Deployment Steps

1. Fork or clone this GitHub repository
2. Connect your GitHub repository to Cloudflare Pages
3. Configure environment secrets in Cloudflare dashboard
4. Set up a Cloudflare D1 database or use an external PostgreSQL database
5. Deploy and enjoy!

## Local Development

1. Clone the repository
2. Install dependencies with `pip install -e .`
3. Set up environment variables
4. Run with `gunicorn --bind 0.0.0.0:5000 main:app`

## Tech Stack

- Flask web framework
- SQLAlchemy ORM
- Gemini AI
- NLTK and TextBlob for NLP
- Trafilatura for web scraping
- Web Speech API and Gemini for voice recognition
