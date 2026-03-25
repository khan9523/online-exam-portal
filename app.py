
try:
    from flask import Flask, render_template, request, redirect, session, Response, flash  # type: ignore
except ImportError as e:
    raise ImportError("Flask not installed. Please run: pip install flask") from e

try:
    from werkzeug.security import generate_password_hash, check_password_hash  # type: ignore
except ImportError as e:
    raise ImportError("werkzeug not installed. Please run: pip install werkzeug") from e

import os
import csv
from database import (
    create_tables,
    connect_db,
    fetch_one,
    fetch_all,
    execute_write,
    execute_many,
    execute_batch,
)

app = Flask(__name__)
app.secret_key = "exam_secret_key"


def get_db_connection():
    return connect_db()


# Initialize database during worker startup (important for gunicorn/Render).
create_tables()


# -------------------- HOME --------------------
@app.route("/")
def home():
    return redirect("/login")


@app.route("/health")
def health():
    return {"status": "ok"}, 200


# -------------------- LOGIN --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        user = fetch_one(
            "SELECT * FROM users WHERE username=? AND role=?",
            (username, role)
        )

        if user and check_password_hash(user[2], password):
            session["username"] = username
            session["role"] = role

            if role == "admin":
                return redirect("/admin")
            else:
                return redirect("/student")
        else:
            error = "Invalid Login Credentials"

    return render_template("login.html", error=error)





@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        execute_write(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), "student")
        )

        flash("Registration successful! Please login.")
        return redirect("/login")

    return render_template("register.html")



@app.route("/create_exam", methods=["POST"])
def create_exam():
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")

    exam_name = request.form["exam_name"]
    execute_write("INSERT INTO exams (exam_name) VALUES (?)", (exam_name,))

    return redirect("/admin")





# -------------------- ADMIN PANEL --------------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    message = None

    # Add Question
    if request.method == "POST":
        exam_id = request.form["exam_id"]
        question = request.form["question"]
        option_a = request.form["option_a"]
        option_b = request.form["option_b"]
        option_c = request.form["option_c"]
        option_d = request.form["option_d"]
        correct_option = request.form["correct_option"]

        cursor.execute("""
            INSERT INTO questions 
            (exam_id, question, option_a, option_b, option_c, option_d, correct_option)

            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (exam_id, question, option_a, option_b, option_c, option_d, correct_option))

        conn.commit()
        message = "Question added successfully"

    # Fetch results
    cursor.execute("SELECT username, score FROM results")
    results = cursor.fetchall()

    # Fetch all questions
    cursor.execute("SELECT * FROM questions")
    all_questions = cursor.fetchall()


    # ---------------- DASHBOARD STATISTICS ----------------
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='student'")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM questions")
    total_questions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM results")
    total_attempts = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM exams")
    exams = cursor.fetchall()


    conn.close()

    return render_template(
    "admin.html",
    message=message,
    results=results,
    questions=all_questions,
    exams=exams,
    total_students=total_students,
    total_questions=total_questions,
    total_attempts=total_attempts
    )


@app.route("/upload_questions", methods=["POST"])
def upload_questions():
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")

    file = request.files["file"]

    csv_data = csv.reader(file.stream.read().decode("UTF-8").splitlines())
    next(csv_data)  # Skip header row

    rows = [tuple(row) for row in csv_data]
    if rows:
        execute_many(
            """
            INSERT INTO questions
            (exam_id, question, option_a, option_b, option_c, option_d, correct_option)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

    return redirect("/admin")

# -------------------- STUDENT EXAM --------------------
@app.route("/student", methods=["GET", "POST"])
def student():
    if "role" not in session or session["role"] != "student":
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch exams
    cursor.execute("SELECT * FROM exams")
    exams = cursor.fetchall()

    # If exam selected
    exam_id = request.args.get("exam_id")

    exam_name = None

    if exam_id:
        results_detail = []
        cursor.execute("SELECT exam_name FROM exams WHERE id=?", (exam_id,))
        exam_name = cursor.fetchone()[0]

    if exam_id:
        results_detail = []
        cursor.execute("SELECT * FROM questions WHERE exam_id=?", (exam_id,))
        questions = cursor.fetchall()

        # prevent reattempt
        cursor.execute(
            "SELECT * FROM results WHERE username=? AND exam_id=?",
            (session["username"], exam_id)
        )
        existing_result = cursor.fetchone()

        if existing_result:

    # Get exam_id from results table
            score = int(existing_result[3])
            exam_id = existing_result[2]

            total = len(questions)
            percentage = (score / total) * 100 if total > 0 else 0
            status = "PASS" if percentage >= 40 else "FAIL"

    # Load saved answers
            cursor.execute("""
                SELECT q.question, a.selected_option, a.correct_option
                FROM answers a
                JOIN questions q ON a.question_id = q.id
                WHERE a.username=? AND a.exam_id=?
            """, (session["username"], exam_id))

            rows = cursor.fetchall()
            results_detail = []

            for row in rows:
                question_text = row[0]
                selected = row[1]
                correct = row[2]

                results_detail.append({
                    "question": question_text,
                    "selected": selected,
                    "correct": correct,
                    "is_correct": selected == correct
                })

            conn.close()

            return render_template(
                "result.html",
                exam_name=exam_name,
                score=score,
                total=total,
                percentage=round(percentage, 2),
                status=status,
                details=results_detail
            )

        if request.method == "POST":
            score = 0
            results_detail = []

            for q in questions:
                q_id = str(q[0])
                correct = q[7]
                selected = request.form.get(q_id)

                is_correct = selected == correct

                if is_correct:
                    score += 1

                    cursor.execute(
                        "INSERT INTO answers (username, exam_id, question_id, selected_option, correct_option) VALUES (?, ?, ?, ?, ?)",
                        (session["username"], exam_id, q[0], selected, correct)
                    )

                options = {
                    "A": q[3],
                    "B": q[4],
                    "C": q[5],
                    "D": q[6]
                }

                results_detail.append({
                    "question": q[2],
                    "selected": options.get(selected, "Not Answered"),
                    "correct": options.get(correct),
                    "is_correct": is_correct
                })

            cursor.execute(
                "INSERT INTO results (username, exam_id, score) VALUES (?, ?, ?)",
                (session["username"], exam_id, score)
            )
            conn.commit()

            total = len(questions)
            percentage = (score / total) * 100 if total > 0 else 0

            conn.close()
            return render_template(
                "result.html",
                 exam_name=exam_name,
                 score=score,
                 total=total,
                 percentage=round(percentage, 2),
                 details=results_detail
            )

        conn.close()
        return render_template("student.html", questions=questions)

    conn.close()
    return render_template("select_exam.html", exams=exams)



# -------------------- CLEAR RESULTS --------------------
@app.route("/clear_results", methods=["POST"])
def clear_results():
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")

    execute_write("DELETE FROM results")

    return redirect("/admin")


@app.route("/delete_question/<int:q_id>")
def delete_question(q_id):
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")

    execute_write("DELETE FROM questions WHERE id=?", (q_id,))

    return redirect("/admin")



@app.route("/edit_question/<int:q_id>", methods=["GET", "POST"])
def edit_question(q_id):
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")

    if request.method == "POST":
        question = request.form["question"]
        option_a = request.form["option_a"]
        option_b = request.form["option_b"]
        option_c = request.form["option_c"]
        option_d = request.form["option_d"]
        correct_option = request.form["correct_option"]

        execute_write("""
            UPDATE questions
            SET question=?, option_a=?, option_b=?, option_c=?, option_d=?, correct_option=?
            WHERE id=?
        """, (question, option_a, option_b, option_c, option_d, correct_option, q_id))
        return redirect("/admin")

    question_data = fetch_one("SELECT * FROM questions WHERE id=?", (q_id,))

    return render_template("edit_question.html", q=question_data)




@app.route("/export_results")
def export_results():
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")

    data = fetch_all("SELECT username, score FROM results")

    def generate():
        yield "Username,Score\n"
        for row in data:
            yield f"{row[0]},{row[1]}\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=results.csv"}
    )


@app.route("/delete_exam/<int:exam_id>")
def delete_exam(exam_id):

    if "role" not in session or session["role"] != "admin":
        return redirect("/login")

    execute_batch([
        ("DELETE FROM answers WHERE exam_id=?", (exam_id,)),
        ("DELETE FROM results WHERE exam_id=?", (exam_id,)),
        ("DELETE FROM questions WHERE exam_id=?", (exam_id,)),
        ("DELETE FROM exams WHERE id=?", (exam_id,)),
    ])

    return redirect("/admin")



# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# -------------------- RUN APP --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


