from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Reader

reader_bp = Blueprint('reader_bp', __name__)

@reader_bp.route('/readers')
def readers():
    search_query = request.args.get('search', '')
    query = Reader.query

    if search_query:
        query = query.filter(Reader.full_name.ilike(f"%{search_query}%"))

    readers = query.all()
    return render_template('readers/index.html', readers=readers)


@reader_bp.route('/readers/add', methods=['GET', 'POST'])
def add_reader():
    if request.method == 'POST':
        full_name = request.form['full_name']
        address = request.form['address']
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')

        new_reader = Reader(
            full_name=full_name,
            address=address,
            phone_number=phone_number,
            email=email
        )
        db.session.add(new_reader)
        db.session.commit()
        flash('Читатель добавлен успешно!', 'success')
        return redirect(url_for('reader_bp.readers'))

    return render_template('readers/add.html')


@reader_bp.route('/readers/<int:reader_id>/edit', methods=['GET', 'POST'])
def edit_reader(reader_id):
    reader = Reader.query.get_or_404(reader_id)

    if request.method == 'POST':
        reader.full_name = request.form['full_name']
        reader.address = request.form['address']
        reader.phone_number = request.form.get('phone_number')
        reader.email = request.form.get('email')

        db.session.commit()
        flash('Данные читателя обновлены!', 'success')
        return redirect(url_for('reader_bp.readers'))

    return render_template('readers/edit.html', reader=reader)



