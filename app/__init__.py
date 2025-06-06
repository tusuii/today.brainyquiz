from flask import Flask, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
import os
from app.config import config
from app.celery_config import make_celery

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
csrf = CSRFProtect()

# Initialize Celery
celery = None

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

def create_app(config_name='default'):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Set Celery configuration
    app.config.update(
        CELERY_BROKER_URL=os.environ.get('CELERY_BROKER_URL', 'amqp://guest:guest@localhost:5672//'),
        CELERY_RESULT_BACKEND=os.environ.get('CELERY_RESULT_BACKEND', 'rpc://')
    )
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize Celery
    global celery
    celery = make_celery(app)
    
    # Configure Flask-Login with stronger session handling
    login_manager.init_app(app)
    login_manager.session_protection = 'strong'
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Initialize CSRF protection
    csrf.init_app(app)
    
    # Register blueprints
    from app.routes.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from app.routes.quiz import quiz as quiz_blueprint
    app.register_blueprint(quiz_blueprint)
    
    from app.routes.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    from app.routes.api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')
    
    # Create a route for the home page
    @app.route('/')
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('quiz.list_quizzes'))
        return redirect(url_for('auth.login'))
    
    return app
