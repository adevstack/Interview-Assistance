import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_object('config.Config')
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    app.secret_key = os.environ.get("SESSION_SECRET", "dev-key-change-in-production")
    
    # Enable proxy fix for Cloudflare compatibility
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Initialize database
    db.init_app(app)

    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register custom template filters
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        """Convert newlines to <br> tags for HTML display"""
        if s is None:
            return ""
        return s.replace('\n', '<br>')

    # Create database tables
    with app.app_context():
        # Import models to register them with SQLAlchemy
        from app.models import user, interview, question, answer
        db.create_all()

    # Register blueprints
    from app.routes import auth, interview, feedback, api
    app.register_blueprint(auth.bp)
    app.register_blueprint(interview.bp)
    app.register_blueprint(feedback.bp)
    app.register_blueprint(api.api_bp)

    # Register a simple route for the index
    @app.route('/')
    def index():
        return auth.index()

    return app
