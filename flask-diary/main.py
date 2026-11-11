import os

from flask import Flask, render_template,request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (LoginManager, UserMixin, login_required, login_user, current_user, logout_user)

from werkzeug.middleware.proxy_fix import ProxyFix

from config import get_secret_key, is_production, security_settings


app = Flask(__name__)
app.config['SECRET_KEY'] = get_secret_key()
app.config.update(security_settings())

if is_production():
    # За прокси хостинга (HTTPS завершается на нём): доверяем заголовкам
    # X-Forwarded-Proto и X-Forwarded-Host от одного прокси.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///diary.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CARDS_PER_PAGE = 6

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # редирект неавторизованных пользователей

# 01 Модели БД
# ---------- МОДЕЛИ БАЗЫ ДАННЫХ (задача 01) ----------

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)



class Card(db.Model):
    __tablename__ = 'card'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subtitle = db.Column(db.String(100))
    text = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Маршруты

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Заполните все поля', 'error')
            return redirect(url_for('register'))

        if db.session.query(User).filter_by(username=username).first():
            flash('Такой пользователь уже существует', 'error')
            return redirect(url_for('register'))

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация прошла успешно! Теперь войдите.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = db.session.query(User).filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))

        flash('Неверный логин или пароль', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout/', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
  
@app.route('/')
@login_required
def index():
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Card.query.filter_by(user_id=current_user.id)
    if q:
        pattern = f'%{q}%'
        query = query.filter(
            Card.title.ilike(pattern)
            | Card.subtitle.ilike(pattern)
            | Card.text.ilike(pattern)
        )

    pagination = query.order_by(Card.id.desc()).paginate(
        page=page, per_page=CARDS_PER_PAGE, error_out=False
    )
    return render_template(
        'index.html', cards=pagination.items, pagination=pagination, q=q
    )

@app.route('/home')
def home():
   return render_template('home.html')


@app.route('/card/<int:id>')
@login_required
def card(id):
    card = Card.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    return render_template('card.html', card=card)


@app.route('/create')
@login_required
def create():
   return redirect(url_for('form_create'))


@app.route('/form_create', methods=['GET', 'POST'])
@login_required
def form_create():
    if request.method == 'POST':
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        text = request.form.get('text')

        card = Card(
            title=title,
            subtitle=subtitle,
            text=text,
            user_id=current_user.id
        )

        db.session.add(card)
        db.session.commit()

        flash('Карточка создана!', 'success')
        return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/card/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_card(id):
    card = Card.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Заголовок не может быть пустым', 'error')
            return redirect(url_for('edit_card', id=card.id))

        card.title = title
        card.subtitle = request.form.get('subtitle')
        card.text = request.form.get('text')
        db.session.commit()

        flash('Карточка обновлена!', 'success')
        return redirect(url_for('card', id=card.id))

    return render_template('edit.html', card=card)


@app.route('/card/<int:id>/delete', methods=['POST'])
@login_required
def delete_card(id):
    card = Card.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    db.session.delete(card)
    db.session.commit()

    flash('Карточка удалена', 'success')
    return redirect(url_for('index'))


# Таблицы создаются при импорте, чтобы приложение работало и под gunicorn
with app.app_context():
    db.create_all()


# Запуск для разработки (в продакшене используется gunicorn)
if __name__ == "__main__":  # pragma: no cover
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
