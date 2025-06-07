from app import db
from app.models import Quiz, Question, Option, UserQuiz, UserAnswer
from datetime import datetime
import logging
from app.tasks import process_quiz_submission, generate_quiz_statistics

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
        Complete a quiz attempt with immediate score calculation
        
        This method calculates the score immediately and shows results to the user,
        while still queuing background tasks for additional processing.
        
        Args:
            user_quiz_id (int): ID of the user quiz attempt
            
        Returns:
            UserQuiz: Updated UserQuiz object or None if not found
        """
        logging.info(f"Starting complete_quiz for user_quiz_id={user_quiz_id}")
        
        user_quiz = UserQuiz.query.get(user_quiz_id)
        if not user_quiz:
            logging.error(f"UserQuiz with ID {user_quiz_id} not found")
            return None
        
        logging.info(f"Found UserQuiz: id={user_quiz.id}, user_id={user_quiz.user_id}, quiz_id={user_quiz.quiz_id}")
            
        # Check if already completed
        if user_quiz.completed_at:
            logging.warning(f"UserQuiz {user_quiz_id} is already completed at {user_quiz.completed_at}")
            return user_quiz
        
        try:
            # IMMEDIATE CALCULATION: Calculate the score synchronously
            logging.info(f"Starting immediate score calculation for UserQuiz {user_quiz_id}")
            
            # Get all questions for this quiz
            questions = Question.query.filter_by(quiz_id=user_quiz.quiz_id).all()
            total_questions = len(questions)
            logging.info(f"Found {total_questions} questions for quiz {user_quiz.quiz_id}")
            
            if total_questions == 0:
                # No questions to score
                logging.warning(f"No questions found for quiz {user_quiz.quiz_id}, setting score to 0")
                user_quiz.score = 0
                user_quiz.completed_at = datetime.utcnow()
                db.session.commit()
                return user_quiz
            
            # Get all user answers in a single query
            user_answers = UserAnswer.query.filter_by(user_quiz_id=user_quiz.id).all()
            logging.info(f"Found {len(user_answers)} answers for UserQuiz {user_quiz_id}")
            
            # Create a mapping of question_id to selected option_id for quick lookup
            answer_map = {answer.question_id: answer.option_id for answer in user_answers}
            
            # Get all correct options for these questions in a single query
            correct_options = db.session.query(Option.question_id, Option.id).filter(
                Option.question_id.in_([q.id for q in questions]),
                Option.is_correct == True
            ).all()
            logging.info(f"Found {len(correct_options)} correct options for quiz {user_quiz.quiz_id}")
            
            # Create a mapping of question_id to correct option_id
            correct_map = {question_id: option_id for question_id, option_id in correct_options}
            
            # Calculate score by comparing the two maps
            score = sum(1 for question_id, correct_option_id in correct_map.items() 
                      if answer_map.get(question_id) == correct_option_id)
            
            logging.info(f"Calculated score: {score}/{total_questions} for UserQuiz {user_quiz_id}")
            
            # Update user quiz with score and completion time
            user_quiz.score = score
            user_quiz.completed_at = datetime.utcnow()
            user_quiz.pending_completion = False  # Mark as completed immediately
            
            # Commit the changes
            logging.info(f"Committing score and completion time for UserQuiz {user_quiz_id}")
            db.session.commit()
            
            # Still queue the statistics generation task in the background
            logging.info(f"Queueing statistics generation for quiz {user_quiz.quiz_id}")
            try:
                generate_quiz_statistics.apply_async(args=[user_quiz.quiz_id], countdown=0)
                logging.info(f"Successfully queued statistics task for quiz {user_quiz.quiz_id}")
            except Exception as stats_error:
                # Don't fail the whole method if just the stats task fails
                logging.error(f"Failed to queue statistics task: {str(stats_error)}")
            
            logging.info(f"Successfully completed quiz {user_quiz_id} with score {score}")
            return user_quiz
            
        except Exception as e:
            logging.error(f"Error completing quiz: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            db.session.rollback()
            return None
            
    @staticmethod
    def calculate_quiz_score(user_quiz_id):
        """
        Calculate the score for a quiz attempt (synchronous version)
        
        This method is kept for backward compatibility and direct use
        when asynchronous processing is not needed.
        
        Args:
            user_quiz_id (int): ID of the user quiz attempt
            
        Returns:
            UserQuiz: Updated UserQuiz object or None if not found
        """
        user_quiz = UserQuiz.query.get(user_quiz_id)
        if not user_quiz:
            return None
        
        # Get all questions for this quiz
        questions = Question.query.filter_by(quiz_id=user_quiz.quiz_id).all()
        total_questions = len(questions)
        
        if total_questions == 0:
            # No questions to score
            user_quiz.score = 0
            user_quiz.completed_at = datetime.utcnow()
            db.session.commit()
            return user_quiz
        
        # Get all user answers in a single query
        user_answers = UserAnswer.query.filter_by(user_quiz_id=user_quiz.id).all()
        
        # Create a mapping of question_id to selected option_id for quick lookup
        answer_map = {answer.question_id: answer.option_id for answer in user_answers}
        
        # Get all correct options for these questions in a single query
        correct_options = db.session.query(Option.question_id, Option.id).filter(
            Option.question_id.in_([q.id for q in questions]),
            Option.is_correct == True
        ).all()
        
        # Create a mapping of question_id to correct option_id
        correct_map = {question_id: option_id for question_id, option_id in correct_options}
        
        # Calculate score by comparing the two maps
        score = sum(1 for question_id, correct_option_id in correct_map.items() 
                  if answer_map.get(question_id) == correct_option_id)
        
        # Update user quiz with score and completion time
        user_quiz.score = score
        user_quiz.completed_at = datetime.utcnow()
        db.session.commit()
        
        return user_quiz
