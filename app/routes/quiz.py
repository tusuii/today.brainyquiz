from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, session
from flask_login import login_required, current_user
from app import db
from app.models import Quiz, Question, Option, UserQuiz, UserAnswer, User
from app.services.quiz_service import QuizService
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

quiz = Blueprint('quiz', __name__)

@quiz.route('/quizzes')
@login_required
def list_quizzes():
    """Display a list of available quizzes"""
    # Debug authentication status
    logging.debug(f"User authenticated: {current_user.is_authenticated}")
    logging.debug(f"User ID: {current_user.id}")
    logging.debug(f"User name: {current_user.username}")
    logging.debug(f"Session data: {session}")
    
    # Verify user exists in database
    user_in_db = User.query.get(current_user.id)
    logging.debug(f"User found in database: {user_in_db is not None}")
    
    # For admin users, show all quizzes. For regular users, only show live quizzes
    quizzes = Quiz.query.all()
    
    # If not admin, filter out quizzes that aren't live
    if not current_user.is_admin:
        quizzes = [quiz for quiz in quizzes if quiz.is_live_safe]
    
    logging.debug(f"Found {len(quizzes)} quizzes")
    
    return render_template('quiz/list.html', quizzes=quizzes, user=current_user)

@quiz.route('/quizzes/<int:quiz_id>')
@login_required
def view_quiz(quiz_id):
    """Display details of a specific quiz"""
    quiz = QuizService.get_quiz_by_id(quiz_id)
    if not quiz:
        flash('Quiz not found.')
        return redirect(url_for('quiz.list_quizzes'))
    
    return render_template('quiz/view.html', quiz=quiz)

@quiz.route('/quizzes/<int:quiz_id>/start')
@login_required
def start_quiz(quiz_id):
    """Start a new quiz attempt"""
    logging.debug(f"Starting quiz with ID: {quiz_id} for user: {current_user.username} (ID: {current_user.id})")
    user_quiz = QuizService.start_quiz(current_user, quiz_id)
    
    if not user_quiz:
        logging.error(f"Failed to start quiz {quiz_id} - quiz not found or error in QuizService")
        flash('Quiz not found.')
        return redirect(url_for('quiz.list_quizzes'))
    
    logging.debug(f"Successfully started quiz. Created UserQuiz with ID: {user_quiz.id}")
    logging.debug(f"Redirecting to take_quiz with user_quiz_id: {user_quiz.id}")
    return redirect(url_for('quiz.take_quiz', user_quiz_id=user_quiz.id))

@quiz.route('/quiz/<int:user_quiz_id>')
@login_required
def take_quiz(user_quiz_id):
    """Take a quiz"""
    logging.debug(f"Accessing take_quiz with user_quiz_id: {user_quiz_id}")
    user_quiz = UserQuiz.query.get(user_quiz_id)
    
    # Check if the quiz belongs to the current user
    if not user_quiz:
        logging.error(f"UserQuiz with ID {user_quiz_id} not found")
        flash('Quiz attempt not found.')
        return redirect(url_for('quiz.list_quizzes'))
    
    if user_quiz.user_id != current_user.id:
        logging.error(f"UserQuiz {user_quiz_id} belongs to user {user_quiz.user_id}, not current user {current_user.id}")
        flash('Quiz attempt not found.')
        return redirect(url_for('quiz.list_quizzes'))
    
    # Check if the quiz is already completed
    if user_quiz.completed_at:
        logging.debug(f"Quiz {user_quiz_id} already completed at {user_quiz.completed_at}")
        return redirect(url_for('quiz.quiz_result', user_quiz_id=user_quiz.id))
    
    # Get all questions for this quiz
    quiz = user_quiz.quiz
    logging.debug(f"Found quiz: {quiz.title} (ID: {quiz.id})")
    
    # Check if time limit has been exceeded for quizzes with a time limit
    if quiz.time_limit:
        from datetime import datetime, timedelta
        time_limit_seconds = quiz.time_limit * 60
        
        # Check if started_at attribute exists, use created_at as fallback
        if hasattr(user_quiz, 'started_at'):
            start_time = user_quiz.started_at
        else:
            # Fallback to created_at if started_at doesn't exist
            logging.warning("UserQuiz.started_at attribute not found, using created_at instead")
            start_time = user_quiz.created_at
        
        time_elapsed = datetime.utcnow() - start_time
        logging.debug(f"Time elapsed: {time_elapsed}, Time limit: {time_limit_seconds} seconds")
        
        # If time limit exceeded, auto-submit the quiz
        if time_elapsed > timedelta(seconds=time_limit_seconds):
            logging.debug(f"Time limit exceeded for quiz {user_quiz_id}")
            flash('Time limit exceeded. Your quiz has been automatically submitted.', 'warning')
            
            # Complete the quiz with current answers
            QuizService.complete_quiz(user_quiz.id)
            return redirect(url_for('quiz.quiz_result', user_quiz_id=user_quiz.id))
    
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    logging.debug(f"Found {len(questions)} questions for quiz {quiz.id}")
    
    # Get user's answers so far
    user_answers = {}
    for answer in UserAnswer.query.filter_by(user_quiz_id=user_quiz.id).all():
        user_answers[answer.question_id] = answer.option_id
    logging.debug(f"Found {len(user_answers)} existing answers for user_quiz {user_quiz_id}")
    
    logging.debug(f"Rendering take.html template for quiz {quiz.id}")
    return render_template('quiz/take.html', 
                          user_quiz=user_quiz, 
                          quiz=quiz, 
                          questions=questions, 
                          user_answers=user_answers)

@quiz.route('/quiz/<int:user_quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(user_quiz_id):
    """Submit answers for a quiz"""
    user_quiz = UserQuiz.query.get(user_quiz_id)
    
    # Check if the quiz belongs to the current user
    if not user_quiz or user_quiz.user_id != current_user.id:
        flash('Quiz attempt not found.')
        return redirect(url_for('quiz.list_quizzes'))
    
    # Check if the quiz is already completed
    if user_quiz.completed_at:
        return redirect(url_for('quiz.quiz_result', user_quiz_id=user_quiz.id))
    
    # Check if time limit has been exceeded
    quiz = user_quiz.quiz
    if quiz.time_limit:
        from datetime import datetime, timedelta
        time_limit_seconds = quiz.time_limit * 60
        
        # Check if started_at attribute exists, use created_at as fallback
        if hasattr(user_quiz, 'started_at'):
            start_time = user_quiz.started_at
        else:
            # Fallback to created_at if started_at doesn't exist
            logging.debug("UserQuiz.started_at attribute not found in submit_quiz, using created_at instead")
            start_time = user_quiz.created_at
            
        time_elapsed = datetime.utcnow() - start_time
        
        # If time limit exceeded, add a message
        if time_elapsed > timedelta(seconds=time_limit_seconds):
            flash('Time limit exceeded. Your answers have been automatically submitted.', 'warning')
    
    # Process submitted answers
    for key, value in request.form.items():
        if key.startswith('question_'):
            try:
                question_id = int(key.split('_')[1])
                option_id = int(value)
                QuizService.submit_answer(user_quiz.id, question_id, option_id)
            except (ValueError, IndexError):
                continue
    
    # Complete the quiz and queue for asynchronous processing
    result = QuizService.complete_quiz(user_quiz.id)
    
    if result:
        flash('Your quiz has been submitted and is being processed.', 'info')
    else:
        flash('There was an issue submitting your quiz. Please try again.', 'danger')
    
    return redirect(url_for('quiz.quiz_result', user_quiz_id=user_quiz.id))

@quiz.route('/quiz/<int:user_quiz_id>/result')
@login_required
def quiz_result(user_quiz_id):
    """Display quiz results"""
    user_quiz = UserQuiz.query.get(user_quiz_id)
    
    # Check if the quiz belongs to the current user
    if not user_quiz or user_quiz.user_id != current_user.id:
        flash('Quiz attempt not found.')
        return redirect(url_for('quiz.list_quizzes'))
    
    # Get all questions for this quiz
    quiz = user_quiz.quiz
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    
    # Get user's answers
    user_answers = {}
    for answer in UserAnswer.query.filter_by(user_quiz_id=user_quiz.id).all():
        user_answers[answer.question_id] = answer.option_id
    
    # Get correct answers
    correct_answers = {}
    for question in questions:
        for option in question.options:
            if option.is_correct:
                correct_answers[question.id] = option.id
                break
    
    # Check if the quiz is still being processed
    processing = user_quiz.pending_completion and not user_quiz.completed_at
    
    return render_template('quiz/result.html', 
                          user_quiz=user_quiz, 
                          quiz=quiz, 
                          questions=questions, 
                          user_answers=user_answers,
                          correct_answers=correct_answers,
                          processing=processing)

# API endpoints for AJAX requests
@quiz.route('/api/quizzes')
@login_required
def api_list_quizzes():
    """API endpoint to get all quizzes"""
    quizzes = QuizService.get_all_quizzes()
    return jsonify([{
        'id': q.id,
        'title': q.title,
        'description': q.description,
        'question_count': q.questions.count()
    } for q in quizzes])

@quiz.route('/api/quizzes/<int:quiz_id>')
@login_required
def api_get_quiz(quiz_id):
    """API endpoint to get a specific quiz"""
    quiz = QuizService.get_quiz_by_id(quiz_id)
    if not quiz:
        return jsonify({'error': 'Quiz not found'}), 404
    
    return jsonify({
        'id': quiz.id,
        'title': quiz.title,
        'description': quiz.description,
        'questions': [{
            'id': q.id,
            'text': q.text,
            'options': [{
                'id': o.id,
                'text': o.text
            } for o in q.options]
        } for q in quiz.questions]
    })

@quiz.route('/api/quiz/<int:user_quiz_id>/submit-answer', methods=['POST'])
@login_required
def api_submit_answer(user_quiz_id):
    """API endpoint to submit an answer for a question"""
    data = request.json
    if not data or 'question_id' not in data or 'option_id' not in data:
        return jsonify({'error': 'Invalid data'}), 400
    
    user_quiz = UserQuiz.query.get(user_quiz_id)
    if not user_quiz or user_quiz.user_id != current_user.id:
        return jsonify({'error': 'Quiz attempt not found'}), 404
    
    if user_quiz.completed_at:
        return jsonify({'error': 'Quiz already completed'}), 400
    
    question_id = data['question_id']
    option_id = data['option_id']
    
    user_answer = QuizService.submit_answer(user_quiz.id, question_id, option_id)
    if not user_answer:
        return jsonify({'error': 'Invalid question or option'}), 400
    
    return jsonify({'success': True})
