from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from app import db
from app.models import User, Quiz, Question, Option, UserQuiz, UserAnswer
from app.services.quiz_loader import QuizLoader
from app.services.quiz_service import QuizService
from werkzeug.security import generate_password_hash
from datetime import datetime
import os
import logging

admin = Blueprint('admin', __name__)

# Admin access decorator
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return login_required(decorated_function)

@admin.route('/')
@admin_required
def index():
    """Admin dashboard"""
    quiz_count = Quiz.query.count()
    user_count = User.query.count()
    attempt_count = UserQuiz.query.count()
    
    return render_template('admin/index.html', 
                          quiz_count=quiz_count, 
                          user_count=user_count, 
                          attempt_count=attempt_count)

@admin.route('/analytics')
@admin_required
def analytics_dashboard():
    """Visual analytics dashboard"""
    return render_template('admin/analytics_dashboard.html')

@admin.route('/quizzes')
@admin_required
def list_quizzes():
    """List all quizzes for admin"""
    quizzes = Quiz.query.all()
    return render_template('admin/quizzes/list.html', quizzes=quizzes)

@admin.route('/quizzes/<int:quiz_id>')
@admin_required
def view_quiz(quiz_id):
    """View quiz details for admin"""
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    
    return render_template('admin/quizzes/view.html', quiz=quiz, questions=questions)

@admin.route('/quizzes/import', methods=['GET', 'POST'])
@admin_required
def import_quiz():
    """Import quiz from YAML file"""
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'quiz_file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['quiz_file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if not file.filename.endswith(('.yml', '.yaml')):
            flash('File must be a YAML file')
            return redirect(request.url)
        
        # Save the file temporarily
        import tempfile
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)
        
        try:
            # Load the quiz into the database
            quiz = QuizLoader.load_quiz_from_file(file_path)
            flash(f'Quiz "{quiz.title}" imported successfully')
            return redirect(url_for('admin.view_quiz', quiz_id=quiz.id))
        except Exception as e:
            flash(f'Error importing quiz: {str(e)}')
            return redirect(request.url)
        finally:
            # Clean up temporary file
            os.remove(file_path)
            os.rmdir(temp_dir)
    
    return render_template('admin/quizzes/import.html')

@admin.route('/quizzes/import-directory')
@admin_required
def import_directory():
    """Import all quizzes from the quizzes directory"""
    quizzes_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'quizzes')
    
    if not os.path.exists(quizzes_dir):
        flash('Quizzes directory not found')
        return redirect(url_for('admin.list_quizzes'))
    
    try:
        quizzes = QuizLoader.load_all_quizzes_from_directory(quizzes_dir)
        flash(f'Successfully imported {len(quizzes)} quizzes')
    except Exception as e:
        flash(f'Error importing quizzes: {str(e)}')
    
    return redirect(url_for('admin.list_quizzes'))

@admin.route('/quizzes/<int:quiz_id>/delete', methods=['POST'])
@admin_required
def delete_quiz(quiz_id):
    """Delete a quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    db.session.delete(quiz)
    db.session.commit()
    
    flash(f'Quiz "{quiz.title}" deleted successfully')
    return redirect(url_for('admin.list_quizzes'))

@admin.route('/quizzes/<int:quiz_id>/toggle-live', methods=['POST'])
@admin_required
def toggle_quiz_live(quiz_id):
    """Toggle the live status of a quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    try:
        # Toggle the is_live status
        quiz.is_live = not quiz.is_live
        db.session.commit()
        
        status = "published" if getattr(quiz, 'is_live', False) else "unpublished"
        flash(f'Quiz "{quiz.title}" {status} successfully')
    except Exception as e:
        db.session.rollback()
        flash(f'Error toggling quiz status: {str(e)}', 'error')
    
    # Redirect back to the referring page (either quiz list or quiz detail)
    return redirect(request.referrer or url_for('admin.list_quizzes'))

@admin.route('/quizzes/<int:quiz_id>/set-time-limit', methods=['POST'])
@admin_required
def set_time_limit(quiz_id):
    """Set the time limit for a quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    try:
        # Get time limit from form
        time_limit = request.form.get('time_limit', '')
        
        # Convert to integer or None if empty
        if time_limit.strip():
            time_limit = int(time_limit)
            if time_limit < 1 or time_limit > 180:
                raise ValueError("Time limit must be between 1 and 180 minutes")
        else:
            time_limit = None
        
        # Update quiz time limit
        quiz.time_limit = time_limit
        db.session.commit()
        
        if time_limit:
            flash(f'Time limit for "{quiz.title}" set to {time_limit} minutes')
        else:
            flash(f'Time limit for "{quiz.title}" removed')
    except ValueError as e:
        db.session.rollback()
        flash(f'Error setting time limit: {str(e)}')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating quiz: {str(e)}')
    
    return redirect(url_for('admin.view_quiz', quiz_id=quiz.id))

@admin.route('/users')
@admin_required
def list_users():
    """List all users for admin"""
    users = User.query.all()
    return render_template('admin/users/list.html', users=users)


@admin.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    """Add a new user"""
    # Generate CSRF token for the form
    csrf_token = generate_csrf()
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = 'is_admin' in request.form
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('admin/users/edit.html', user=None)
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('admin/users/edit.html', user=None)
        
        # Create new user
        user = User(
            username=username,
            email=email,
            is_admin=is_admin,
            created_at=datetime.utcnow()
        )
        user.password = password  # This will hash the password
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User {username} created successfully', 'success')
        return redirect(url_for('admin.list_users'))
    
    return render_template('admin/users/edit.html', user=None)

@admin.route('/users/<int:user_id>')
@admin_required
def view_user(user_id):
    """View user details for admin"""
    user = User.query.get_or_404(user_id)
    user_quizzes = UserQuiz.query.filter_by(user_id=user.id).all()
    
    return render_template('admin/users/view.html', user=user, user_quizzes=user_quizzes)


@admin.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit an existing user"""
    user = User.query.get_or_404(user_id)
    
    # Generate CSRF token for the form
    csrf_token = generate_csrf()
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = 'is_admin' in request.form
        
        # Check if username already exists (for a different user)
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            flash('Username already exists', 'danger')
            return render_template('admin/users/edit.html', user=user)
        
        # Check if email already exists (for a different user)
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user.id:
            flash('Email already exists', 'danger')
            return render_template('admin/users/edit.html', user=user)
        
        # Update user details
        user.username = username
        user.email = email
        
        # Only update password if provided
        if password:
            user.password = password  # This will hash the password
        
        # Don't allow removing admin status from yourself
        if user.id == current_user.id and user.is_admin and not is_admin:
            flash('You cannot remove your own admin status', 'danger')
        else:
            user.is_admin = is_admin
        
        db.session.commit()
        
        flash(f'User {username} updated successfully', 'success')
        return redirect(url_for('admin.view_user', user_id=user.id))
    
    return render_template('admin/users/edit.html', user=user)

@admin.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    """Toggle admin status for a user"""
    user = User.query.get_or_404(user_id)
    
    # Prevent removing admin status from yourself
    if user.id == current_user.id:
        flash('You cannot remove your own admin status')
        return redirect(url_for('admin.view_user', user_id=user.id))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    flash(f'Admin status for {user.username} {"enabled" if user.is_admin else "disabled"}')
    return redirect(url_for('admin.view_user', user_id=user.id))

@admin.route('/results')
@admin_required
def view_results():
    """View all quiz results"""
    # Get filter parameter
    quiz_filter = request.args.get('quiz_filter', type=int)
    
    # Query with filter if provided
    query = UserQuiz.query.filter(UserQuiz.completed_at.isnot(None))
    if quiz_filter:
        query = query.filter_by(quiz_id=quiz_filter)
    
    # Get all completed quiz attempts
    user_quizzes = query.order_by(UserQuiz.completed_at.desc()).all()
    
    # Get all quizzes for filter dropdown
    quizzes = Quiz.query.all()
    
    return render_template('admin/results.html', user_quizzes=user_quizzes, quizzes=quizzes)


@admin.route('/attempts/<int:attempt_id>')
@admin_required
def view_attempt(attempt_id):
    """View details of a specific quiz attempt"""
    user_quiz = UserQuiz.query.get_or_404(attempt_id)
    
    # Get all questions for this quiz
    questions = Question.query.filter_by(quiz_id=user_quiz.quiz_id).all()
    
    # Get user answers
    user_answers = UserAnswer.query.filter_by(user_quiz_id=user_quiz.id).all()
    
    # Create a dictionary of answers by question_id for easy lookup
    answers = {answer.question_id: answer for answer in user_answers}
    
    return render_template('admin/attempt_detail.html', 
                          user_quiz=user_quiz, 
                          questions=questions, 
                          answers=answers)
