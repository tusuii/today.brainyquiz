from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import generate_csrf
from app import db
from app.models import User
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

auth = Blueprint('auth', __name__)

@auth.route('/test')
def test_auth():
    """Test route to verify authentication"""
    if current_user.is_authenticated:
        logging.debug(f"Test route accessed by user: {current_user.username}")
    else:
        logging.debug("Test route accessed by anonymous user")
    
    # Convert session to a readable format
    session_data = dict(session)
    
    return render_template('test_auth.html', session_data=session_data)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Generate CSRF token for the form
    csrf_token = generate_csrf()
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Login attempt: username={username}")
        
        user = User.query.filter_by(username=username).first()
        if user is None:
            print(f"User not found: {username}")
            flash('Invalid username or password.')
            return render_template('auth/login.html')
            
        if not user.verify_password(password):
            print(f"Invalid password for user: {username}")
            flash('Invalid username or password.')
            return render_template('auth/login.html')
            
        print(f"Login successful for user: {username}")
        # Set session to permanent and login the user
        session.permanent = True
        login_user(user, remember=True)
        
        # Force session to be saved
        session['user_id'] = user.id
        session['_fresh'] = True
        
        next_page = request.args.get('next')
        if next_page is None or not next_page.startswith('/'):
            next_page = url_for('quiz.list_quizzes')  # Redirect directly to quiz list
        
        print(f"Redirecting to: {next_page}")
        return redirect(next_page)
    
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Generate CSRF token for the form
    csrf_token = generate_csrf()
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.password = password
        
        # Make the first user an admin
        if User.query.count() == 0:
            user.is_admin = True
        
        db.session.add(user)
        db.session.commit()
        
        flash('You have been registered successfully. Please log in.')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')
