import sqlite3


def connect_db():
    conn = sqlite3.connect("exam.db", timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
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
        exam_name TEXT
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
        correct_option TEXT
    )
   """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        exam_id INTEGER,
        score INTEGER
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        exam_id INTEGER,
        question_id INTEGER,
        selected_option TEXT,
        correct_option TEXT
    )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username_role ON users(username, role)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_exam_id ON questions(exam_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_username_exam ON results(username, exam_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_answers_username_exam ON answers(username, exam_id)")


    conn.commit()
    conn.close()
