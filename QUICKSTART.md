# 🚀 Quick Start Guide

## Installation (2 minutes)

```bash
cd OnlineExamSystem

# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize database
python init_db.py

# 3. Run the app
python app.py
```

Open: http://127.0.0.1:10000/login

## 🔑 Default Credentials

**Admin Account**
- Username: `admin`
- Password: `admin123`

**Test Student Account** (create during registration)
- Register as any student

## 📋 First Steps

### As Admin:
1. Login with admin credentials
2. Go to Dashboard - see system statistics
3. Create an Exam:
   - Click "Create New Exam"
   - Set name, duration (30 min), passing % (50%)
4. Add Questions:
   - Select exam → "Questions"
   - Add 10+ questions with options
   - Set correct answer and difficulty
5. View Analytics:
   - See real-time exam statistics
   - Download PDF/CSV reports

### As Student:
1. Register for an account
2. Login
3. Click "Take Exam"
4. Answer questions (timer counts down)
5. Auto-submit or click Submit
6. View result and download PDF report

## ✨ Key Features to Try

### Timer-Based Exams
- Start an exam and watch the countdown timer
- When time expires, exam auto-submits automatically
- See time-taken in results

### Randomized Questions
- Take the same exam twice - questions appear in different order!
- Answer options are shuffled each time
- Correct answer still grades correctly

### Analytics
- Admin: Go to Analytics to see:
  - Which questions students struggle with
  - Performance by category
  - Pass rates and averages
  - Download comprehensive PDF reports

### Student Dashboard
- View all your exam attempts
- See your average score
- Download all results as CSV
- Download individual result PDFs

### Password Security
- Try login with wrong password - fails
- Passwords are hashed with bcrypt (never stored plain text)
- Try changing focus tabs - session remains secure

## 🎯 Common Tasks

### Create a New Exam
```
Admin → Create New Exam
→ Enter name, description, duration, passing %
→ Save
→ Add questions to it
```

### Add Questions
```
Exam → Questions
→ Click "Add New Question"
→ Enter question, options A-D
→ Select correct answer
→ Set category and difficulty
```

### Generate Reports
```
Admin: Exam → Analytics → Download PDF/CSV
or
Student: Dashboard → Download Report
```

### View Student Progress
```
Admin → Manage Students → See all registrations
Admin → Dashboard → See attempt statistics
Admin → Analytics → See per-question performance
```

## 🔒 Security Features Demo

1. **Password Security**
   - Admin/Student passwords are bcrypt hashed
   - Try resetting password - migration to new hash
   - Session expires after 8 hours

2. **Session Protection**
   - Cookies are HTTP-only (JavaScript can't access)
   - Browser tab isolation maintained
   - Logout immediately revokes session

3. **Exam Integrity**
   - Can only take exam once (auto-submit prevents resubmit)
   - Results are immutable after submission
   - Session token validates each submission

## 📊 Sample Data

Default database includes:
- Sample exam: "Python Basics"
- 5 sample questions
- Different difficulty levels
- Multiple categories

Try taking this exam to see all features in action!

## 🆘 Troubleshooting

**Port 10000 already in use?**
- Change in app.py: `port=10001`

**Import errors?**
- Run: `pip install --upgrade -r requirements.txt`

**Database locked?**
- Delete `exam.db` and re-run `python init_db.py`

**Forgot admin password?**
- Reset: `python init_db.py` creates new default

## 📚 Documentation

- `README.md` - Full documentation
- `IMPLEMENTATION.md` - Technical details
- Code comments - Inline documentation

## 🎓 Learning Path

1. **Day 1**: Create an exam with 10 questions
2. **Day 2**: Have students take it (timer works!)
3. **Day 3**: Review analytics and generate reports
4. **Day 4**: Test security features and customization

## 🚀 Production Deployment

When ready to deploy:

1. Set environment variables:
   ```bash
   export SECRET_KEY="your-random-secret-key"
   export FLASK_DEBUG="False"
   ```

2. Use production server:
   ```bash
   gunicorn app:app --bind 0.0.0.0:5000 --workers 4
   ```

3. Configure SSL/TLS

4. Set up database backups

5. Enable logging

## 📞 Need Help?

All features are documented:
- Hover over fields for hints
- Check README.md for details
- Code is well-commented
- Database schema is normalized

---

**Enjoy your Online Exam System! 🎉**

Version 2.0 | March 28, 2026
