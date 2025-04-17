# main.py
from models import db
from app import app, restore_if_needed
from routes.books import book_bp
from routes.loans import loan_bp
from routes.reports import report_bp
from routes.readers import reader_bp


app.register_blueprint(book_bp)
app.register_blueprint(loan_bp)
app.register_blueprint(report_bp)
app.register_blueprint(reader_bp)




if __name__ == '__main__':
    with app.app_context():
        restore_if_needed() 
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)