"""
Test configuration for the exam application.
This file contains pytest fixtures and configuration for testing.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Set test environment variables before importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['CELERY_BROKER_URL'] = 'memory://'
os.environ['CELERY_RESULT_BACKEND'] = 'rpc://'

# Mock the Celery tasks module before importing app
sys.modules['app.tasks'] = __import__('tests.mock_tasks', fromlist=['*'])

# Import app and models
from app import create_app, db as _db
from app.models import User, Quiz, Question, Option, UserQuiz, UserAnswer

# Import our mock tasks
from tests.mock_tasks import process_quiz_submission, generate_quiz_statistics

@pytest.fixture(scope='session')
def app():
    """Create and configure a Flask app for testing."""
    # Ensure we're using SQLite in-memory database for testing
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SERVER_NAME': 'localhost.localdomain',
    })
    
    # Create application context
    with app.app_context():
        yield app


@pytest.fixture(scope='session')
def db(app):
    """Create and configure a database for testing."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def session(db):
    """Create a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    # Use SQLAlchemy's scoped_session directly
    from sqlalchemy.orm import scoped_session, sessionmaker
    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)
    
    # Replace the db session with our test session
    old_session = db.session
    db.session = session
    
    yield session
    
    # Clean up
    transaction.rollback()
    connection.close()
    session.remove()
    db.session = old_session


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def authenticated_client(app, client, test_user):
    """Create an authenticated test client."""
    # Use Flask's test client to login
    with client.session_transaction() as sess:
        # Flask-Login uses '_user_id' as the session key
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
    
    # Make a request to the app to ensure the session is saved
    # Use follow_redirects=True to handle any redirects
    client.get('/', follow_redirects=True)
    
    return client


@pytest.fixture
def test_user(session):
    """Create a test user."""
    user = User(
        username='testuser',
        email='test@example.com'
    )
    user.password = 'password123'  # Using the password property setter
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def test_quiz(session):
    """Create a test quiz."""
    quiz = Quiz(
        title='Test Quiz',
        description='A quiz for testing',
        is_live=True,  # Make the quiz visible to regular users
        time_limit=10  # 10 minutes
    )
    session.add(quiz)
    session.flush()
    
    # Create questions
    questions = []
    for i in range(3):
        question = Question(
            quiz_id=quiz.id,
            text=f'Test Question {i+1}'
        )
        session.add(question)
        session.flush()
        questions.append(question)
        
        # Create options for each question (1 correct, 3 incorrect)
        for j in range(4):
            option = Option(
                question_id=question.id,
                text=f'Option {j+1} for Question {i+1}',
                is_correct=(j == 0)  # First option is correct
            )
            session.add(option)
    
    session.commit()
    return quiz


@pytest.fixture
def mock_celery_task():
    """Mock Celery tasks for testing.
    
    This fixture returns the mocks without executing the task functions,
    allowing tests to verify that tasks are queued correctly.
    """
    # Since we're using apply_async in the service, we need to mock it directly
    # We'll use a simpler approach by just mocking the task objects themselves
    with patch('app.services.quiz_service.process_quiz_submission') as mock_process:
        with patch('app.services.quiz_service.generate_quiz_statistics') as mock_stats:
            # Configure the mocks to have apply_async method
            mock_process.apply_async = MagicMock()
            mock_stats.apply_async = MagicMock()
            
            # Return the mocks without executing the task functions
            # This allows tests to verify that tasks are queued correctly
            yield (mock_process, mock_stats)
