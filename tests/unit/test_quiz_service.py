"""
Unit tests for the QuizService class.
"""
import pytest
from datetime import datetime
from app.services.quiz_service import QuizService
from app.models import UserQuiz, UserAnswer, Option


def test_complete_quiz_async(app, session, test_user, test_quiz, mock_celery_task):
    """Test that complete_quiz performs immediate scoring and queues statistics task."""
    # Create a user quiz
    user_quiz = UserQuiz(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        created_at=datetime.utcnow()
    )
    session.add(user_quiz)
    session.commit()
    
    # Get the mocked task
    mock_process, mock_stats = mock_celery_task
    
    # Call the complete_quiz method
    result = QuizService.complete_quiz(user_quiz.id)
    
    # Verify the result - score should be calculated immediately
    assert result is not None
    assert result.id == user_quiz.id
    assert result.pending_completion is False  # Now false as quiz is completed immediately
    assert result.completed_at is not None  # Should have completion timestamp
    
    # Verify that only the statistics task was queued (not the process task)
    mock_process.apply_async.assert_not_called()  # Process task should not be called
    # Check that apply_async was called with the correct args parameter
    mock_stats.apply_async.assert_called_once_with(args=[test_quiz.id], countdown=0)


def test_calculate_quiz_score(app, session, test_user, test_quiz):
    """Test the synchronous quiz score calculation."""
    # Create a user quiz
    user_quiz = UserQuiz(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        created_at=datetime.utcnow()
    )
    session.add(user_quiz)
    session.commit()
    
    # Get questions and correct options
    questions = test_quiz.questions.all()  # Convert query to list
    
    # Submit answers (all correct)
    for question in questions:
        correct_option = Option.query.filter_by(
            question_id=question.id, 
            is_correct=True
        ).first()
        
        user_answer = UserAnswer(
            user_quiz_id=user_quiz.id,
            question_id=question.id,
            option_id=correct_option.id
        )
        session.add(user_answer)
    
    session.commit()
    
    # Calculate score
    result = QuizService.calculate_quiz_score(user_quiz.id)
    
    # Verify the result
    assert result is not None
    assert result.id == user_quiz.id
    assert result.score == len(questions)
    assert result.completed_at is not None


def test_submit_answer(app, session, test_user, test_quiz):
    """Test submitting an answer to a quiz."""
    # Create a user quiz
    user_quiz = UserQuiz(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        created_at=datetime.utcnow()
    )
    session.add(user_quiz)
    session.commit()
    
    # Get a question and option
    question = test_quiz.questions[0]
    option = question.options[0]
    
    # Submit an answer
    result = QuizService.submit_answer(user_quiz.id, question.id, option.id)
    
    # Verify the result
    assert result is not None
    assert result.user_quiz_id == user_quiz.id
    assert result.question_id == question.id
    assert result.option_id == option.id
    
    # Submit the same answer again (should update)
    new_option = question.options[1]
    result = QuizService.submit_answer(user_quiz.id, question.id, new_option.id)
    
    # Verify the result was updated
    assert result.option_id == new_option.id


def test_start_quiz(app, session, test_user, test_quiz):
    """Test starting a quiz."""
    # Start the quiz
    user_quiz = QuizService.start_quiz(test_user, test_quiz.id)
    
    # Verify the result
    assert user_quiz is not None
    assert user_quiz.user_id == test_user.id
    assert user_quiz.quiz_id == test_quiz.id
    assert user_quiz.score == 0
    assert user_quiz.completed_at is None
    assert user_quiz.created_at is not None
