"""
This script will create a migration to add the is_live field to the Quiz model.
Run this script with Flask app context to generate the migration.
"""
import sys
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db

# Create the Flask app with the application context
app = create_app()

with app.app_context():
    # Import the models to ensure they're registered with SQLAlchemy
    from app.models import Quiz, User, Question, Option, UserQuiz, UserAnswer
    
    # Create a migration for the is_live field
    from alembic import op
    import sqlalchemy as sa
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    
    # Get the database connection
    conn = db.engine.connect()
    
    # Create a migration context
    context = MigrationContext.configure(conn)
    
    # Create an operations object
    op = Operations(context)
    
    try:
        # Check if the column already exists
        conn.execute(sa.text("SELECT is_live FROM quizzes LIMIT 1"))
        print("Column 'is_live' already exists in the 'quizzes' table.")
    except Exception:
        # Add the is_live column
        print("Adding 'is_live' column to the 'quizzes' table...")
        op.add_column('quizzes', sa.Column('is_live', sa.Boolean(), nullable=False, server_default='false'))
        print("Column 'is_live' added successfully.")
    
    conn.close()
    print("Migration completed.")
