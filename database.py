import os
import sqlite3


def _get_database_path():
    # Allow explicit override first.
    explicit_path = os.environ.get("DATABASE_PATH")
    if explicit_path:
        return explicit_path

    # Prefer Render persistent disk when mounted.
    render_disk = os.environ.get("RENDER_DISK_PATH") or os.environ.get("RENDER_DISK_MOUNT_PATH")
    if render_disk:
        os.makedirs(render_disk, exist_ok=True)
        return os.path.join(render_disk, "exam.db")

    # Use a writable temp path in containerized environments when no disk is mounted.
    if os.name != "nt":
        return "/tmp/exam.db"

    # Fallback to local project path for Windows development.
    return "exam.db"


def _add_column_if_missing(cursor, table_name, column_name, definition):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = {row[1] for row in cursor.fetchall()}
    if column_name not in columns:
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")
        except sqlite3.OperationalError as exc:
            # SQLite cannot add columns with non-constant defaults via ALTER TABLE.
            if "non-constant default" in str(exc).lower() and " default " in definition.lower():
                base_definition = definition.split(" DEFAULT ", 1)[0]
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {base_definition}")
            else:
                raise


def connect_db():
    db_path = _get_database_path()
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path, timeout=10)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError:
        # Some file systems do not support WAL; fallback to default journal mode.
        conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def fetch_one(query, params=()):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    return row


def fetch_all(query, params=()):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def execute_write(query, params=()):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()


def execute_many(query, rows):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.executemany(query, rows)
    conn.commit()
    conn.close()


def execute_batch(statements):
    conn = connect_db()
    cursor = conn.cursor()
    for query, params in statements:
        cursor.execute(query, params)
    conn.commit()
    conn.close()


def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        role TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_name TEXT,
        description TEXT DEFAULT '',
        duration_minutes INTEGER DEFAULT 30
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id INTEGER,
        question TEXT,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        correct_option TEXT,
        category TEXT DEFAULT 'General',
        difficulty TEXT DEFAULT 'Medium'
    )
   """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        exam_id INTEGER,
        score INTEGER,
        percentage REAL DEFAULT 0,
        status TEXT DEFAULT 'FAIL',
        submitted_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        exam_id INTEGER,
        question_id INTEGER,
        selected_option TEXT,
        correct_option TEXT,
        is_correct INTEGER DEFAULT 0
    )
    """)

    _add_column_if_missing(cursor, "exams", "description", "TEXT DEFAULT ''")
    _add_column_if_missing(cursor, "exams", "duration_minutes", "INTEGER DEFAULT 30")
    _add_column_if_missing(cursor, "questions", "category", "TEXT DEFAULT 'General'")
    _add_column_if_missing(cursor, "questions", "difficulty", "TEXT DEFAULT 'Medium'")
    _add_column_if_missing(cursor, "results", "percentage", "REAL DEFAULT 0")
    _add_column_if_missing(cursor, "results", "status", "TEXT DEFAULT 'FAIL'")
    _add_column_if_missing(cursor, "results", "submitted_at", "TEXT")
    _add_column_if_missing(cursor, "answers", "is_correct", "INTEGER DEFAULT 0")

    cursor.execute("UPDATE exams SET description = COALESCE(description, '')")
    cursor.execute("UPDATE exams SET duration_minutes = COALESCE(duration_minutes, 30)")
    cursor.execute("UPDATE questions SET category = COALESCE(category, 'General')")
    cursor.execute("UPDATE questions SET difficulty = COALESCE(difficulty, 'Medium')")
    cursor.execute("UPDATE results SET percentage = COALESCE(percentage, 0)")
    cursor.execute("UPDATE results SET status = COALESCE(status, 'FAIL')")
    cursor.execute("UPDATE results SET submitted_at = COALESCE(submitted_at, CURRENT_TIMESTAMP)")
    cursor.execute("UPDATE answers SET is_correct = COALESCE(is_correct, 0)")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username_role ON users(username, role)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_exam_id ON questions(exam_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_username_exam ON results(username, exam_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_answers_username_exam ON answers(username, exam_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_exam_id ON results(exam_id)")

    # New tables for enhanced features
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exam_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        exam_id INTEGER,
        session_token TEXT UNIQUE,
        start_time TEXT,
        end_time TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exam_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id INTEGER,
        total_questions INTEGER DEFAULT 10,
        questions_per_category TEXT,
        difficulty_distribution TEXT,
        randomize_questions INTEGER DEFAULT 1,
        shuffle_options INTEGER DEFAULT 1,
        passing_percentage INTEGER DEFAULT 50,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        session_token TEXT UNIQUE,
        ip_address TEXT,
        user_agent TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        expires_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id INTEGER,
        total_attempts INTEGER DEFAULT 0,
        average_score REAL DEFAULT 0,
        pass_rate REAL DEFAULT 0,
        average_time_minutes REAL DEFAULT 0,
        question_difficulty_stats TEXT,
        category_performance TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Add new columns to existing tables
    _add_column_if_missing(cursor, "users", "password_hash", "TEXT")
    _add_column_if_missing(cursor, "users", "created_at", "TEXT DEFAULT CURRENT_TIMESTAMP")
    _add_column_if_missing(cursor, "users", "is_active", "INTEGER DEFAULT 1")
    
    _add_column_if_missing(cursor, "exams", "randomize_questions", "INTEGER DEFAULT 1")
    _add_column_if_missing(cursor, "exams", "shuffle_options", "INTEGER DEFAULT 1")
    _add_column_if_missing(cursor, "exams", "passing_percentage", "INTEGER DEFAULT 50")
    _add_column_if_missing(cursor, "exams", "total_questions", "INTEGER DEFAULT 10")
    _add_column_if_missing(cursor, "exams", "created_at", "TEXT DEFAULT CURRENT_TIMESTAMP")
    
    _add_column_if_missing(cursor, "results", "time_taken_minutes", "REAL DEFAULT 0")
    _add_column_if_missing(cursor, "results", "question_count", "INTEGER DEFAULT 0")
    _add_column_if_missing(cursor, "results", "correct_count", "INTEGER DEFAULT 0")

    cursor.execute("UPDATE users SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP)")
    cursor.execute("UPDATE users SET is_active = COALESCE(is_active, 1)")
    cursor.execute("UPDATE exams SET randomize_questions = COALESCE(randomize_questions, 1)")
    cursor.execute("UPDATE exams SET shuffle_options = COALESCE(shuffle_options, 1)")
    cursor.execute("UPDATE exams SET passing_percentage = COALESCE(passing_percentage, 50)")
    cursor.execute("UPDATE exams SET total_questions = COALESCE(total_questions, 10)")
    cursor.execute("UPDATE exams SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP)")
    cursor.execute("UPDATE results SET time_taken_minutes = COALESCE(time_taken_minutes, 0)")
    cursor.execute("UPDATE results SET question_count = COALESCE(question_count, 0)")
    cursor.execute("UPDATE results SET correct_count = COALESCE(correct_count, 0)")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exam_sessions_token ON exam_sessions(session_token)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_sessions_token ON admin_sessions(session_token)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_exam_id ON analytics(exam_id)")

    conn.commit()
    conn.close()
