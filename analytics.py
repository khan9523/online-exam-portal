import json
from datetime import datetime
from database import fetch_all, fetch_one, execute_write


class AnalyticsManager:
    """Handles analytics, dashboards, and performance metrics."""
    
    @staticmethod
    def get_exam_statistics(exam_id):
        """Get comprehensive statistics for an exam."""
        results = fetch_all(
            """
            SELECT score, percentage, status, time_taken_minutes, question_count, correct_count
            FROM results
            WHERE exam_id = ?
            """,
            (exam_id,)
        )
        
        if not results:
            return {
                'total_attempts': 0,
                'average_score': 0,
                'pass_rate': 0,
                'average_time_minutes': 0,
                'highest_score': 0,
                'lowest_score': 0
            }
        
        total_attempts = len(results)
        percentages = [r[1] for r in results]
        scores = [r[0] for r in results]
        statuses = [r[2] for r in results]
        times = [r[3] or 0 for r in results]
        
        average_percentage = sum(percentages) / len(percentages) if percentages else 0
        pass_count = sum(1 for s in statuses if s == 'PASS')
        pass_rate = (pass_count / total_attempts * 100) if total_attempts > 0 else 0
        average_time = sum(times) / len(times) if times else 0
        
        return {
            'total_attempts': total_attempts,
            'average_score': round(average_percentage, 2),
            'pass_rate': round(pass_rate, 2),
            'average_time_minutes': round(average_time, 2),
            'highest_score': max(percentages) if percentages else 0,
            'lowest_score': min(percentages) if percentages else 0,
            'pass_count': pass_count,
            'fail_count': total_attempts - pass_count
        }
    
    @staticmethod
    def get_question_performance(exam_id):
        """Analyze performance on each question."""
        questions = fetch_all(
            """
            SELECT id, question, difficulty, category
            FROM questions
            WHERE exam_id = ?
            """,
            (exam_id,)
        )
        
        question_performance = []
        
        for q in questions:
            q_id, question_text, difficulty, category = q
            
            answers = fetch_all(
                """
                SELECT is_correct
                FROM answers
                WHERE question_id = ? AND exam_id = ?
                """,
                (q_id, exam_id)
            )
            
            if not answers:
                continue
            
            correct_count = sum(1 for a in answers if a[0] == 1)
            total_count = len(answers)
            correct_percentage = (correct_count / total_count * 100) if total_count > 0 else 0
            
            question_performance.append({
                'question_id': q_id,
                'question_text': question_text,
                'difficulty': difficulty,
                'category': category,
                'total_attempts': total_count,
                'correct_attempts': correct_count,
                'success_rate': round(correct_percentage, 2)
            })
        
        return question_performance
    
    @staticmethod
    def get_category_performance(exam_id):
        """Analyze performance by question category."""
        categories = fetch_all(
            "SELECT DISTINCT category FROM questions WHERE exam_id = ?",
            (exam_id,)
        )
        
        category_stats = []
        
        for cat in categories:
            category = cat[0]
            
            results = fetch_all(
                """
                SELECT a.is_correct
                FROM answers a
                JOIN questions q ON a.question_id = q.id
                WHERE a.exam_id = ? AND q.category = ?
                """,
                (exam_id, category)
            )
            
            if not results:
                continue
            
            correct_count = sum(1 for r in results if r[0] == 1)
            total_count = len(results)
            success_rate = (correct_count / total_count * 100) if total_count > 0 else 0
            
            category_stats.append({
                'category': category,
                'total_questions': total_count,
                'correct_answers': correct_count,
                'success_rate': round(success_rate, 2)
            })
        
        return category_stats
    
    @staticmethod
    def get_difficulty_performance(exam_id):
        """Analyze performance by difficulty level."""
        difficulties = ['Easy', 'Medium', 'Hard']
        difficulty_stats = []
        
        for difficulty in difficulties:
            results = fetch_all(
                """
                SELECT a.is_correct
                FROM answers a
                JOIN questions q ON a.question_id = q.id
                WHERE a.exam_id = ? AND q.difficulty = ?
                """,
                (exam_id, difficulty)
            )
            
            if not results:
                continue
            
            correct_count = sum(1 for r in results if r[0] == 1)
            total_count = len(results)
            success_rate = (correct_count / total_count * 100) if total_count > 0 else 0
            
            difficulty_stats.append({
                'difficulty': difficulty,
                'total_questions': total_count,
                'correct_answers': correct_count,
                'success_rate': round(success_rate, 2)
            })
        
        return difficulty_stats
    
    @staticmethod
    def get_student_dashboard(username):
        """Get comprehensive dashboard for a student."""
        results = fetch_all(
            """
            SELECT exam_id, score, percentage, status, submitted_at
            FROM results
            WHERE username = ?
            ORDER BY submitted_at DESC
            """,
            (username,)
        )
        
        exam_attempts = []
        total_attempts = 0
        pass_attempts = 0
        total_percentage = 0
        
        for r in results:
            exam_id, score, percentage, status, submitted = r
            exam_name = fetch_one("SELECT exam_name FROM exams WHERE id = ?", (exam_id,))
            
            if exam_name:
                exam_attempts.append({
                    'exam_id': exam_id,
                    'exam_name': exam_name[0],
                    'score': score,
                    'percentage': percentage,
                    'status': status,
                    'submitted_at': submitted
                })
                
                total_attempts += 1
                if status == 'PASS':
                    pass_attempts += 1
                total_percentage += percentage
        
        average_percentage = (total_percentage / total_attempts) if total_attempts > 0 else 0
        
        return {
            'username': username,
            'total_attempts': total_attempts,
            'passed_attempts': pass_attempts,
            'failed_attempts': total_attempts - pass_attempts,
            'average_percentage': round(average_percentage, 2),
            'exam_attempts': exam_attempts
        }
    
    @staticmethod
    def get_admin_dashboard():
        """Get comprehensive dashboard for admin."""
        # Total exams and students
        total_exams = fetch_one("SELECT COUNT(*) FROM exams")
        total_students = fetch_one("SELECT COUNT(*) FROM users WHERE role = 'student'")
        total_attempts = fetch_one("SELECT COUNT(*) FROM results")
        
        exams = fetch_all("SELECT id, exam_name FROM exams ORDER BY created_at DESC LIMIT 10")
        
        exam_stats = []
        for exam in exams:
            exam_id, exam_name = exam
            stats = AnalyticsManager.get_exam_statistics(exam_id)
            stats['exam_id'] = exam_id
            stats['exam_name'] = exam_name
            exam_stats.append(stats)
        
        return {
            'total_exams': total_exams[0] if total_exams else 0,
            'total_students': total_students[0] if total_students else 0,
            'total_attempts': total_attempts[0] if total_attempts else 0,
            'latest_exams': exam_stats
        }
    
    @staticmethod
    def update_analytics(exam_id):
        """Update analytics cache for an exam."""
        stats = AnalyticsManager.get_exam_statistics(exam_id)
        category_perf = AnalyticsManager.get_category_performance(exam_id)
        difficulty_perf = AnalyticsManager.get_difficulty_performance(exam_id)
        
        existing = fetch_one("SELECT id FROM analytics WHERE exam_id = ?", (exam_id,))
        
        if existing:
            execute_write(
                """
                UPDATE analytics
                SET total_attempts = ?, average_score = ?, pass_rate = ?, 
                    average_time_minutes = ?, category_performance = ?,
                    question_difficulty_stats = ?, updated_at = ?
                WHERE exam_id = ?
                """,
                (
                    stats['total_attempts'],
                    stats['average_score'],
                    stats['pass_rate'],
                    stats['average_time_minutes'],
                    json.dumps(category_perf),
                    json.dumps(difficulty_perf),
                    datetime.now().isoformat(),
                    exam_id
                )
            )
        else:
            execute_write(
                """
                INSERT INTO analytics 
                (exam_id, total_attempts, average_score, pass_rate, average_time_minutes, 
                 category_performance, question_difficulty_stats, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    exam_id,
                    stats['total_attempts'],
                    stats['average_score'],
                    stats['pass_rate'],
                    stats['average_time_minutes'],
                    json.dumps(category_perf),
                    json.dumps(difficulty_perf),
                    datetime.now().isoformat()
                )
            )
