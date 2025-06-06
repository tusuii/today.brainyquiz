"""
Integration tests for Celery and RabbitMQ integration.
"""
import pytest
from unittest.mock import patch
from datetime import datetime
from app.models import UserQuiz, UserAnswer, Option

# Import our mock tasks
from tests.mock_tasks import process_quiz_submission, generate_quiz_statistics


def test_process_quiz_submission_task(app, session, test_user, test_quiz):
    """Test that the process_quiz_submission task correctly calculates scores."""
    # Create a user quiz
    user_quiz = UserQuiz(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        pending_completion=True,
        created_at=datetime.utcnow()
    )
    session.add(user_quiz)
    session.commit()
    
    # Get questions and correct options
    questions = test_quiz.questions.all()  # Convert query to list
    
    # Submit answers (2 correct, 1 incorrect)
    for i, question in enumerate(questions):
        correct_option = Option.query.filter_by(
            question_id=question.id, 
            is_correct=True
        ).first()
        
        # Make the last answer incorrect
        if i == len(questions) - 1:
            incorrect_option = Option.query.filter_by(
                question_id=question.id, 
                is_correct=False
            ).first()
            
            user_answer = UserAnswer(
                user_quiz_id=user_quiz.id,
                question_id=question.id,
                option_id=incorrect_option.id
            )
        else:
            user_answer = UserAnswer(
                user_quiz_id=user_quiz.id,
                question_id=question.id,
                option_id=correct_option.id
            )
            
        session.add(user_answer)
    
    session.commit()
    
    # Run our mock task
    result = process_quiz_submission(user_quiz.id)
    
    # Refresh the user quiz from the database
    session.refresh(user_quiz)
    
    # Verify the result
    assert user_quiz.completed_at is not None
    assert user_quiz.score == 2  # 2 out of 3 correct
    assert not user_quiz.pending_completion


def test_generate_quiz_statistics_task(app, session, test_user, test_quiz):
    """Test that the generate_quiz_statistics task correctly calculates statistics."""
    # Create multiple user quizzes with different scores
    for i in range(3):
        user_quiz = UserQuiz(
            user_id=test_user.id,
            quiz_id=test_quiz.id,
            score=i * 33.3,  # 0%, 33.3%, 66.6%
            completed_at=datetime.utcnow()
        )
        session.add(user_quiz)
    
    # Add one incomplete quiz
    incomplete_quiz = UserQuiz(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        created_at=datetime.utcnow()
    )
    session.add(incomplete_quiz)
    session.commit()
    
    # Run our mock task
    stats = generate_quiz_statistics(test_quiz.id)
    
    # Verify the statistics
    assert stats is not None
    assert stats['quiz_id'] == test_quiz.id
    assert stats['total_attempts'] == 3
    assert round(stats['average_score'], 1) == round((0 + 33.3 + 66.6) / 3, 1)
    assert round(stats['completion_rate'], 1) == round(3 / 4 * 100, 1)  # 3 completed out of 4 started


@pytest.mark.skip(reason="Requires running RabbitMQ and Celery worker")
def test_celery_task_queue_integration(app, session, test_user, test_quiz):
    """
    Test the integration with Celery task queue.
    
    This test requires a running RabbitMQ and Celery worker.
    Skip by default, but can be run in a full integration environment.
    """
    # Create a user quiz
    user_quiz = UserQuiz(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        pending_completion=True,
        created_at=datetime.utcnow()
    )
    session.add(user_quiz)
    session.commit()
    
    # Submit a correct answer
    questions = test_quiz.questions.all()  # Convert query to list
    question = questions[0]
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
    
    # Queue the task through Celery
    task_result = process_quiz_submission.delay(user_quiz.id)
    
    # Wait for the task to complete
    result = task_result.get(timeout=10)
    
    # Refresh the user quiz from the database
    session.refresh(user_quiz)
    
    # Verify the result
    assert user_quiz.completed_at is not None
    assert user_quiz.score == 1  # 1 out of 3 questions answered, and it was correct
    assert not user_quiz.pending_completion
