# Flask Quiz Application

A quiz application built with Flask that loads questions from YAML files and stores data in PostgreSQL.

## Features

- Load quiz questions from YAML files
- Store quiz data in PostgreSQL database
- User authentication and session management
- Quiz taking functionality with scoring
- Admin interface for managing quizzes and viewing results
- Dockerized application for easy deployment

## Requirements

- Docker and Docker Compose

## Quick Start

1. Clone the repository
2. Navigate to the project directory
3. Run the application with Docker Compose:

```bash
docker-compose up --build
```

4. Access the application at http://localhost:5000

## Project Structure

- `app/`: Flask application code
  - `routes/`: Route handlers
  - `services/`: Business logic services
  - `templates/`: HTML templates
  - `static/`: CSS, JavaScript, and images
- `quizzes/`: YAML quiz files
- `Dockerfile`: Docker configuration
- `docker-compose.yml`: Docker Compose configuration

## Quiz File Format

Quiz files should be in YAML format with the following structure:

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
```

## Admin Access

The first registered user will automatically be granted admin privileges. Admin users can:

- Import quizzes from YAML files
- View all users and quiz results
- Manage quizzes and users

## License

MIT
