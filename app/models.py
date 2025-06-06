from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    """User model for authentication and tracking quiz results"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_quizzes = db.relationship('UserQuiz', backref='user', lazy='dynamic')
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Quiz(db.Model):
    """Quiz model containing quiz metadata"""
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    # We'll handle the is_live column in a way that works even if the column doesn't exist yet
    # Using server_default ensures it works with existing records
    is_live = db.Column(db.Boolean, server_default='false', default=False)  # Controls visibility to regular users
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('Question', backref='quiz', lazy='dynamic', cascade='all, delete-orphan')
    user_quizzes = db.relationship('UserQuiz', backref='quiz', lazy='dynamic')
    
    # Property to safely get is_live status even if column doesn't exist
    @property
    def is_live_safe(self):
        try:
            return self.is_live
        except Exception:
            return False
    
    def __repr__(self):
        return f'<Quiz {self.title}>'

class Question(db.Model):
    """Question model for quiz questions"""
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    options = db.relationship('Option', backref='question', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Question {self.id}: {self.text[:20]}...>'

class Option(db.Model):
    """Option model for question choices"""
    __tablename__ = 'options'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Option {self.id}: {self.text[:20]}...>'

class UserQuiz(db.Model):
    """UserQuiz model for tracking quiz attempts"""
    __tablename__ = 'user_quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_answers = db.relationship('UserAnswer', backref='user_quiz', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<UserQuiz {self.id}: User {self.user_id} - Quiz {self.quiz_id}>'

class UserAnswer(db.Model):
    """UserAnswer model for tracking individual answers"""
    __tablename__ = 'user_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_quiz_id = db.Column(db.Integer, db.ForeignKey('user_quizzes.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('options.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    question = db.relationship('Question')
    option = db.relationship('Option')
    
    def __repr__(self):
        return f'<UserAnswer {self.id}: UserQuiz {self.user_quiz_id} - Question {self.question_id}>'
