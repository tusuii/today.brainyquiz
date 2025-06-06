from app import create_app, db
from app.models import User, Quiz, Question, Option, UserQuiz, UserAnswer

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Add database models to flask shell context"""
    return {
        'db': db,
        'User': User,
        'Quiz': Quiz,
        'Question': Question,
        'Option': Option,
        'UserQuiz': UserQuiz,
        'UserAnswer': UserAnswer
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
