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
        
        # Validate question structure
        for i, question in enumerate(quiz_data.get('questions', [])):
            if not isinstance(question, dict):
                raise ValueError(f"Question {i+1} must be a dictionary")
            if not question.get('text'):
                raise ValueError(f"Question {i+1} is missing text field")
            
            # Validate options
            if not question.get('options') or not isinstance(question['options'], list):
                raise ValueError(f"Question '{question.get('text', f'#{i+1}')}' must have options as a list")
            
            # Check if at least one option is correct
            has_correct = False
            for j, option in enumerate(question.get('options', [])):
                if not isinstance(option, dict):
                    raise ValueError(f"Option {j+1} in question '{question.get('text', f'#{i+1}')}' must be a dictionary")
                if 'text' not in option:
                    raise ValueError(f"Option {j+1} in question '{question.get('text', f'#{i+1}')}' is missing text field")
                
                # Check for correct answer
                is_correct = option.get('correct', False) or option.get('is_correct', False)
                if is_correct:
                    has_correct = True
            
            if not has_correct:
                logging.warning(f"Question '{question.get('text', f'#{i+1}')}' has no correct answer marked")
        
        logging.info(f"Quiz validation passed: {quiz_data['title']}")
        
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
                                
                                # Ensure text is a string and handle numeric values
                                if 'text' in opt_data:
                                    # Convert any value to string explicitly
                                    option_text = str(opt_data['text']).strip()
                                    if not option_text:
                                        logging.warning(f"Empty option text for question {question.id}")
                                        continue
                                else:
                                    logging.warning(f"Option missing 'text' field for question {question.id}")
                                    continue
                                
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
