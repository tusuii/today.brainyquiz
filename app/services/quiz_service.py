from app import db
from app.models import Quiz, Question, Option, UserQuiz, UserAnswer
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class QuizService:
    """Service for handling quiz operations"""
    
    @staticmethod
    def get_all_quizzes():
        """
        Get all quizzes from the database
        
        Returns:
            list: List of Quiz objects
        """
        return Quiz.query.all()
    
    @staticmethod
    def get_quiz_by_id(quiz_id):
        """
        Get a quiz by ID
        
        Args:
            quiz_id (int): ID of the quiz
            
        Returns:
            Quiz: Quiz object or None if not found
        """
        return Quiz.query.get(quiz_id)
    
    @staticmethod
    def start_quiz(user, quiz_id):
        """
        Start a new quiz attempt for a user
        
        Args:
            user (User): User object
            quiz_id (int): ID of the quiz
            
        Returns:
            UserQuiz: Created UserQuiz object or None if quiz not found
        """
        logging.debug(f"QuizService.start_quiz called with user_id={user.id}, quiz_id={quiz_id}")
        
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            logging.error(f"Quiz with ID {quiz_id} not found")
            return None
        
        logging.debug(f"Found quiz: {quiz.title} (ID: {quiz.id})")
        
        # Check if quiz has questions
        question_count = Question.query.filter_by(quiz_id=quiz.id).count()
        logging.debug(f"Quiz has {question_count} questions")
        
        if question_count == 0:
            logging.warning(f"Quiz {quiz_id} has no questions!")
        
        # Create a new user quiz attempt
        try:
            # Explicitly set created_at to ensure it's set to the current time
            user_quiz = UserQuiz(
                user=user,
                quiz=quiz,
                created_at=datetime.utcnow()
            )
            db.session.add(user_quiz)
            db.session.commit()
            logging.debug(f"Created new UserQuiz with ID {user_quiz.id}, created_at: {user_quiz.created_at}")
            return user_quiz
        except Exception as e:
            logging.error(f"Error creating UserQuiz: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def submit_answer(user_quiz_id, question_id, option_id):
        """
        Submit an answer for a question in a quiz attempt
        
        Args:
            user_quiz_id (int): ID of the user quiz attempt
            question_id (int): ID of the question
            option_id (int): ID of the selected option
            
        Returns:
            UserAnswer: Created UserAnswer object or None if not valid
        """
        user_quiz = UserQuiz.query.get(user_quiz_id)
        question = Question.query.get(question_id)
        option = Option.query.get(option_id)
        
        if not user_quiz or not question or not option:
            return None
        
        # Check if question belongs to the quiz
        if question.quiz_id != user_quiz.quiz_id:
            return None
        
        # Check if option belongs to the question
        if option.question_id != question.id:
            return None
        
        # Check if answer already exists for this question in this attempt
        existing_answer = UserAnswer.query.filter_by(
            user_quiz_id=user_quiz_id,
            question_id=question_id
        ).first()
        
        if existing_answer:
            # Update existing answer
            existing_answer.option_id = option_id
            db.session.commit()
            return existing_answer
        
        # Create new answer
        user_answer = UserAnswer(
            user_quiz=user_quiz,
            question=question,
            option=option
        )
        db.session.add(user_answer)
        db.session.commit()
        
        return user_answer
    
    @staticmethod
    def complete_quiz(user_quiz_id):
        """
        Complete a quiz attempt and calculate the score
        
        Args:
            user_quiz_id (int): ID of the user quiz attempt
            
        Returns:
            UserQuiz: Updated UserQuiz object or None if not found
        """
        user_quiz = UserQuiz.query.get(user_quiz_id)
        if not user_quiz:
            return None
        
        # Calculate score
        score = 0
        total_questions = 0
        
        # Get all questions for this quiz
        questions = Question.query.filter_by(quiz_id=user_quiz.quiz_id).all()
        total_questions = len(questions)
        
        # Check each answer
        for question in questions:
            user_answer = UserAnswer.query.filter_by(
                user_quiz_id=user_quiz.id,
                question_id=question.id
            ).first()
            
            if user_answer:
                # Check if the selected option is correct
                option = Option.query.get(user_answer.option_id)
                if option and option.is_correct:
                    score += 1
        
        # Update user quiz with score and completion time
        user_quiz.score = score
        user_quiz.completed_at = datetime.utcnow()
        db.session.commit()
        
        return user_quiz
