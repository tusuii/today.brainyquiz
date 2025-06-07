"""
Celery tasks for the exam application.
This module defines background tasks to be processed by Celery workers.
"""
import logging
from app import celery, db
from app.models import Quiz, Question, Option, User, UserQuiz, UserAnswer
from datetime import datetime
import time

@celery.task(name='app.tasks.process_quiz_submission')
def process_quiz_submission(user_quiz_id):
    """
    Process a quiz submission asynchronously.
    
    This task handles the calculation of quiz results and updates the database
    without blocking the web server during high traffic loads.
    
    Args:
        user_quiz_id: ID of the UserQuiz to process
    """
    try:
        logging.info(f"Processing quiz submission for UserQuiz ID: {user_quiz_id}")
        
        # No artificial delay needed in production
        
        # Get the user quiz
        user_quiz = UserQuiz.query.get(user_quiz_id)
        if not user_quiz:
            logging.error(f"UserQuiz with ID {user_quiz_id} not found")
            return
        
        # Skip if already completed
        if user_quiz.completed_at:
            logging.info(f"UserQuiz {user_quiz_id} already processed")
            return
            
        # Get all questions for this quiz - use eager loading to reduce queries
        quiz = Quiz.query.get(user_quiz.quiz_id)
        questions = Question.query.filter_by(quiz_id=quiz.id).all()
        
        # Get user answers with a single query - eager load related data
        user_answers = UserAnswer.query.filter_by(user_quiz_id=user_quiz.id).all()
        
        # Calculate score
        total_questions = len(questions)
        correct_answers = 0
        
        # Optimize by fetching all correct options in a single query
        correct_options = {opt.question_id: opt.id for opt in 
                          Option.query.filter(Option.question_id.in_([q.id for q in questions]), 
                                             Option.is_correct == True).all()}
        
        # Process answers without additional database queries
        for answer in user_answers:
            correct_option_id = correct_options.get(answer.question_id)
            if correct_option_id and answer.option_id == correct_option_id:
                correct_answers += 1
        
        # Calculate percentage score
        score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # Update user quiz record
        user_quiz.score = score_percentage
        user_quiz.completed_at = datetime.utcnow()
        
        # Commit changes to database
        db.session.commit()
        
        logging.info(f"Quiz {user_quiz_id} processed successfully. Score: {score_percentage:.2f}%")
        return score_percentage
        
    except Exception as e:
        logging.error(f"Error processing quiz submission: {str(e)}")
        # Ensure the session is rolled back in case of error
        db.session.rollback()
        raise

@celery.task(name='app.tasks.generate_quiz_statistics')
def generate_quiz_statistics(quiz_id):
    """
    Generate statistics for a quiz asynchronously.
    
    This task computes statistics about quiz performance across all users
    who have taken the quiz.
    
    Args:
        quiz_id: ID of the Quiz to analyze
    """
    try:
        logging.info(f"Generating statistics for Quiz ID: {quiz_id}")
        
        # No artificial delay needed in production
        
        # Get all completed user quizzes for this quiz
        user_quizzes = UserQuiz.query.filter(
            UserQuiz.quiz_id == quiz_id,
            UserQuiz.completed_at.isnot(None)
        ).all()
        
        if not user_quizzes:
            logging.info(f"No completed quizzes found for Quiz ID {quiz_id}")
            return {
                'quiz_id': quiz_id,
                'total_attempts': 0,
                'average_score': 0,
                'completion_rate': 0
            }
        
        # Calculate statistics
        total_attempts = len(user_quizzes)
        total_score = sum(uq.score for uq in user_quizzes if uq.score is not None)
        average_score = total_score / total_attempts if total_attempts > 0 else 0
        
        # Get all started quizzes (including incomplete)
        all_started = UserQuiz.query.filter_by(quiz_id=quiz_id).count()
        completion_rate = (total_attempts / all_started * 100) if all_started > 0 else 0
        
        stats = {
            'quiz_id': quiz_id,
            'total_attempts': total_attempts,
            'average_score': average_score,
            'completion_rate': completion_rate
        }
        
        logging.info(f"Statistics generated for Quiz ID {quiz_id}: {stats}")
        return stats
        
    except Exception as e:
        logging.error(f"Error generating quiz statistics: {str(e)}")
        raise
