import csv
import json
from io import StringIO, BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from database import fetch_all, fetch_one


class ReportGenerator:
    """Generate PDF and CSV reports for students and administrators."""
    
    @staticmethod
    def generate_student_report_pdf(username, exam_id):
        """Generate a PDF report of student's exam result."""
        from exam import ExamManager
        
        result = ExamManager.get_student_result(username, exam_id)
        if not result:
            return None
        
        exam = fetch_one("SELECT exam_name, description FROM exams WHERE id = ?", (exam_id,))
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=1
        )
        elements.append(Paragraph("Exam Result Report", title_style))
        
        # Exam Info
        exam_name = exam[0] if exam else "N/A"
        elements.append(Spacer(1, 0.2*inch))
        info_data = [
            ["Student Name:", username],
            ["Exam Name:", exam_name],
            ["Date Submitted:", result['submitted_at']],
            ["Status:", f"<b>{result['status']}</b>"],
            ["Score:", f"{result['correct_count']}/{result['question_count']}"],
            ["Percentage:", f"{result['percentage']}%"],
            ["Time Taken:", f"{result['time_taken_minutes']:.1f} minutes"]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        elements.append(info_table)
        
        # Detailed Answer Review
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("Answer Review", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        
        for idx, detail in enumerate(result['details'], 1):
            status_text = "✓ Correct" if detail['is_correct'] else "✗ Incorrect"
            status_color = colors.green if detail['is_correct'] else colors.red
            
            question_para = Paragraph(
                f"<b>Question {idx}: {detail['question_text']}</b>",
                styles['Heading3']
            )
            elements.append(question_para)
            
            # Options table
            options_data = [
                ["Option", "Answer", "Your Answer", "Correct?"]
            ]
            
            for key in ['A', 'B', 'C', 'D']:
                your_answer = "●" if detail['selected_option'] == key else ""
                is_selected = detail['selected_option'] == key
                correct = detail['correct_option'] == key
                
                marker = ""
                if correct:
                    marker = "✓"
                elif is_selected and not correct:
                    marker = "✗"
                
                options_data.append([
                    key,
                    detail['options'][key],
                    your_answer,
                    marker
                ])
            
            options_table = Table(options_data, colWidths=[0.5*inch, 3*inch, 0.8*inch, 0.8*inch])
            options_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
            ]))
            elements.append(options_table)
            elements.append(Spacer(1, 0.2*inch))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def generate_exam_analytics_pdf(exam_id):
        """Generate a PDF report of exam analytics for admin."""
        from analytics import AnalyticsManager
        
        exam = fetch_one("SELECT exam_name, description, total_questions FROM exams WHERE id = ?", (exam_id,))
        if not exam:
            return None
        
        stats = AnalyticsManager.get_exam_statistics(exam_id)
        question_perf = AnalyticsManager.get_question_performance(exam_id)
        category_perf = AnalyticsManager.get_category_performance(exam_id)
        difficulty_perf = AnalyticsManager.get_difficulty_performance(exam_id)
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=20,
            alignment=1
        )
        elements.append(Paragraph(f"Exam Analytics: {exam[0]}", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Overview Statistics
        elements.append(Paragraph("Overview Statistics", styles['Heading2']))
        stats_data = [
            ["Metric", "Value"],
            ["Total Attempts", str(stats['total_attempts'])],
            ["Average Score", f"{stats['average_score']}%"],
            ["Pass Rate", f"{stats['pass_rate']}%"],
            ["Average Time", f"{stats['average_time_minutes']} min"],
            ["Pass Count", str(stats['pass_count'])],
            ["Fail Count", str(stats['fail_count'])]
        ]
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Category Performance
        if category_perf:
            elements.append(Paragraph("Performance by Category", styles['Heading2']))
            cat_data = [["Category", "Total Questions", "Success Rate"]]
            for cat in category_perf:
                cat_data.append([
                    cat['category'],
                    str(cat['total_questions']),
                    f"{cat['success_rate']}%"
                ])
            cat_table = Table(cat_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
            cat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            elements.append(cat_table)
            elements.append(Spacer(1, 0.2*inch))
        
        # Difficulty Performance
        if difficulty_perf:
            elements.append(PageBreak())
            elements.append(Paragraph("Performance by Difficulty", styles['Heading2']))
            diff_data = [["Difficulty", "Total Questions", "Success Rate"]]
            for diff in difficulty_perf:
                diff_data.append([
                    diff['difficulty'],
                    str(diff['total_questions']),
                    f"{diff['success_rate']}%"
                ])
            diff_table = Table(diff_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
            diff_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            elements.append(diff_table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def generate_student_results_csv(username):
        """Generate CSV report of all student results."""
        results = fetch_all(
            """
            SELECT exam_id, score, percentage, status, time_taken_minutes, submitted_at
            FROM results
            WHERE username = ?
            ORDER BY submitted_at DESC
            """,
            (username,)
        )
        
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            "Exam Name", "Score", "Percentage", "Status", 
            "Time Taken (min)", "Submitted At"
        ])
        
        for r in results:
            exam_id, score, percentage, status, time_taken, submitted = r
            exam = fetch_one("SELECT exam_name FROM exams WHERE id = ?", (exam_id,))
            exam_name = exam[0] if exam else f"Exam {exam_id}"
            
            writer.writerow([
                exam_name,
                score,
                f"{percentage}%",
                status,
                f"{time_taken:.1f}" if time_taken else "N/A",
                submitted
            ])
        
        return output.getvalue()
    
    @staticmethod
    def generate_exam_results_csv(exam_id):
        """Generate CSV report of all results for an exam."""
        results = fetch_all(
            """
            SELECT username, score, percentage, status, time_taken_minutes, submitted_at
            FROM results
            WHERE exam_id = ?
            ORDER BY submitted_at DESC
            """,
            (exam_id,)
        )
        
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            "Student", "Score", "Percentage", "Status", 
            "Time Taken (min)", "Submitted At"
        ])
        
        for r in results:
            username, score, percentage, status, time_taken, submitted = r
            writer.writerow([
                username,
                score,
                f"{percentage}%",
                status,
                f"{time_taken:.1f}" if time_taken else "N/A",
                submitted
            ])
        
        return output.getvalue()
