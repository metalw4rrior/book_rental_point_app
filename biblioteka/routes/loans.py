# routes/loans.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Loan, Book, Reader, Librarian, BookRequest
from sqlalchemy import desc, text
from datetime import datetime, timedelta

loan_bp = Blueprint('loan_bp', __name__)

@loan_bp.route('/loans')
def loans():
    status_filter = request.args.get('status', '')
    query = Loan.query
    if status_filter:
        query = query.filter(Loan.status == status_filter)
    loans = query.order_by(desc(Loan.issue_date)).all()
    return render_template('loans/index.html', loans=loans)

@loan_bp.route('/loans/add', methods=['GET', 'POST'])
def add_loan():
    if request.method == 'POST':
        book_id = request.form.get('book_id')
        reader_id = request.form.get('reader_id')
        librarian_id = request.form.get('librarian_id')
        issue_date = datetime.strptime(request.form.get('issue_date'), '%Y-%m-%d').date()
        due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
        book = Book.query.get(book_id)
        if not book.availability:
            flash('Эта книга недоступна для выдачи', 'danger')
            return redirect(url_for('loan_bp.add_loan'))

        new_loan = Loan(
            book_id=book_id,
            reader_id=reader_id,
            librarian_id=librarian_id,
            issue_date=issue_date,
            due_date=due_date,
            status='Active'
        )
        
        book.availability = False
        
        db.session.add(new_loan)
        db.session.commit()

        pending_request = BookRequest.query.filter_by(
            reader_id=reader_id, 
            book_id=book_id,
            status='Pending'
        ).first()
        
        if pending_request:
            pending_request.status = 'Fulfilled'
            db.session.commit()
        
        flash('Loan created successfully!', 'success')
        return redirect(url_for('loan_bp.loans'))
    
    books = Book.query.filter_by(availability=True).all()
    readers = Reader.query.all()
    librarians = Librarian.query.all()

    today = datetime.now().date()
    default_due_date = today + timedelta(days=14)
    
    return render_template('loans/add.html', books=books, readers=readers, 
                          librarians=librarians, today=today, default_due_date=default_due_date)

@loan_bp.route('/loans/<int:loan_id>/return', methods=['GET', 'POST'])
def return_book(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    
    if loan.status == 'Returned':
        flash('This book has already been returned', 'warning')
        return redirect(url_for('loan_bp.loans'))
    
    if request.method == 'POST':
        return_date = datetime.strptime(request.form.get('return_date'), '%Y-%m-%d').date()
        
        loan.return_date = return_date
        
        # Calculate overdue fine
        if return_date > loan.due_date:
            days_overdue = (return_date - loan.due_date).days
            loan.overdue_fine = days_overdue * 0.50  # 50 рублей в день
            loan.status = 'Returned'
        else:
            loan.overdue_fine = 0
            loan.status = 'Returned'
        
        # Update book availability
        book = Book.query.get(loan.book_id)
        book.availability = True
        
        db.session.commit()
        
        flash('Книга успешно возвращена!', 'success')
        return redirect(url_for('loan_bp.loans'))
    
    today = datetime.now().date()
    
    return render_template('loans/return.html', loan=loan, today=today)

@loan_bp.route('/loans/<int:loan_id>/extend', methods=['GET', 'POST'])
def extend_loan(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    
    if loan.status != 'Active':
        flash('Можно продлять только активные книги', 'warning')
        return redirect(url_for('loan_bp.loans'))
    
    if request.method == 'POST':
        additional_days = int(request.form.get('additional_days', 7))

        db.session.execute(text('CALL extend_due_date(:loan_id, :days)'), 
                          {'loan_id': loan_id, 'days': additional_days})
        db.session.commit()
        
        flash(f'Loan extended by {additional_days} days', 'success')
        return redirect(url_for('loan_bp.loans'))
    
    return render_template('loans/extend.html', loan=loan)