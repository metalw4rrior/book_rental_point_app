from flask import Flask, render_template
from models import db, Book, Reader, Loan, BookRequest
from datetime import datetime
from sqlalchemy import desc, inspect
import subprocess
import os
from dotenv import load_dotenv
import time
load_dotenv()
db_password = os.getenv('DB_PASSWORD')
app = Flask(__name__,template_folder='templates')
app.secret_key = 'library_management_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://postgres:{db_password}@postgres:5432/libratrack'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def restore_if_needed():
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if not tables:
            print("No tables found. Attempting pg_restore...")
            dump_path = '/app/libratrack.dump'
            try:
                env = os.environ.copy()
                env['PGPASSWORD'] = db_password

                result = subprocess.run([
                    'pg_restore',
                    '-h', 'postgres',
                    '-U', 'postgres',
                    '-d', 'libratrack',
                    dump_path
                ], check=True, env=env)
                print("Restore completed successfully.")
            except subprocess.CalledProcessError as e:
                print("Restore failed:", e)
            except Exception as ex:
                print("Unexpected error during restore:", ex)
        else:
            print("Tables already exist. Skipping restore.")


@app.route('/')
def dashboard():
    total_books = Book.query.count()
    available_books = Book.query.filter_by(availability=True).count()
    active_loans = Loan.query.filter_by(status='Active').count()
    overdue_loans = Loan.query.filter(Loan.status == 'Active', Loan.due_date < db.func.current_date()).count()
    total_readers = Reader.query.count()
    pending_requests = BookRequest.query.filter_by(status='Pending').count()
    
    today = datetime.now().date()
    due_today = Loan.query.filter_by(due_date=today, status='Active').count()
    
    recent_loans = Loan.query.order_by(desc(Loan.issue_date)).limit(5).all()
    
    return render_template('dashboard.html', 
                          total_books=total_books,
                          available_books=available_books,
                          active_loans=active_loans,
                          overdue_loans=overdue_loans,
                          total_readers=total_readers,
                          due_today=due_today,
                          pending_requests=pending_requests,
                          recent_loans=recent_loans)

if __name__ == '__main__':
    time.sleep(5)  
    restore_if_needed()
    app.run(host="0.0.0.0", port=5000, debug=True)

