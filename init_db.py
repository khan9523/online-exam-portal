#!/usr/bin/env python
"""
Initialize the database with sample data for testing
"""

import os
from database import create_tables, execute_write, execute_many
from auth import AuthManager

def init_database():
    """Initialize database and create sample admin/student accounts"""
    
    # Create tables
    create_tables()
    print("✓ Database tables created")
    
    # Create default admin user
    try:
        admin = AuthManager.authenticate_user('admin', 'admin123')
        if not admin:
            AuthManager.create_user('admin', 'admin123', role='admin')
            print("✓ Admin user created (username: admin, password: admin123)")
    except Exception as e:
        print(f"Note: Admin user already exists or error: {e}")
    
    # Create a sample exam
    try:
        execute_write(
            """
            INSERT INTO exams (exam_name, description, duration_minutes, passing_percentage, total_questions, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ('Python Basics', 'Test your knowledge of Python fundamentals', 30, 50, 10, '2026-03-28 12:00:00')
        )
        print("✓ Sample exam created: Python Basics")
        
        # Add sample questions
        questions = [
            ('Python Basics', 1, 'What is the output of print(2 ** 3)?', '6', '8', '9', '16', 'B', 'Operators', 'Easy'),
            ('Python Basics', 1, 'Which keyword is used to define a function?', 'func', 'function', 'def', 'define', 'C', 'Syntax', 'Easy'),
            ('Python Basics', 1, 'What data type is 3.14 in Python?', 'int', 'str', 'float', 'double', 'C', 'Data Types', 'Easy'),
            ('Python Basics', 1, 'How do you create a list in Python?', '{}', '[]', '()', '<>', 'B', 'Collections', 'Easy'),
            ('Python Basics', 1, 'Which of these is NOT a Python built-in function?', 'len()', 'print()', 'length()', 'type()', 'C', 'Functions', 'Medium'),
        ]
        
        for question in questions:
            execute_write(
                """
                INSERT INTO questions (exam_id, question, option_a, option_b, option_c, option_d, correct_option, category, difficulty)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                question[1:]
            )
        print("✓ Sample questions added to the exam")
        
    except Exception as e:
        print(f"Note: Sample exam/questions already exist or error: {e}")
    
    print("\n✅ Database initialized successfully!")
    print("\nDefault credentials:")
    print("  Admin - username: admin, password: admin123")
    print("\nYou can now run the app with: python app.py")

if __name__ == '__main__':
    init_database()
