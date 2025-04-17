# routes/reports.py
from flask import Blueprint, render_template, request, Response
from models import db, Book, Loan, Reader
from sqlalchemy import func
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
import io
from models import db, Genre, BookGenre
from datetime import date
import base64
import pandas as pd

report_bp = Blueprint('report_bp', __name__)

@report_bp.route('/reports')
def reports():
    return render_template('reports/index.html')


@report_bp.route('/reports/overdue')
def overdue_report():
    today = date.today()

    # получаем просроченные книги и вычисляем штраф
    overdue_loans = (
        db.session.query(
            Loan,
            Book.title,
            Reader.full_name,
            func.cast(today - Loan.due_date, db.Integer).label('days_overdue'),
            func.cast(today - Loan.due_date, db.Integer) * 0.50  # штраф 50 рублей за день
        )
        .join(Book, Loan.book_id == Book.ID)
        .join(Reader, Loan.reader_id == Reader.ID)
        .filter(Loan.return_date.is_(None), Loan.due_date < today)
        .all()
    )

    overdue_books = [
        {
            'title': title,
            'reader_name': reader_name,
            'issue_date': loan.issue_date,
            'due_date': loan.due_date,
            'days_overdue': int(days_overdue),
            'estimated_fine': float(fine)  # штраф будет вычислен
        }
        for loan, title, reader_name, days_overdue, fine in overdue_loans
    ]

    if request.args.get('export') == 'csv':
        # экспорт в CSV
        csv_data = "Название книги,Имя читателя,Дата выдачи,Дата сдачи,Дней просрочено,Сумма штрафа\n"
        for b in overdue_books:
            csv_data += f"{b['title']},{b['reader_name']},{b['issue_date']},{b['due_date']},{b['days_overdue']},{b['estimated_fine']}\n"
        return Response(csv_data, mimetype="text/csv",
                        headers={"Content-Disposition": "attachment;filename=overdue_report.csv"})

    return render_template('reports/overdue.html', overdue_books=overdue_books)


@report_bp.route('/reports/popular-books')
def popular_books_report():
    # Get date range from query parameters or use default (last 30 days)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    today = datetime.now().date()
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        start_date = today - timedelta(days=30)
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        end_date = today
    
    popular_books = db.session.query(
        Book.ID, 
        Book.title,
        func.count(Loan.ID).label('loan_count')
    ).join(Loan).filter(
        Loan.issue_date.between(start_date, end_date)
    ).group_by(
        Book.ID, 
        Book.title
    ).order_by(
        func.count(Loan.ID).desc()
    ).limit(10).all()
    
#график
    if popular_books:
        plt.figure(figsize=(10, 6))
        titles = [book.title[:20] + '...' if len(book.title) > 20 else book.title for book in popular_books]
        counts = [book.loan_count for book in popular_books]
        
        plt.bar(titles, counts)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.ylabel('Number of Loans')
        plt.title('Most Popular Books')
        
        # Convert plot to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        chart_img = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
    else:
        chart_img = None
    
    return render_template('reports/popular_books.html', 
                          popular_books=popular_books,
                          start_date=start_date,
                          end_date=end_date,
                          chart_img=chart_img)

@report_bp.route('/reports/reader-activity')
def reader_activity_report():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    today = datetime.now().date()
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        start_date = today - timedelta(days=30)
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        end_date = today
    
    active_readers = db.session.query(
        Reader.ID, 
        Reader.full_name,
        func.count(Loan.ID).label('loan_count')
    ).join(Loan).filter(
        Loan.issue_date.between(start_date, end_date)
    ).group_by(
        Reader.ID, 
        Reader.full_name
    ).order_by(
        func.count(Loan.ID).desc()
    ).limit(10).all()
    
    # график 2
    if active_readers:
        plt.figure(figsize=(10, 6))
        names = [reader.full_name for reader in active_readers]
        counts = [reader.loan_count for reader in active_readers]
        
        plt.bar(names, counts)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.ylabel('Number of Loans')
        plt.title('Most Active Readers')
        
        # Convert plot to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        chart_img = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
    else:
        chart_img = None
    
    return render_template('reports/reader_activity.html', 
                          active_readers=active_readers,
                          start_date=start_date,
                          end_date=end_date,
                          chart_img=chart_img)
@report_bp.route('/reports/books-by-genre')
def books_by_genre_report():
    genre_counts = (
        db.session.query(
            Genre.name,
            func.count(BookGenre.book_id).label('book_count')
        )
        .join(BookGenre, Genre.ID == BookGenre.genre_id)
        .group_by(Genre.name)
        .order_by(func.count(BookGenre.book_id).desc())
        .all()
    )
    
    if request.args.get('export') == 'csv':
        df = pd.DataFrame(genre_counts, columns=['Genre', 'Book Count'])
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=books_by_genre_report.csv"}
        )
    
    if genre_counts:
        plt.figure(figsize=(10, 6))
        genres = [genre or 'Не указан' for genre, _ in genre_counts]
        counts = [count for _, count in genre_counts]
        
        plt.bar(genres, counts, color='#cc0000')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.ylabel('Количество книг')
        plt.title('Количество книг по жанрам')
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        chart_img = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
    else:
        chart_img = None

    return render_template('reports/books_by_genre.html',
                           genre_counts=genre_counts,
                           chart_img=chart_img)
