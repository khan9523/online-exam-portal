# Online Exam System - Complete Edition

A comprehensive Flask-based online examination platform with advanced features including timer-based exams, randomized questions, secure authentication, detailed analytics, and report generation.

## 🎯 Features

### 🔐 Security & Authentication
- **Password Hashing**: Industry-standard bcrypt password hashing with 12 rounds
- **Session Protection**: Secure session management with HTTP-only cookies
- **Admin Sessions**: Tracked admin sessions with IP and user agent
- **Token-Based Exam Access**: Unique session tokens for each exam attempt

### ⏱️ Exam Management
- **Timer-Based Exams**: Countdown timer with auto-submit at expiration
- **Auto-Submit**: Automatic submission when time expires
- **Exam Configuration**:
  - Custom duration per exam
  - Passing percentage threshold
  - Total question count
  - Randomization and shuffling options

### 🎲 Question Features
- **Question Randomization**: Optional random order of questions
- **Option Shuffling**: Randomized answer options while tracking correct answers
- **Question Categories**: Organize questions by topic
- **Difficulty Levels**: Easy, Medium, Hard classifications
- **Question Performance**: Track which questions students struggle with

### 📊 Analytics & Dashboards
- **Student Dashboard**: Personal performance summary and exam history
- **Admin Dashboard**: System-wide statistics and exam overview
- **Detailed Analytics**:
  - Question-level performance metrics
  - Category-wise performance analysis
  - Difficulty-level performance tracking
  - Pass/fail statistics
  - Average scores and time tracking

### 📄 Report Generation
- **PDF Reports**:
  - Student result reports with detailed answers
  - Exam analytics reports for admins
- **CSV Exports**:
  - Student results export
  - Exam results export with all student attempts
- **Professional Formatting**: Business-ready report layouts

## 🚀 Installation & Setup

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Initialize Database
```bash
python init_db.py
```

This will:
- Create database tables
- Create a default admin account (admin / admin123)
- Add sample Python exam with questions

### Step 3: Run the Application
```bash
python app.py
```

The application will be available at: `http://127.0.0.1:10000/login`

## 📚 Usage

### Admin Panel (admin / admin123)

1. **Dashboard**: View system statistics and recent exams
2. **Manage Exams**: Create, edit, and view exams
3. **Manage Questions**: Add questions with randomization options
4. **Manage Students**: View registered students
5. **Analytics**: View detailed exam analytics and performance metrics
6. **Reports**: Download PDF and CSV reports

### Student Portal

1. **Select Exam**: Browse available exams
2. **Take Exam**: 
   - Timer countdown
   - Randomized questions and options
   - Real-time progress tracking
3. **View Results**: Detailed review of answers
4. **Dashboard**: Personal performance statistics
5. **Download Reports**: PDF result and CSV exports

## 🏗️ Project Structure

```
OnlineExamSystem/
├── app.py                 # Main Flask application
├── auth.py               # Authentication & security module
├── database.py           # Database connection & schema
├── exam.py              # Exam logic & randomization
├── analytics.py         # Analytics & dashboards
├── reports.py           # PDF & CSV report generation
├── requirements.txt      # Python dependencies
├── init_db.py           # Database initialization
├── templates/           # Jinja2 HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── select_exam.html
│   ├── exam.html
│   ├── result.html
│   ├── student.html
│   ├── admin_dashboard.html
│   ├── admin.html
│   ├── edit_exam.html
│   ├── questions.html
│   ├── edit_question.html
│   ├── analytics.html
│   ├── students.html
│   └── 404.html, 500.html
├── static/
│   └── style.css         # Modern responsive styling
└── scripts/
    └── health_check.py   # Health endpoint for deployment

```

## 🔧 Configuration

### Environment Variables
- `SECRET_KEY`: Flask session secret (set for production)
- `FLASK_DEBUG`: Debug mode (False for production)

### File Storage
- SQLite database: `exam.db`
- Session files: `flask_session/` directory

### Security Settings
- Secure cookies enabled
- HTTP-only cookies enabled
- Same-site cookie policy: Lax

## 📊 Database Schema

### Tables
- **users**: Student and admin accounts with hashed passwords
- **exams**: Exam configurations and metadata
- **questions**: Questions with options and difficulty levels
- **results**: Student exam attempt results
- **answers**: Detailed answer records for analytics
- **exam_sessions**: Active exam session tracking
- **admin_sessions**: Admin login session tracking
- **analytics**: Cached analytics data
- **exam_templates**: Exam generation rules

## 🎨 Design Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Modern UI**: Clean, professional interface with gradients
- **Color-Coded Status**: Visual indicators for pass/fail
- **Progress Tracking**: Visual progress bar during exam
- **Real-time Timer**: Countdown timer with critical warnings

## 🔒 Security Checklist

✅ Password hashing with bcrypt (12 rounds)
✅ Session tokens for exam access
✅ HTTP-only cookies
✅ Secure cookie transmission
✅ Admin session tracking
✅ Input validation
✅ CSRF protection ready
✅ SQL injection prevention (parameterized queries)

## 📝 API Endpoints

### Authentication
- `POST /login` - User login
- `POST /register` - Student registration
- `GET /logout` - User logout

### Student Endpoints
- `GET /student/exams` - Browse exams
- `GET /student/exam/<id>` - Start exam
- `POST /student/submit-exam` - Submit exam
- `GET /student/result/<id>` - View result
- `GET /student/dashboard` - Student dashboard
- `GET /student/report/pdf/<id>` - Download result PDF
- `GET /student/report/csv` - Download all results CSV

### Admin Endpoints
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/exams` - Manage exams
- `POST /admin/exam/create` - Create exam
- `GET /admin/exam/<id>/edit` - Edit exam
- `GET /admin/exam/<id>/questions` - Manage questions
- `POST /admin/exam/<id>/questions` - Add question
- `GET /admin/question/<id>/edit` - Edit question
- `GET /admin/exam/<id>/analytics` - View analytics
- `GET /admin/exam/<id>/report/pdf` - Download analytics PDF
- `GET /admin/exam/<id>/report/csv` - Download results CSV
- `GET /admin/students` - Manage students

### Health
- `GET /health` - Health check endpoint

## 🚀 Deployment

### Render.com (as configured in Procfile)
```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
```

### Docker (example)
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

## 📈 Performance Features

- SQLite WAL mode for concurrent access
- Indexed database queries for fast lookups
- Cached analytics data
- Efficient session management
- Optimized CSS and JavaScript

## 📞 Support & Troubleshooting

### Issue: "Module not found" error
**Solution**: Run `pip install -r requirements.txt` to install all dependencies

### Issue: Database locked
**Solution**: Delete `exam.db` and `init_db.py` to reset, or check for multiple processes

### Issue: Password authentication failing
**Solution**: Ensure bcrypt is installed: `pip install bcrypt`

## 🎓 Future Enhancements

- Two-factor authentication
- Proctored exam mode (webcam monitoring)
- Question bank management
- Batch student imports
- Email notifications
- Exam scheduling
- Certificate generation
- Mobile app

## 📄 License

This project is provided as-is for educational and commercial use.

## ✨ Changelog

### Version 2.0 (Current)
- ✅ Password hashing with bcrypt
- ✅ Timer-based auto-submit exams
- ✅ Question randomization and shuffling
- ✅ Admin session tracking
- ✅ Detailed analytics & dashboards
- ✅ PDF & CSV report generation
- ✅ Question categories & difficulty levels
- ✅ Exam templates & generation rules

### Version 1.0 (Previous)
- Basic exam and question management
- Student registration and login
- Basic results display

---

**Last Updated**: March 28, 2026