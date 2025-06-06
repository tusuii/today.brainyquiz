import os
import yaml
import logging
from app import db
from app.models import Quiz, Question, Option

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class QuizLoader:
    """Service for loading quizzes from YAML files into the database"""
    
    @staticmethod
    def load_quiz_from_file(file_path):
        """
        Load a quiz from a YAML file and save it to the database
        
        Args:
            file_path (str): Path to the YAML file
            
        Returns:
            Quiz: The created Quiz object
        """
        logging.debug(f"Loading quiz from file: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Quiz file not found: {file_path}")
        
        try:
            with open(file_path, 'r') as file:
                quiz_data = yaml.safe_load(file)
                logging.debug(f"Quiz data loaded: {quiz_data['title'] if 'title' in quiz_data else 'No title'}")
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML file: {e}")
            raise ValueError(f"Error parsing YAML file: {e}")
        
        # Validate quiz data
        if not quiz_data.get('title'):
            raise ValueError("Quiz must have a title")
        if not quiz_data.get('questions') or not isinstance(quiz_data['questions'], list):
            raise ValueError("Quiz must have questions as a list")
        
        # Create quiz in database
        try:
            quiz = Quiz(
                title=quiz_data['title'],
                description=quiz_data.get('description', ''),
                is_live=False  # Default to not live
            )
            db.session.add(quiz)
            # Flush to get the quiz ID
            db.session.flush()
            logging.debug(f"Created quiz with ID: {quiz.id}")
            
            # Add questions and options
            for q_index, q_data in enumerate(quiz_data['questions']):
                if not q_data.get('text'):
                    logging.warning(f"Skipping question {q_index} without text")
                    continue  # Skip questions without text
                    
                try:
                    question = Question(
                        quiz=quiz,
                        text=q_data['text']
                    )
                    db.session.add(question)
                    db.session.flush()  # Get the question ID
                    logging.debug(f"Created question with ID: {question.id}, text: {question.text[:30]}...")
                    
                    # Add options for this question
                    if q_data.get('options') and isinstance(q_data['options'], list):
                        for opt_index, opt_data in enumerate(q_data['options']):
                            if not opt_data.get('text'):
                                logging.warning(f"Skipping option {opt_index} without text for question {question.id}")
                                continue  # Skip options without text
                                
                            try:
                                # Handle both 'correct' and 'is_correct' fields in YAML files
                                is_correct = opt_data.get('correct', False) or opt_data.get('is_correct', False)
                                
                                # Ensure text is a string
                                option_text = str(opt_data['text'])
                                
                                option = Option(
                                    question_id=question.id,  # Use ID directly
                                    text=option_text,
                                    is_correct=bool(is_correct)  # Ensure boolean type
                                )
                                db.session.add(option)
                                logging.debug(f"Created option: {option_text[:20]}..., is_correct: {is_correct}")
                            except Exception as e:
                                logging.error(f"Error creating option: {e}")
                                raise
                except Exception as e:
                    logging.error(f"Error creating question: {e}")
                    raise
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating quiz: {e}")
            raise
        
        # Commit all changes to database
        db.session.commit()
        return quiz
    
    @staticmethod
    def load_all_quizzes_from_directory(directory_path):
        """
        Load all YAML quiz files from a directory
        
        Args:
            directory_path (str): Path to directory containing quiz files
            
        Returns:
            list: List of Quiz objects created
        """
        logging.info(f"Loading all quizzes from directory: {directory_path}")
        if not os.path.isdir(directory_path):
            logging.error(f"Directory not found: {directory_path}")
            raise NotADirectoryError(f"Directory not found: {directory_path}")
        
        quizzes = []
        for filename in os.listdir(directory_path):
            if filename.endswith(('.yml', '.yaml')):
                try:
                    file_path = os.path.join(directory_path, filename)
                    logging.info(f"Processing quiz file: {filename}")
                    quiz = QuizLoader.load_quiz_from_file(file_path)
                    quizzes.append(quiz)
                    logging.info(f"Successfully loaded quiz: {quiz.title}")
                except Exception as e:
                    # Log error but continue with other files
                    logging.error(f"Error loading quiz file {filename}: {str(e)}")
                    print(f"Error loading quiz file {filename}: {e}")
        
        logging.info(f"Loaded {len(quizzes)} quizzes successfully")
        return quizzes
