# Local Setup Guide for Windows

This guide will help you set up and run the AI Interview Preparation platform on your local Windows machine with VS Code.

## Step 1: Clone the Repository
Open Command Prompt or PowerShell:
```
git clone <your-github-repository-url>
cd <project-folder-name>
```

## Step 2: Set Up a Virtual Environment
```
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate
```
You should see `(venv)` at the beginning of your command prompt line.

## Step 3: Install Dependencies
```
pip install -e .
```
If you encounter any issues, try installing the specific packages:
```
pip install email-validator flask-login flask flask-sqlalchemy gunicorn psycopg2-binary flask-wtf nltk textblob language-tool-python trafilatura google-generativeai
```

## Step 4: Set Up Environment Variables
Create a `.env` file in your project root. In VS Code, right-click in the Explorer panel → New File → name it `.env`, then add:
```
DATABASE_URL=postgresql://username:password@hostname:port/database_name
GEMINI_API_KEY=your_gemini_api_key
SESSION_SECRET=your_session_secret
FLASK_ENV=development
```

## Step 5: Install and Configure PostgreSQL on Windows
1. Download and install PostgreSQL from the [official website](https://www.postgresql.org/download/windows/)
2. During installation, note your password and port (default is 5432)
3. After installation, you can use pgAdmin (included in the installation) to:
   - Create a new database for your project
   - Your DATABASE_URL will look like: `postgresql://postgres:yourpassword@localhost:5432/yourdatabasename`

## Step 6: Initialize the Database
Open Command Prompt in your project directory with the virtual environment activated:
```
python -c "from app import create_app; from app.models import *; app = create_app(); app.app_context().push(); from app import db; db.create_all()"
```

## Step 7: Download NLTK Data
```
python download_nltk_data.py
```

## Step 8: Run the Application
```
python run.py
```
Or if you prefer using a production-ready server (Waitress is a good option for Windows):
```
pip install waitress
waitress-serve --port=5000 main:app
```

## Step 9: Access the Application
Open your browser and go to: http://localhost:5000

## Windows-Specific Troubleshooting:

- **PostgreSQL issues**: If you have trouble connecting, make sure the PostgreSQL service is running. Check Windows Services (services.msc)

- **Environment variables**: Windows sometimes has issues with `.env` files. If needed, you can set environment variables directly in the terminal:
  ```
  set DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/yourdatabasename
  set GEMINI_API_KEY=your_key
  set SESSION_SECRET=your_secret
  set FLASK_ENV=development
  ```

- **Package issues**: If you get errors about missing packages, install them one by one with pip

- **Port in use**: If port 5000 is already in use, change to another port in run.py or use:
  ```
  python -c "from app import create_app; app = create_app(); app.run(host='0.0.0.0', port=8080, debug=True)"
  ```

## Managing Dependencies

If you make changes to the dependencies, you can update your virtual environment:
```
pip install -e .
```

## Accessing the Admin Interface

Once you've created a user account, you can access the admin interface at: http://localhost:5000/admin