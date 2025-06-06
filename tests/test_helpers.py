"""
Test helper functions for the exam application.
This module provides synchronous versions of Celery tasks for testing.
"""
from datetime import datetime
import logging
from app.models import UserQuiz, UserAnswer, Option, Question
from app import db


def process_quiz_submission_sync(user_quiz_id):
    """
    Synchronous version of the process_quiz_submission task for testing.
    
    Args:
        user_quiz_id: ID of the UserQuiz to process
    
    Returns:
        The updated UserQuiz instance
    """
    try:
        # Get the user quiz
        user_quiz = UserQuiz.query.get(user_quiz_id)
        if not user_quiz:
            logging.error(f"UserQuiz with ID {user_quiz_id} not found")
            return None
        
        # Get all questions for this quiz
        questions = Question.query.filter_by(quiz_id=user_quiz.quiz_id).all()
        total_questions = len(questions)
        
        if total_questions == 0:
            logging.warning(f"No questions found for quiz {user_quiz.quiz_id}")
            user_quiz.score = 0
            user_quiz.completed_at = datetime.utcnow()
            user_quiz.pending_completion = False
            db.session.commit()
            return user_quiz
        
        # Get user answers
        user_answers = UserAnswer.query.filter_by(user_quiz_id=user_quiz_id).all()
        
        # Calculate score
        correct_answers = 0
        for answer in user_answers:
            option = Option.query.get(answer.option_id)
            if option and option.is_correct:
                correct_answers += 1
        
        # Update user quiz
        user_quiz.score = correct_answers
        user_quiz.completed_at = datetime.utcnow()
        user_quiz.pending_completion = False
        db.session.commit()
        
        return user_quiz
        
    except Exception as e:
        logging.error(f"Error processing quiz submission: {str(e)}")
        raise


def generate_quiz_statistics_sync(quiz_id):
    """
    Synchronous version of the generate_quiz_statistics task for testing.
    
    Args:
        quiz_id: ID of the Quiz to generate statistics for
    
    Returns:
        Dictionary containing quiz statistics
    """
    try:
        # Get all completed user quizzes for this quiz
        user_quizzes = UserQuiz.query.filter(
            UserQuiz.quiz_id == quiz_id,
            UserQuiz.completed_at.isnot(None)
        ).all()
        
        if not user_quizzes:
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
        
        return stats
        
    except Exception as e:
        logging.error(f"Error generating quiz statistics: {str(e)}")
        raise
