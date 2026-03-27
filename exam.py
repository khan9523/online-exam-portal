import random
import json
from datetime import datetime, timedelta
from database import fetch_one, fetch_all, execute_write


class ExamManager:
    """Handles exam logic including randomization, shuffling, and submission."""
    
    @staticmethod
    def get_exam_questions(exam_id, randomize=True, shuffle_options=True):
        """
        Get questions for an exam with optional randomization and shuffling.
        
        Args:
            exam_id: The exam ID
            randomize: If True, randomize the order of questions
            shuffle_options: If True, shuffle the answer options
            
        Returns:
            List of question dictionaries with randomized order and options
        """
        questions = fetch_all(
            """
            SELECT id, question, option_a, option_b, option_c, option_d, 
                   correct_option, category, difficulty
            FROM questions
            WHERE exam_id = ?
            ORDER BY id
            """,
            (exam_id,)
        )
        
        if not questions:
            return []
        
        # Convert to list of dicts
        questions_list = []
        for q in questions:
            question_dict = {
                'id': q[0],
                'question': q[1],
                'options': {
                    'A': q[2],
                    'B': q[3],
                    'C': q[4],
                    'D': q[5]
                },
                'correct_option': q[6],
                'category': q[7],
                'difficulty': q[8]
            }
            questions_list.append(question_dict)
        
        # Randomize question order
        if randomize:
            random.shuffle(questions_list)
        
        # Shuffle options
        if shuffle_options:
            for question in questions_list:
                ExamManager._shuffle_options(question)
        
        return questions_list
    
    @staticmethod
    def _shuffle_options(question):
        """Shuffle answer options and update correct_option reference."""
        options = question['options']
        original_correct = question['correct_option']
        
        # Get the full text of the correct answer
        correct_text = options[original_correct]
        
        # Create list of tuples (key, value)
        option_items = list(options.items())
        random.shuffle(option_items)
        
        # Rebuild options dict
        new_options = {}
        new_correct_key = None
        
        for new_key, (old_key, value) in zip(['A', 'B', 'C', 'D'], option_items):
            new_options[new_key] = value
            if value == correct_text:
                new_correct_key = new_key
        
        question['options'] = new_options
        question['correct_option'] = new_correct_key
    
    @staticmethod
    def get_exam_config(exam_id):
        """Get exam configuration including duration and rules."""
        exam = fetch_one(
            """
            SELECT id, exam_name, description, duration_minutes, 
                   randomize_questions, shuffle_options, passing_percentage,
                   total_questions
            FROM exams
            WHERE id = ?
            """,
            (exam_id,)
        )
        
        if not exam:
            return None
        
        return {
            'id': exam[0],
            'name': exam[1],
            'description': exam[2],
            'duration_minutes': exam[3],
            'randomize_questions': exam[4],
            'shuffle_options': exam[5],
            'passing_percentage': exam[6],
            'total_questions': exam[7]
        }
    
    @staticmethod
    def submit_answers(username, exam_id, answers_dict):
        """
        Submit exam answers and calculate score.
        
        Args:
            username: Student username
            exam_id: Exam ID
            answers_dict: Dictionary of {question_id: selected_option}
            
        Returns:
            Dictionary with score, percentage, and detailed results
        """
        questions = fetch_all(
            "SELECT id, correct_option FROM questions WHERE exam_id = ?",
            (exam_id,)
        )
        
        if not questions:
            return None
        
        correct_count = 0
        total_count = len(questions)
        answer_records = []
        
        for question in questions:
            question_id, correct_option = question
            selected_option = answers_dict.get(str(question_id), None)
            is_correct = 1 if selected_option == correct_option else 0
            correct_count += is_correct
            
            answer_records.append((
                username,
                exam_id,
                question_id,
                selected_option,
                correct_option,
                is_correct
            ))
        
        # Insert answer records
        from database import execute_many
        execute_many(
            """
            INSERT INTO answers (username, exam_id, question_id, selected_option, 
                                correct_option, is_correct)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            answer_records
        )
        
        # Calculate results
        percentage = (correct_count / total_count * 100) if total_count > 0 else 0
        exam_config = ExamManager.get_exam_config(exam_id)
        passing_percentage = exam_config['passing_percentage'] if exam_config else 50
        status = 'PASS' if percentage >= passing_percentage else 'FAIL'
        
        # Insert result record
        execute_write(
            """
            INSERT INTO results (username, exam_id, score, percentage, status, 
                                question_count, correct_count, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (username, exam_id, correct_count, percentage, status, 
             total_count, correct_count, datetime.now().isoformat())
        )
        
        return {
            'correct_count': correct_count,
            'total_count': total_count,
            'percentage': round(percentage, 2),
            'status': status,
            'passing_percentage': passing_percentage
        }
    
    @staticmethod
    def get_student_result(username, exam_id):
        """Get detailed result for a student's exam attempt."""
        result = fetch_one(
            """
            SELECT id, score, percentage, status, time_taken_minutes, 
                   question_count, correct_count, submitted_at
            FROM results
            WHERE username = ? AND exam_id = ?
            ORDER BY submitted_at DESC
            LIMIT 1
            """,
            (username, exam_id)
        )
        
        if not result:
            return None
        
        result_id, score, percentage, status, time_taken, q_count, c_count, submitted = result
        
        # Get detailed answers
        answers = fetch_all(
            """
            SELECT question_id, selected_option, correct_option, is_correct
            FROM answers
            WHERE username = ? AND exam_id = ?
            """,
            (username, exam_id)
        )
        
        # Get questions for detailed feedback
        questions_details = []
        for answer in answers:
            q_id, selected, correct, is_correct = answer
            question = fetch_one(
                "SELECT question, option_a, option_b, option_c, option_d FROM questions WHERE id = ?",
                (q_id,)
            )
            if question:
                questions_details.append({
                    'question_id': q_id,
                    'question_text': question[0],
                    'selected_option': selected,
                    'correct_option': correct,
                    'is_correct': bool(is_correct),
                    'options': {
                        'A': question[1],
                        'B': question[2],
                        'C': question[3],
                        'D': question[4]
                    }
                })
        
        return {
            'score': score,
            'percentage': percentage,
            'status': status,
            'time_taken_minutes': time_taken,
            'question_count': q_count,
            'correct_count': c_count,
            'submitted_at': submitted,
            'details': questions_details
        }
    
    @staticmethod
    def is_exam_time_expired(exam_id, username):
        """Check if exam time has expired for a user."""
        session = fetch_one(
            """
            SELECT start_time FROM exam_sessions
            WHERE username = ? AND exam_id = ? AND is_active = 1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (username, exam_id)
        )
        
        if not session:
            return True
        
        start_time_str = session[0]
        start_time = datetime.fromisoformat(start_time_str)
        
        exam_config = ExamManager.get_exam_config(exam_id)
        if not exam_config:
            return True
        
        duration = timedelta(minutes=exam_config['duration_minutes'])
        end_time = start_time + duration
        
        return datetime.now() > end_time
    
    @staticmethod
    def get_time_remaining(exam_id, username):
        """Get remaining time in minutes for an active exam."""
        session = fetch_one(
            """
            SELECT start_time FROM exam_sessions
            WHERE username = ? AND exam_id = ? AND is_active = 1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (username, exam_id)
        )
        
        if not session:
            return 0
        
        start_time_str = session[0]
        start_time = datetime.fromisoformat(start_time_str)
        
        exam_config = ExamManager.get_exam_config(exam_id)
        if not exam_config:
            return 0
        
        duration = timedelta(minutes=exam_config['duration_minutes'])
        end_time = start_time + duration
        time_remaining = end_time - datetime.now()
        
        return max(0, time_remaining.total_seconds() / 60)
