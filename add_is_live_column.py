"""
Simple script to add the is_live column to the quizzes table.
This script uses raw SQL to directly modify the database schema.
"""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database connection parameters from environment variables
DB_HOST = os.environ.get('DB_HOST', 'postgres')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'quizdb')
DB_USER = os.environ.get('DB_USER', 'quizuser')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'quizpassword')

# Connect to the database
print(f"Connecting to database: {DB_NAME} on {DB_HOST}:{DB_PORT}")
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

# Set autocommit mode to avoid transaction issues
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cursor = conn.cursor()

try:
    # Check if the column already exists
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='quizzes' AND column_name='is_live'")
    if cursor.fetchone():
        print("Column 'is_live' already exists in the 'quizzes' table.")
    else:
        # Add the is_live column with a default value of false
        print("Adding 'is_live' column to the 'quizzes' table...")
        cursor.execute("ALTER TABLE quizzes ADD COLUMN is_live BOOLEAN DEFAULT FALSE")
        print("Column 'is_live' added successfully.")
except Exception as e:
    print(f"Error: {str(e)}")
finally:
    cursor.close()
    conn.close()
    print("Database connection closed.")
