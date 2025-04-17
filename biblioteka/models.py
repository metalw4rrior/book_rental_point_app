from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class Publisher(db.Model):
    __tablename__ = 'PUBLISHER'
    ID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    founding_year = db.Column(db.Integer)
    books = db.relationship('Book', backref='publisher', lazy=True)

class Book(db.Model):
    __tablename__ = 'BOOK'
    ID = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    publication_year = db.Column(db.Integer)
    page_count = db.Column(db.Integer)
    condition = db.Column(db.String(50))
    availability = db.Column(db.Boolean, default=True)
    publisher_id = db.Column(db.Integer, db.ForeignKey('PUBLISHER.ID'))
    
    authors = db.relationship('Author', secondary='AUTHOR_BOOK', lazy='subquery',
                          backref=db.backref('books', lazy=True))
    genres = db.relationship('Genre', secondary='BOOK_GENRE', lazy='subquery',
                            backref=db.backref('books', lazy=True))

class Reader(db.Model):
    __tablename__ = 'READER'
    ID = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(100))
    registration_date = db.Column(db.Date, default=db.func.current_date())
    loans = db.relationship('Loan', backref='reader', lazy=True)

class Librarian(db.Model):
    __tablename__ = 'LIBRARIAN'
    ID = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20))
    loans = db.relationship('Loan', backref='librarian', lazy=True)

class Author(db.Model):
    __tablename__ = 'AUTHOR'
    ID = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    birth_year = db.Column(db.Integer)
    biography = db.Column(db.Text)

class Genre(db.Model):
    __tablename__ = 'GENRE'
    ID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)

class Loan(db.Model):
    __tablename__ = 'LOAN'
    ID = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('BOOK.ID', ondelete='CASCADE'), nullable=False)
    reader_id = db.Column(db.Integer, db.ForeignKey('READER.ID'), nullable=False)
    librarian_id = db.Column(db.Integer, db.ForeignKey('LIBRARIAN.ID'), nullable=False)
    issue_date = db.Column(db.Date, default=db.func.current_date(), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='Active')
    overdue_fine = db.Column(db.Numeric(10,2), default=0.00)
    
    book = db.relationship('Book', backref='loans')

class AuthorBook(db.Model):
    __tablename__ = 'AUTHOR_BOOK'
    author_id = db.Column(db.Integer, db.ForeignKey('AUTHOR.ID'), primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('BOOK.ID'), primary_key=True)

class BookGenre(db.Model):
    __tablename__ = 'BOOK_GENRE'
    book_id = db.Column(db.Integer, db.ForeignKey('BOOK.ID'), primary_key=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('GENRE.ID'), primary_key=True)

class BookRequest(db.Model):
    __tablename__ = 'BOOK_REQUEST'
    ID = db.Column(db.Integer, primary_key=True)
    reader_id = db.Column(db.Integer, db.ForeignKey('READER.ID'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('BOOK.ID'), nullable=True)  
    request_title = db.Column(db.String(255))  
    request_author = db.Column(db.String(255))  
    request_date = db.Column(db.Date, default=db.func.current_date(), nullable=False)
    status = db.Column(db.String(50), default='Pending') 
    notes = db.Column(db.Text)
    
    reader = db.relationship('Reader', backref='requests')
    requested_book = db.relationship('Book', backref='requests')