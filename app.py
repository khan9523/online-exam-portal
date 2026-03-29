from flask import Flask, render_template, request, session, redirect, url_for, jsonify, send_file
from flask_session import Session
from functools import wraps
from datetime import datetime, timedelta
from io import BytesIO
import os

# Import custom modules
from database import create_tables, fetch_one, fetch_all, execute_write
from auth import AuthManager
from exam import ExamManager
from analytics import AnalyticsManager
from reports import ReportGenerator

# Initialize Flask app
app = Flask(__name__)
session_dir = os.environ.get('SESSION_FILE_DIR', '/tmp/flask_session')
os.makedirs(session_dir, exist_ok=True)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = session_dir
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize session
Session(app)


def ensure_admin_user():
    """Create an admin account at startup if one does not already exist."""
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')

    existing_admin = fetch_one(
        "SELECT id FROM users WHERE username = ? AND role = 'admin'",
        (admin_username,)
    )

    if not existing_admin:
        AuthManager.create_user(admin_username, admin_password, role='admin')


def ensure_sample_exams():
    """Seed sample exams and questions if there are no exams yet."""
    existing_exam = fetch_one("SELECT id FROM exams LIMIT 1")
    if existing_exam:
        return

    exams_to_seed = [
        {
            'name': 'Python Basics',
            'description': 'Core Python syntax, data types, and functions.',
            'duration': 30,
            'questions': [
                ('What is the output of print(2 ** 3)?', '6', '8', '9', '16', 'B', 'Operators', 'Easy'),
                ('Which keyword is used to define a function in Python?', 'func', 'function', 'def', 'lambda', 'C', 'Syntax', 'Easy'),
                ('Which type stores key-value pairs?', 'list', 'set', 'tuple', 'dict', 'D', 'Data Structures', 'Easy'),
                ('Which method adds one item to a list?', 'append()', 'add()', 'insert_all()', 'push()', 'A', 'Collections', 'Medium'),
                ('What does len([1, 2, 3]) return?', '2', '3', '4', 'Error', 'B', 'Built-ins', 'Easy'),
            ],
        },
        {
            'name': 'Web Development Fundamentals',
            'description': 'HTML, CSS, HTTP, and basic web concepts.',
            'duration': 25,
            'questions': [
                ('Which tag is used for hyperlinks in HTML?', '<link>', '<a>', '<href>', '<p>', 'B', 'HTML', 'Easy'),
                ('Which HTTP method is commonly used to create data?', 'GET', 'POST', 'DELETE', 'HEAD', 'B', 'HTTP', 'Easy'),
                ('What does CSS stand for?', 'Computer Style Sheets', 'Creative Style Syntax', 'Cascading Style Sheets', 'Colorful Style Sheets', 'C', 'CSS', 'Easy'),
                ('Which status code means Not Found?', '200', '301', '404', '500', 'C', 'HTTP', 'Easy'),
                ('Which property changes text color in CSS?', 'font-style', 'text-color', 'color', 'foreground', 'C', 'CSS', 'Medium'),
            ],
        },
        {
            'name': 'General Aptitude',
            'description': 'Logical reasoning and quantitative basics.',
            'duration': 20,
            'questions': [
                ('If 5x = 20, what is x?', '2', '4', '5', '10', 'B', 'Math', 'Easy'),
                ('Find the next number: 2, 4, 8, 16, ?', '18', '24', '32', '34', 'C', 'Series', 'Easy'),
                ('A train travels 60 km in 1 hour. Its speed is?', '60 km/h', '30 km/h', '90 km/h', '120 km/h', 'A', 'Speed', 'Easy'),
                ('If all roses are flowers and some flowers fade quickly, which is true?', 'All roses fade quickly', 'Some roses may fade quickly', 'No roses are flowers', 'Roses are never flowers', 'B', 'Logic', 'Medium'),
                ('What is 15% of 200?', '20', '25', '30', '35', 'C', 'Percentages', 'Easy'),
            ],
        },
    ]

    for exam_data in exams_to_seed:
        execute_write(
            """
            INSERT INTO exams (exam_name, description, duration_minutes, passing_percentage, total_questions)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                exam_data['name'],
                exam_data['description'],
                exam_data['duration'],
                50,
                len(exam_data['questions'])
            )
        )

        exam_row = fetch_one(
            "SELECT id FROM exams WHERE exam_name = ? ORDER BY id DESC LIMIT 1",
            (exam_data['name'],)
        )
        if not exam_row:
            continue

        exam_id = exam_row[0]
        for question in exam_data['questions']:
            execute_write(
                """
                INSERT INTO questions
                (exam_id, question, option_a, option_b, option_c, option_d, correct_option, category, difficulty)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (exam_id, *question)
            )

# Create database tables on startup
with app.app_context():
    create_tables()
    ensure_admin_user()
    ensure_sample_exams()


# ======================= DECORATORS =======================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['user'].get('role') != 'student':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ======================= AUTH ROUTES =======================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        user = AuthManager.authenticate_user(username, password)
        
        if user:
            session['user'] = user
            session.permanent = remember_me
            
            # Create admin session for admin users
            if user['role'] == 'admin':
                admin_session = AuthManager.create_admin_session(
                    user['id'],
                    request.remote_addr,
                    request.headers.get('User-Agent', '')
                )
                session['admin_session'] = admin_session
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('select_exam'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or len(username) < 3:
            return render_template('register.html', error='Username must be at least 3 characters')
        
        if len(password) < 6:
            return render_template('register.html', error='Password must be at least 6 characters')
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        
        # Check if user exists
        existing = fetch_one("SELECT id FROM users WHERE username = ?", (username,))
        if existing:
            return render_template('register.html', error='Username already exists')
        
        # Create user
        AuthManager.create_user(username, password, role='student')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    if 'admin_session' in session:
        AuthManager.revoke_admin_session(session['admin_session'])
    session.clear()
    return redirect(url_for('login'))


# ======================= STUDENT ROUTES =======================

@app.route('/student/exams')
@student_required
def select_exam():
    exams = fetch_all("SELECT id, exam_name, description, duration_minutes FROM exams ORDER BY id DESC")
    return render_template('select_exam.html', exams=exams)


@app.route('/student/exam/<int:exam_id>')
@student_required
def take_exam(exam_id):
    username = session['user']['username']
    
    # Check if already attempted
    existing_result = fetch_one(
        "SELECT id FROM results WHERE username = ? AND exam_id = ? LIMIT 1",
        (username, exam_id)
    )
    
    if existing_result:
        return redirect(url_for('view_result', exam_id=exam_id))
    
    # Create session
    exam_token = AuthManager.create_session_token(username, exam_id)
    exam_config = ExamManager.get_exam_config(exam_id)
    
    if not exam_config:
        return "Exam not found", 404
    
    # Get questions with randomization
    questions = ExamManager.get_exam_questions(
        exam_id,
        randomize=exam_config['randomize_questions'],
        shuffle_options=exam_config['shuffle_options']
    )
    
    return render_template(
        'exam.html',
        exam=exam_config,
        questions=questions,
        session_token=exam_token
    )


@app.route('/student/submit-exam', methods=['POST'])
@student_required
def submit_exam():
    data = request.get_json()
    username = session['user']['username']
    exam_id = int(data.get('exam_id'))
    exam_token = data.get('session_token')
    answers = data.get('answers', {})
    time_taken_minutes = float(data.get('time_taken', 0))
    
    # Validate session
    if not AuthManager.validate_session_token(exam_token, exam_id):
        return jsonify({'error': 'Invalid session'}), 403
    
    # Submit answers
    result = ExamManager.submit_answers(username, exam_id, answers)
    
    # Update time taken
    if result:
        execute_write(
            "UPDATE results SET time_taken_minutes = ? WHERE username = ? AND exam_id = ?",
            (time_taken_minutes, username, exam_id)
        )
        
        # Update analytics
        AnalyticsManager.update_analytics(exam_id)
    
    # End session
    AuthManager.end_session(exam_token)
    
    return jsonify(result)


@app.route('/student/result/<int:exam_id>')
@student_required
def view_result(exam_id):
    username = session['user']['username']
    try:
        result = ExamManager.get_student_result(username, exam_id)
    except Exception:
        app.logger.exception("Failed to build detailed result for user=%s exam_id=%s", username, exam_id)
        basic_result = fetch_one(
            """
            SELECT score,
                   COALESCE(percentage, 0),
                   COALESCE(status, 'FAIL'),
                   COALESCE(time_taken_minutes, 0),
                   COALESCE(question_count, 0),
                   COALESCE(correct_count, score),
                   submitted_at
            FROM results
            WHERE username = ? AND exam_id = ?
            ORDER BY submitted_at DESC
            LIMIT 1
            """,
            (username, exam_id)
        )

        result = None
        if basic_result:
            result = {
                'score': basic_result[0],
                'percentage': basic_result[1],
                'status': basic_result[2],
                'time_taken_minutes': basic_result[3],
                'question_count': basic_result[4],
                'correct_count': basic_result[5],
                'submitted_at': basic_result[6],
                'details': []
            }
    
    if not result:
        return "Result not found", 404
    
    exam = fetch_one("SELECT exam_name, description, passing_percentage FROM exams WHERE id = ?", (exam_id,))
    exam_passing_percentage = exam[2] if exam else 50

    return render_template(
        'result.html',
        result=result,
        exam=exam,
        exam_id=exam_id,
        exam_passing_percentage=exam_passing_percentage
    )


@app.route('/student/dashboard')
@student_required
def student_dashboard():
    username = session['user']['username']
    dashboard = AnalyticsManager.get_student_dashboard(username)
    return render_template('student.html', dashboard=dashboard)


@app.route('/student/report/pdf/<int:exam_id>')
@student_required
def download_result_pdf(exam_id):
    username = session['user']['username']
    pdf_data = ReportGenerator.generate_student_report_pdf(username, exam_id)
    
    if not pdf_data:
        return "Report not found", 404
    
    return send_file(
        BytesIO(pdf_data),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'{username}_exam_{exam_id}_result.pdf'
    )


@app.route('/student/report/csv')
@student_required
def download_results_csv():
    username = session['user']['username']
    csv_data = ReportGenerator.generate_student_results_csv(username)
    
    return send_file(
        BytesIO(csv_data.encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{username}_results.csv'
    )


# ======================= ADMIN ROUTES =======================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    dashboard = AnalyticsManager.get_admin_dashboard()
    return render_template('admin_dashboard.html', dashboard=dashboard)


@app.route('/admin/exams')
@admin_required
def manage_exams():
    exams = fetch_all(
        """
        SELECT id, exam_name, description, duration_minutes, total_questions
        FROM exams ORDER BY id DESC
        """
    )
    return render_template('admin.html', exams=exams)


@app.route('/admin/exam/create', methods=['GET', 'POST'])
@admin_required
def create_exam():
    if request.method == 'POST':
        exam_name = request.form.get('exam_name')
        description = request.form.get('description', '')
        duration_minutes = int(request.form.get('duration_minutes', 30))
        passing_percentage = int(request.form.get('passing_percentage', 50))
        total_questions = int(request.form.get('total_questions', 10))
        
        execute_write(
            """
            INSERT INTO exams (exam_name, description, duration_minutes, 
                             passing_percentage, total_questions, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (exam_name, description, duration_minutes, passing_percentage, 
             total_questions, datetime.now().isoformat())
        )
        
        return redirect(url_for('manage_exams'))
    
    return render_template('create_exam.html')


@app.route('/admin/exam/<int:exam_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_exam(exam_id):
    if request.method == 'POST':
        exam_name = request.form.get('exam_name')
        description = request.form.get('description', '')
        duration_minutes = int(request.form.get('duration_minutes', 30))
        passing_percentage = int(request.form.get('passing_percentage', 50))
        
        execute_write(
            """
            UPDATE exams
            SET exam_name = ?, description = ?, duration_minutes = ?, 
                passing_percentage = ?
            WHERE id = ?
            """,
            (exam_name, description, duration_minutes, passing_percentage, exam_id)
        )
        
        return redirect(url_for('manage_exams'))
    
    exam = fetch_one(
        "SELECT id, exam_name, description, duration_minutes, passing_percentage FROM exams WHERE id = ?",
        (exam_id,)
    )
    
    return render_template('edit_exam.html', exam=exam)


@app.route('/admin/exam/<int:exam_id>/questions', methods=['GET', 'POST'])
@admin_required
def manage_questions(exam_id):
    if request.method == 'POST':
        question_text = request.form.get('question')
        option_a = request.form.get('option_a')
        option_b = request.form.get('option_b')
        option_c = request.form.get('option_c')
        option_d = request.form.get('option_d')
        correct_option = request.form.get('correct_option')
        category = request.form.get('category', 'General')
        difficulty = request.form.get('difficulty', 'Medium')
        
        execute_write(
            """
            INSERT INTO questions (exam_id, question, option_a, option_b, option_c, option_d,
                                  correct_option, category, difficulty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (exam_id, question_text, option_a, option_b, option_c, option_d,
             correct_option, category, difficulty)
        )
        
        return redirect(url_for('manage_questions', exam_id=exam_id))
    
    exam = fetch_one("SELECT exam_name FROM exams WHERE id = ?", (exam_id,))
    questions = fetch_all(
        "SELECT id, question, correct_option, category, difficulty FROM questions WHERE exam_id = ?",
        (exam_id,)
    )
    
    return render_template('questions.html', exam_id=exam_id, exam_name=exam[0] if exam else '', questions=questions)


@app.route('/admin/question/<int:question_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_question(question_id):
    if request.method == 'POST':
        question_text = request.form.get('question')
        option_a = request.form.get('option_a')
        option_b = request.form.get('option_b')
        option_c = request.form.get('option_c')
        option_d = request.form.get('option_d')
        correct_option = request.form.get('correct_option')
        category = request.form.get('category', 'General')
        difficulty = request.form.get('difficulty', 'Medium')
        
        execute_write(
            """
            UPDATE questions
            SET question = ?, option_a = ?, option_b = ?, option_c = ?, option_d = ?,
                correct_option = ?, category = ?, difficulty = ?
            WHERE id = ?
            """,
            (question_text, option_a, option_b, option_c, option_d,
             correct_option, category, difficulty, question_id)
        )
        
        question = fetch_one("SELECT exam_id FROM questions WHERE id = ?", (question_id,))
        return redirect(url_for('manage_questions', exam_id=question[0]))
    
    question = fetch_one(
        "SELECT id, exam_id, question, option_a, option_b, option_c, option_d, correct_option, category, difficulty FROM questions WHERE id = ?",
        (question_id,)
    )
    
    return render_template('edit_question.html', question=question)


@app.route('/admin/exam/<int:exam_id>/analytics')
@admin_required
def exam_analytics(exam_id):
    stats = AnalyticsManager.get_exam_statistics(exam_id)
    question_perf = AnalyticsManager.get_question_performance(exam_id)
    category_perf = AnalyticsManager.get_category_performance(exam_id)
    difficulty_perf = AnalyticsManager.get_difficulty_performance(exam_id)
    
    exam = fetch_one("SELECT exam_name FROM exams WHERE id = ?", (exam_id,))
    
    return render_template(
        'analytics.html',
        exam_id=exam_id,
        exam_name=exam[0] if exam else '',
        stats=stats,
        question_perf=question_perf,
        category_perf=category_perf,
        difficulty_perf=difficulty_perf
    )


@app.route('/admin/exam/<int:exam_id>/report/pdf')
@admin_required
def download_exam_analytics_pdf(exam_id):
    pdf_data = ReportGenerator.generate_exam_analytics_pdf(exam_id)
    
    if not pdf_data:
        return "Report not found", 404
    
    return send_file(
        BytesIO(pdf_data),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'exam_{exam_id}_analytics.pdf'
    )


@app.route('/admin/exam/<int:exam_id>/report/csv')
@admin_required
def download_exam_results_csv(exam_id):
    csv_data = ReportGenerator.generate_exam_results_csv(exam_id)
    
    return send_file(
        BytesIO(csv_data.encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'exam_{exam_id}_results.csv'
    )


@app.route('/admin/students')
@admin_required
def manage_students():
    students = fetch_all(
        "SELECT id, username, created_at FROM users WHERE role = 'student' ORDER BY id DESC"
    )
    return render_template('students.html', students=students)


# ======================= HEALTH CHECK =======================

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


# ======================= ERROR HANDLERS =======================

@app.errorhandler(404)
def not_found(error):
    return '<h2>404 - Page Not Found</h2><p><a href="/">Go Home</a></p>', 404


@app.errorhandler(500)
def internal_error(error):
    app.logger.exception('Unhandled server error at %s: %s', request.path, error)
    return '<h2>500 - Server Error</h2><p>Something went wrong. Please try again.</p>', 500


# ======================= CONTEXT PROCESSORS =======================

@app.context_processor
def inject_user():
    return {'user': session.get('user')}


if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', False), host='0.0.0.0', port=10000)
