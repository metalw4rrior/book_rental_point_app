# routes/books.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Book, Publisher, Author, Genre, AuthorBook, BookGenre, Loan
from sqlalchemy import desc
import logging

book_bp = Blueprint('book_bp', __name__)

@book_bp.route('/books')
def books():
    search_query = request.args.get('search', '')
    genre_filter = request.args.get('genre', '')
    availability_filter = request.args.get('availability', '')

    query = Book.query

    if search_query:
        query = query.filter(Book.title.ilike(f'%{search_query}%'))
    
    if genre_filter:
        query = query.join(BookGenre).join(Genre).filter(Genre.name == genre_filter)
    
    if availability_filter:
        is_available = availability_filter == 'available'
        query = query.filter(Book.availability == is_available)
    
    books = query.all()
    genres = Genre.query.all()
    
    return render_template('books/index.html', books=books, genres=genres)

@book_bp.route('/books/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        publication_year = request.form.get('publication_year')
        page_count = request.form.get('page_count')
        condition = request.form.get('condition')
        publisher_id = request.form.get('publisher_id')  # Получаем publisher_id
        author_ids = request.form.getlist('author_ids')  
        genre_ids = request.form.getlist('genre_ids')  
        
        new_book = Book(
            title=title,
            publication_year=publication_year if publication_year else None,
            page_count=page_count if page_count else None,
            condition=condition,
            availability=True,
            publisher_id=publisher_id
        )
        
        db.session.add(new_book)
        db.session.commit()

        for author_id in author_ids:
            author_book = AuthorBook(author_id=author_id, book_id=new_book.ID)
            db.session.add(author_book)
        
        for genre_id in genre_ids:
            book_genre = BookGenre(book_id=new_book.ID, genre_id=genre_id)
            db.session.add(book_genre)
        
        db.session.commit()
        flash('Книга успешно добавлена!', 'success')
        return redirect(url_for('book_bp.books'))
    
    publishers = Publisher.query.all()
    authors = Author.query.all()
    genres = Genre.query.all()
    return render_template('books/add.html', publishers=publishers, authors=authors, genres=genres)


@book_bp.route('/add_publisher', methods=['POST'])
def add_publisher():
    name = request.form.get('name')
    city = request.form.get('city')
    founding_year = request.form.get('founding_year')
    try:
        new_publisher = Publisher(name=name, city=city, founding_year=founding_year)
        db.session.add(new_publisher)
        db.session.commit()

        flash(f'Издатель "{new_publisher.name}" успешно добавлен!', 'success')
        return redirect(url_for('book_bp.add_book'))  
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении издателя: {str(e)}', 'danger')
        return redirect(url_for('book_bp.add_book'))  

@book_bp.route('/add_author', methods=['POST'])
def add_author():
    full_name = request.form.get('full_name')
    country = request.form.get('country')
    birth_year = request.form.get('birth_year')
    bio = request.form.get('bio')
    try:
        new_author = Author(full_name=full_name, country=country, birth_year=birth_year, bio=bio)
        db.session.add(new_author)
        db.session.commit()

        flash(f'Автор "{new_author.full_name}" успешно добавлен!', 'success')
        return redirect(url_for('book_bp.add_book'))  # Возвращаемся на страницу добавления книги
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении автора: {str(e)}', 'danger')
        return redirect(url_for('book_bp.add_book'))  # Возвращаемся на страницу добавления книги

@book_bp.route('/books/<int:book_id>')
def view_book(book_id):
    book = Book.query.get_or_404(book_id)
    loan_history = Loan.query.filter_by(book_id=book_id).order_by(desc(Loan.issue_date)).all()
    
    return render_template('books/view.html', book=book, loan_history=loan_history)

@book_bp.route('/books/<int:book_id>/edit', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.publication_year = request.form.get('publication_year')
        book.page_count = request.form.get('page_count')
        book.condition = request.form.get('condition')
        book.publisher_id = request.form.get('publisher_id')
        
        AuthorBook.query.filter_by(book_id=book_id).delete()
        author_ids = request.form.getlist('author_ids')
        for author_id in author_ids:
            author_book = AuthorBook(author_id=author_id, book_id=book_id)
            db.session.add(author_book)
        
        BookGenre.query.filter_by(book_id=book_id).delete()
        genre_ids = request.form.getlist('genre_ids')
        for genre_id in genre_ids:
            book_genre = BookGenre(book_id=book_id, genre_id=genre_id) 
            db.session.add(book_genre)
        
        db.session.commit()
        flash('Book updated successfully!', 'success')
        return redirect(url_for('book_bp.view_book', book_id=book_id))
    publishers = Publisher.query.all()
    authors = Author.query.all()
    genres = Genre.query.all()
    current_author_ids = [author.ID for author in book.authors]
    current_genre_ids = [genre.ID for genre in book.genres]
    return render_template(
    'books/edit.html',
    book=book,
    publishers=publishers,
    authors=authors,
    genres=genres,
    current_author_ids=current_author_ids,
    current_genre_ids=current_genre_ids
)

@book_bp.route('/books/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    try:
        db.session.begin_nested()
        
        BookGenre.query.filter_by(book_id=book_id).delete()
        AuthorBook.query.filter_by(book_id=book_id).delete()
        Loan.query.filter_by(book_id=book_id).delete()
        
        Book.query.filter_by(ID=book_id).delete()
        
        db.session.commit()
        flash('Книга успешно удалена', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'danger')
        logging.error(f"Ошибка при удалении книги {book_id}: {str(e)}")
    
    return redirect(url_for('book_bp.books'))


@book_bp.route('/books/<int:book_id>/confirm_delete', methods=['GET'])
def confirm_delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('books/confirm_delete.html', book=book)
