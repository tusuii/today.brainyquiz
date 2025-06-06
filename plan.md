# Flask Quiz Application Plan

## Overview
This project will create a quiz application using Flask that loads questions from YAML files, stores data in PostgreSQL, and runs in Docker containers.

## Features
- Load quiz questions from YAML files
- Store quiz data in PostgreSQL database
- User authentication and session management
- Quiz taking functionality with scoring
- Admin interface for managing quizzes and viewing results
- Dockerized application for easy deployment

## Tech Stack
- **Backend**: Python 3 + Flask
- **Database**: PostgreSQL
- **Containerization**: Docker and Docker Compose
- **Frontend**: HTML, CSS, JavaScript (with Bootstrap for styling)

## Project Structure
```
exam-app/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── README.md
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── quiz.py
│   │   └── admin.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── quiz_loader.py
│   │   └── quiz_service.py
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── templates/
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── quiz/
│   │   └── admin/
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
└── quizzes/
    ├── sample_quiz.yml
    └── ...
```

## Database Schema

### Users Table
- id (PK)
- username (unique)
- email (unique)
- password_hash
- is_admin (boolean)
- created_at
- updated_at

### Quizzes Table
- id (PK)
- title
- description
- created_at
- updated_at

### Questions Table
- id (PK)
- quiz_id (FK to Quizzes)
- question_text
- created_at
- updated_at

### Options Table
- id (PK)
- question_id (FK to Questions)
- option_text
- is_correct (boolean)
- created_at
- updated_at

### UserQuizzes Table
- id (PK)
- user_id (FK to Users)
- quiz_id (FK to Quizzes)
- score
- completed_at
- created_at
- updated_at

### UserAnswers Table
- id (PK)
- user_quiz_id (FK to UserQuizzes)
- question_id (FK to Questions)
- option_id (FK to Options)
- created_at
- updated_at

## Implementation Plan

### Phase 1: Project Setup
1. Set up project structure
2. Create requirements.txt with dependencies
3. Create Dockerfile and docker-compose.yml
4. Set up basic Flask application
5. Configure PostgreSQL connection

### Phase 2: Database Models
1. Create SQLAlchemy models for all tables
2. Set up database migrations
3. Create database initialization script

### Phase 3: Quiz Loading Service
1. Create YAML parser for quiz files
2. Implement quiz loading service
3. Create sample quiz YAML files

### Phase 4: Core Functionality
1. Implement user authentication (register, login, logout)
2. Create quiz listing and selection interface
3. Implement quiz taking functionality
4. Add scoring system

### Phase 5: Admin Interface
1. Create admin dashboard
2. Add quiz management features
3. Add user management features
4. Implement results viewing

### Phase 6: Frontend Styling and UX
1. Design and implement responsive UI with Bootstrap
2. Add JavaScript for interactive elements
3. Improve user experience

### Phase 7: Testing and Deployment
1. Write unit tests
2. Perform integration testing
3. Document deployment process
4. Finalize Docker configuration

## YAML File Format
```yaml
title: Sample Quiz
description: A sample quiz to demonstrate the format
questions:
  - text: What is the capital of France?
    options:
      - text: London
        correct: false
      - text: Berlin
        correct: false
      - text: Paris
        correct: true
      - text: Madrid
        correct: false
  - text: Which planet is known as the Red Planet?
    options:
      - text: Venus
        correct: false
      - text: Mars
        correct: true
      - text: Jupiter
        correct: false
      - text: Saturn
        correct: false
```

## API Endpoints

### Authentication
- POST /api/auth/register - Register a new user
- POST /api/auth/login - Log in a user
- POST /api/auth/logout - Log out a user

### Quiz
- GET /api/quizzes - List all quizzes
- GET /api/quizzes/:id - Get a specific quiz
- POST /api/quizzes/:id/start - Start a quiz
- POST /api/quizzes/:id/submit - Submit quiz answers

### Admin
- POST /api/admin/quizzes - Create a new quiz
- PUT /api/admin/quizzes/:id - Update a quiz
- DELETE /api/admin/quizzes/:id - Delete a quiz
- GET /api/admin/results - View all results
- GET /api/admin/users - View all users

## Next Steps
After implementing this plan, potential future enhancements could include:
- Timed quizzes
- Different question types (multiple choice, true/false, fill-in-the-blank)
- User profile pages
- Quiz categories and tags
- Social sharing features
- Analytics dashboard
